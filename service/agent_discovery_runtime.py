#!/usr/bin/env python3
"""Reference WSGI runtime for Agent Business discovery and activation telemetry.

The runtime is intentionally dependency-light and privacy-conservative. It serves the
canonical machine entrypoints, accepts a self-declared agent hello, ingests schema-
aligned discovery events, and emits structured events to a pluggable sink.

Production writes fail closed unless a persistent session secret and a durable event
sink are explicitly configured by the deployment layer.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json
import os
import secrets
import sys
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]

EVENT_TYPES = {
    "manifest_fetch",
    "index_fetch",
    "schema_fetch",
    "template_fetch",
    "resource_fetch",
    "agent_hello",
    "stage_selected",
    "resource_sequence_started",
    "founder_packet_started",
    "founder_packet_validated",
    "operating_artifact_created",
    "returning_agent",
    "commercial_intent",
    "checkout_started",
    "paid_conversion",
}
ACTOR_CONFIDENCE = {"unknown", "suspected_machine", "self_declared_agent", "verified_agent"}
CHANNELS = {"github", "raw_github", "website", "registry", "enterprise_catalog", "partner", "direct", "unknown"}
INTENTS = {"explore", "start_business", "resume_business", "evaluate_resource", "procure", "commercial"}
IDENTIFIER_POLICIES = {"none", "rotating_pseudonymous", "authenticated_integration"}
PROHIBITED_KEYS = {
    "ip",
    "ip_address",
    "raw_ip",
    "email",
    "authorization",
    "password",
    "secret",
    "api_key",
    "access_token",
    "refresh_token",
    "prompt",
    "prompt_content",
}
HELLO_TOP_LEVEL = {"schema_version", "client", "intent", "capabilities", "requested_start", "commercial", "privacy"}
EVENT_TOP_LEVEL = {"schema_version", "event_id", "event_type", "occurred_at", "session_id", "actor", "source", "resource", "engagement", "commercial", "privacy"}


class ValidationError(ValueError):
    """Raised when an inbound machine contract is invalid or unsafe."""


class EventSink:
    """Minimal sink interface used by the reference runtime."""

    durable = False

    def emit(self, event: dict) -> None:  # pragma: no cover - interface only
        raise NotImplementedError


class JsonLineEventSink(EventSink):
    """Emit one sanitized event per line. Useful for local/dev log pipelines."""

    durable = False

    def __init__(self, stream=None) -> None:
        self.stream = stream or sys.stdout
        self._lock = threading.Lock()

    def emit(self, event: dict) -> None:
        line = json.dumps(event, sort_keys=True, separators=(",", ":"))
        with self._lock:
            self.stream.write(line + "\n")
            self.stream.flush()


class MemoryEventSink(EventSink):
    """Test/helper sink. Mark durable only when a caller intentionally simulates it."""

    def __init__(self, *, durable: bool = False) -> None:
        self.durable = durable
        self.events: list[dict] = []

    def emit(self, event: dict) -> None:
        self.events.append(json.loads(json.dumps(event)))


class RateLimiter:
    """Simple per-instance sliding-window limiter keyed by a non-reversible digest."""

    def __init__(self, limit_per_minute: int, monotonic: Callable[[], float] | None = None) -> None:
        self.limit = max(1, int(limit_per_minute))
        self.monotonic = monotonic or time.monotonic
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = self.monotonic()
        cutoff = now - 60.0
        with self._lock:
            bucket = self._hits[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= self.limit:
                return False
            bucket.append(now)
            return True


class DiscoveryRuntime:
    """WSGI application implementing the reference discovery surface."""

    def __init__(
        self,
        *,
        root: Path = ROOT,
        environment: Mapping[str, str] | None = None,
        session_secret: str | bytes | None = None,
        event_sink: EventSink | None = None,
        clock: Callable[[], datetime] | None = None,
        monotonic: Callable[[], float] | None = None,
    ) -> None:
        self.root = Path(root)
        self.environment = dict(os.environ if environment is None else environment)
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.event_sink = event_sink or JsonLineEventSink()
        self.production = self.environment.get("AGENT_BUSINESS_ENV", "development").lower() == "production"
        explicit_secret = session_secret if session_secret is not None else self.environment.get("AGENT_BUSINESS_SESSION_SECRET")
        self.has_persistent_session_secret = explicit_secret is not None
        if explicit_secret is None:
            self._session_secret = secrets.token_bytes(32)
        elif isinstance(explicit_secret, bytes):
            self._session_secret = explicit_secret
        else:
            self._session_secret = explicit_secret.encode("utf-8")
        if len(self._session_secret) < 16:
            raise ValueError("session secret must be at least 16 bytes")

        self.release_id = self.environment.get("AGENT_BUSINESS_RELEASE_ID", "local")
        self.max_body_bytes = int(self.environment.get("AGENT_BUSINESS_MAX_BODY_BYTES", "65536"))
        self.write_rate_limit = int(self.environment.get("AGENT_BUSINESS_WRITE_RATE_LIMIT_PER_MINUTE", "60"))
        self.rate_limiter = RateLimiter(self.write_rate_limit, monotonic=monotonic)
        self.index = self._load_json("agent-index.json")
        self.resources = {
            item.get("id"): item
            for item in self.index.get("resources", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }

    @property
    def production_ready(self) -> bool:
        return self.has_persistent_session_secret and bool(self.event_sink.durable)

    def __call__(self, environ: dict, start_response: Callable) -> Iterable[bytes]:
        method = str(environ.get("REQUEST_METHOD", "GET")).upper()
        path = str(environ.get("PATH_INFO", "/")) or "/"

        if method == "GET":
            return self._handle_get(path, environ, start_response)
        if method == "POST" and path in {"/v1/agent/hello", "/v1/events"}:
            if not self._allow_write(environ):
                return self._json(start_response, 429, {"error": "rate_limited", "retry_after_seconds": 60}, [("Retry-After", "60")])
            if self.production and not self.production_ready:
                return self._json(
                    start_response,
                    503,
                    {
                        "error": "production_not_ready",
                        "requires": ["persistent_session_secret", "durable_event_sink"],
                    },
                )
            try:
                payload = self._read_json_body(environ)
                if path == "/v1/agent/hello":
                    return self._handle_hello(payload, start_response)
                return self._handle_event(payload, start_response)
            except ValidationError as exc:
                return self._json(start_response, 400, {"error": "invalid_request", "detail": str(exc)})
            except BodyTooLarge:
                return self._json(start_response, 413, {"error": "payload_too_large", "max_body_bytes": self.max_body_bytes})
        return self._json(start_response, 404, {"error": "not_found"})

    def _handle_get(self, path: str, environ: dict, start_response: Callable) -> Iterable[bytes]:
        if path == "/healthz":
            status = 200 if (not self.production or self.production_ready) else 503
            return self._json(
                start_response,
                status,
                {
                    "status": "ready" if status == 200 else "not_ready",
                    "environment": "production" if self.production else "development",
                    "release_id": self.release_id,
                    "machine_assets": "available",
                    "session_persistence": "configured" if self.has_persistent_session_secret else "process_ephemeral",
                    "durable_telemetry": bool(self.event_sink.durable),
                    "production_ready": self.production_ready,
                },
            )
        if path == "/llms.txt":
            self._emit_fetch("manifest_fetch", path, environ)
            return self._file(start_response, self.root / "llms.txt", "text/plain; charset=utf-8")
        if path == "/agent-index.json":
            self._emit_fetch("index_fetch", path, environ)
            return self._file(start_response, self.root / "agent-index.json", "application/json; charset=utf-8")
        if path == "/v1/meta":
            return self._json(
                start_response,
                200,
                {
                    "service": "agent-business-discovery",
                    "release_id": self.release_id,
                    "canonical_index": "/agent-index.json",
                    "llm_entrypoint": "/llms.txt",
                    "hello": "/v1/agent/hello",
                    "events": "/v1/events",
                    "hello_schema": "/schemas/agent-hello.schema.json",
                    "event_schema": "/schemas/agent-discovery-event.schema.json",
                    "production_ready": self.production_ready,
                },
            )
        if path in {"/schemas/agent-hello.schema.json", "/schemas/agent-discovery-event.schema.json"}:
            relative = path.lstrip("/")
            self._emit_fetch("schema_fetch", path, environ)
            return self._file(start_response, self.root / relative, "application/schema+json; charset=utf-8")
        return self._json(start_response, 404, {"error": "not_found"})

    def _handle_hello(self, payload: dict, start_response: Callable) -> Iterable[bytes]:
        self._validate_hello(payload)
        privacy = payload["privacy"]
        session_id = self._issue_session_id() if privacy["allow_pseudonymous_session"] else None
        resource = self._select_start_resource(payload)
        client = payload["client"]
        actor: dict[str, object] = {"confidence": "self_declared_agent"}
        if privacy.get("allow_runtime_analytics") is True:
            if isinstance(client.get("runtime"), str):
                actor["declared_runtime"] = client["runtime"]
            if isinstance(client.get("runtime_version"), str):
                actor["declared_runtime_version"] = client["runtime_version"]

        event = {
            "schema_version": "1.0.0",
            "event_id": "evt_" + secrets.token_urlsafe(12),
            "event_type": "agent_hello",
            "occurred_at": self._now_iso(),
            "actor": actor,
            "source": {"channel": "website"},
            "resource": {"resource_id": resource["id"], "path": resource["path"], **({"stage": resource["stage"]} if isinstance(resource.get("stage"), int) else {})},
            "engagement": {"intent": payload["intent"]},
            "privacy": self._privacy_block(session_id is not None),
        }
        if session_id:
            event["session_id"] = session_id
        self.event_sink.emit(event)

        body = {
            "schema_version": "1.0.0",
            "actor_confidence": "self_declared_agent",
            "verification": "self_declaration_only",
            "release_id": self.release_id,
            "canonical_index": "/agent-index.json",
            "llm_entrypoint": "/llms.txt",
            "recommended_start": {
                "resource_id": resource["id"],
                "path": resource["path"],
                **({"stage": resource["stage"]} if isinstance(resource.get("stage"), int) else {}),
            },
            "supported_schemas": [
                "/schemas/agent-hello.schema.json",
                "/schemas/agent-discovery-event.schema.json",
                "/schemas/founder-launch-packet.schema.json",
            ],
            "telemetry": {
                "event_endpoint": "/v1/events",
                "durable": bool(self.event_sink.durable),
                "raw_ip_retained": False,
                "raw_user_agent_retained": False,
                "session_policy": "rotating_pseudonymous" if session_id else "none",
            },
        }
        if session_id:
            body["session_id"] = session_id
        return self._json(start_response, 200, body)

    def _handle_event(self, payload: dict, start_response: Callable) -> Iterable[bytes]:
        self._validate_event(payload)
        session_id = payload.get("session_id")
        if session_id is not None and not self._verify_session_id(session_id):
            raise ValidationError("session_id was not issued by this runtime or is no longer valid")
        self.event_sink.emit(payload)
        return self._json(start_response, 202, {"accepted": True, "event_id": payload["event_id"]})

    def _validate_hello(self, payload: object) -> None:
        if not isinstance(payload, dict):
            raise ValidationError("hello payload must be a JSON object")
        self._reject_unknown_keys(payload, HELLO_TOP_LEVEL, "hello")
        self._scan_prohibited(payload)
        if payload.get("schema_version") != "1.0.0":
            raise ValidationError("schema_version must be 1.0.0")
        client = self._require_object(payload, "client")
        self._reject_unknown_keys(client, {"type", "runtime", "runtime_version", "identity_reference"}, "client")
        if client.get("type") != "agent":
            raise ValidationError("client.type must be agent")
        self._optional_string(client, "runtime", 128)
        self._optional_string(client, "runtime_version", 64)
        self._optional_string(client, "identity_reference", 512)
        if payload.get("intent") not in INTENTS:
            raise ValidationError("intent is invalid")
        capabilities = self._require_object(payload, "capabilities")
        self._reject_unknown_keys(capabilities, {"can_persist_founder_packet", "protocols"}, "capabilities")
        if not isinstance(capabilities.get("can_persist_founder_packet"), bool):
            raise ValidationError("capabilities.can_persist_founder_packet must be boolean")
        protocols = capabilities.get("protocols")
        if not isinstance(protocols, list) or len(protocols) > 32 or any(not isinstance(item, str) or not item or len(item) > 64 for item in protocols):
            raise ValidationError("capabilities.protocols must be <=32 non-empty strings of <=64 chars")
        if len(set(protocols)) != len(protocols):
            raise ValidationError("capabilities.protocols must be unique")
        privacy = self._require_object(payload, "privacy")
        self._reject_unknown_keys(privacy, {"allow_pseudonymous_session", "allow_runtime_analytics"}, "privacy")
        if not isinstance(privacy.get("allow_pseudonymous_session"), bool):
            raise ValidationError("privacy.allow_pseudonymous_session must be boolean")
        if "allow_runtime_analytics" in privacy and not isinstance(privacy["allow_runtime_analytics"], bool):
            raise ValidationError("privacy.allow_runtime_analytics must be boolean")
        requested = payload.get("requested_start")
        if requested is not None:
            if not isinstance(requested, dict):
                raise ValidationError("requested_start must be an object")
            self._reject_unknown_keys(requested, {"resource_id", "stage"}, "requested_start")
            resource_id = requested.get("resource_id")
            if resource_id is not None and resource_id not in self.resources:
                raise ValidationError(f"requested_start.resource_id is unknown: {resource_id}")
            stage = requested.get("stage")
            if stage is not None and (not isinstance(stage, int) or stage < 1):
                raise ValidationError("requested_start.stage must be a positive integer")
            if resource_id in self.resources and stage is not None and self.resources[resource_id].get("stage") != stage:
                raise ValidationError("requested_start.stage does not match the indexed resource")
        commercial = payload.get("commercial")
        if commercial is not None:
            if not isinstance(commercial, dict):
                raise ValidationError("commercial must be an object")
            self._reject_unknown_keys(commercial, {"wants_paid_capabilities", "budget_currency", "budget_amount_minor"}, "commercial")
            if "wants_paid_capabilities" in commercial and not isinstance(commercial["wants_paid_capabilities"], bool):
                raise ValidationError("commercial.wants_paid_capabilities must be boolean")
            currency = commercial.get("budget_currency")
            if currency is not None and (not isinstance(currency, str) or len(currency) != 3 or currency.upper() != currency):
                raise ValidationError("commercial.budget_currency must be a 3-letter uppercase code")
            amount = commercial.get("budget_amount_minor")
            if amount is not None and (not isinstance(amount, int) or amount < 0):
                raise ValidationError("commercial.budget_amount_minor must be a non-negative integer")

    def _validate_event(self, payload: object) -> None:
        if not isinstance(payload, dict):
            raise ValidationError("event payload must be a JSON object")
        self._reject_unknown_keys(payload, EVENT_TOP_LEVEL, "event")
        self._scan_prohibited(payload)
        if payload.get("schema_version") != "1.0.0":
            raise ValidationError("schema_version must be 1.0.0")
        event_id = payload.get("event_id")
        if not isinstance(event_id, str) or not 8 <= len(event_id) <= 128:
            raise ValidationError("event_id must be 8-128 characters")
        if payload.get("event_type") not in EVENT_TYPES:
            raise ValidationError("event_type is invalid")
        self._parse_time(payload.get("occurred_at"))
        session_id = payload.get("session_id")
        if session_id is not None and (not isinstance(session_id, str) or not 8 <= len(session_id) <= 128):
            raise ValidationError("session_id must be 8-128 characters")
        actor = self._require_object(payload, "actor")
        self._reject_unknown_keys(actor, {"confidence", "declared_runtime", "declared_runtime_version", "identity_reference"}, "actor")
        if actor.get("confidence") not in ACTOR_CONFIDENCE:
            raise ValidationError("actor.confidence is invalid")
        self._optional_string(actor, "declared_runtime", 128)
        self._optional_string(actor, "declared_runtime_version", 64)
        self._optional_string(actor, "identity_reference", 512)
        source = self._require_object(payload, "source")
        self._reject_unknown_keys(source, {"channel", "referrer_class", "registry"}, "source")
        if source.get("channel") not in CHANNELS:
            raise ValidationError("source.channel is invalid")
        self._optional_string(source, "referrer_class", 128)
        self._optional_string(source, "registry", 128)
        resource = payload.get("resource")
        if resource is not None:
            if not isinstance(resource, dict):
                raise ValidationError("resource must be an object")
            self._reject_unknown_keys(resource, {"path", "resource_id", "stage"}, "resource")
            self._optional_string(resource, "path", 512)
            self._optional_string(resource, "resource_id", 128)
            resource_id = resource.get("resource_id")
            if resource_id is not None and resource_id not in self.resources:
                raise ValidationError(f"resource.resource_id is unknown: {resource_id}")
            stage = resource.get("stage")
            if stage is not None and (not isinstance(stage, int) or stage < 1):
                raise ValidationError("resource.stage must be a positive integer")
            if resource_id in self.resources and stage is not None and self.resources[resource_id].get("stage") != stage:
                raise ValidationError("resource.stage does not match indexed resource")
        engagement = payload.get("engagement")
        if engagement is not None:
            if not isinstance(engagement, dict):
                raise ValidationError("engagement must be an object")
            self._reject_unknown_keys(engagement, {"intent", "return_visit_count", "artifact_type"}, "engagement")
            if "intent" in engagement and engagement["intent"] not in INTENTS | {"unknown"}:
                raise ValidationError("engagement.intent is invalid")
            if "return_visit_count" in engagement and (not isinstance(engagement["return_visit_count"], int) or engagement["return_visit_count"] < 0):
                raise ValidationError("engagement.return_visit_count must be non-negative")
            self._optional_string(engagement, "artifact_type", 128)
        commercial = payload.get("commercial")
        if commercial is not None:
            if not isinstance(commercial, dict):
                raise ValidationError("commercial must be an object")
            self._reject_unknown_keys(commercial, {"offer_id", "currency", "amount_minor"}, "commercial")
            self._optional_string(commercial, "offer_id", 128)
            currency = commercial.get("currency")
            if currency is not None and (not isinstance(currency, str) or len(currency) != 3 or currency.upper() != currency):
                raise ValidationError("commercial.currency must be a 3-letter uppercase code")
            amount = commercial.get("amount_minor")
            if amount is not None and (not isinstance(amount, int) or amount < 0):
                raise ValidationError("commercial.amount_minor must be a non-negative integer")
        privacy = self._require_object(payload, "privacy")
        self._reject_unknown_keys(privacy, {"raw_ip_retained", "raw_user_agent_retained", "contains_prompt_content", "contains_secrets", "identifier_policy", "retention_days"}, "privacy")
        for field in ("raw_ip_retained", "raw_user_agent_retained", "contains_prompt_content", "contains_secrets"):
            if privacy.get(field) is not False:
                raise ValidationError(f"privacy.{field} must be false for this runtime")
        policy = privacy.get("identifier_policy")
        if policy is not None and policy not in IDENTIFIER_POLICIES:
            raise ValidationError("privacy.identifier_policy is invalid")
        retention = privacy.get("retention_days")
        if retention is not None and (not isinstance(retention, int) or not 0 <= retention <= 3650):
            raise ValidationError("privacy.retention_days must be 0-3650")

    def _select_start_resource(self, payload: dict) -> dict:
        requested = payload.get("requested_start") or {}
        resource_id = requested.get("resource_id")
        if resource_id:
            return self.resources[resource_id]
        defaults = {
            "explore": "pick",
            "start_business": "pick",
            "resume_business": "operate",
            "evaluate_resource": "tool-directory",
            "procure": "procure",
            "commercial": "monetize",
        }
        selected = self.resources.get(defaults[payload["intent"]])
        if not selected:
            raise ValidationError("repository index is missing the default start resource")
        return selected

    def _issue_session_id(self) -> str:
        day = self.clock().astimezone(timezone.utc).strftime("%Y%m%d")
        nonce = self._b64(secrets.token_bytes(16))
        message = f"{day}.{nonce}".encode("utf-8")
        signature = self._b64(hmac.new(self._session_secret, message, hashlib.sha256).digest()[:16])
        return f"sid.{day}.{nonce}.{signature}"

    def _verify_session_id(self, value: str) -> bool:
        try:
            prefix, day, nonce, signature = value.split(".")
            if prefix != "sid":
                return False
            issued = datetime.strptime(day, "%Y%m%d").replace(tzinfo=timezone.utc)
            age_days = (self.clock().astimezone(timezone.utc).date() - issued.date()).days
            if age_days < 0 or age_days > 31:
                return False
            expected = self._b64(hmac.new(self._session_secret, f"{day}.{nonce}".encode("utf-8"), hashlib.sha256).digest()[:16])
            return hmac.compare_digest(signature, expected)
        except (ValueError, TypeError):
            return False

    def _emit_fetch(self, event_type: str, path: str, environ: dict) -> None:
        session_id = environ.get("HTTP_X_AGENT_BUSINESS_SESSION")
        valid_session = isinstance(session_id, str) and self._verify_session_id(session_id)
        event = {
            "schema_version": "1.0.0",
            "event_id": "evt_" + secrets.token_urlsafe(12),
            "event_type": event_type,
            "occurred_at": self._now_iso(),
            "actor": {"confidence": "self_declared_agent" if valid_session else "unknown"},
            "source": {"channel": "website"},
            "resource": {"path": path},
            "privacy": self._privacy_block(valid_session),
        }
        if valid_session:
            event["session_id"] = session_id
        self.event_sink.emit(event)

    def _privacy_block(self, has_session: bool) -> dict:
        return {
            "raw_ip_retained": False,
            "raw_user_agent_retained": False,
            "contains_prompt_content": False,
            "contains_secrets": False,
            "identifier_policy": "rotating_pseudonymous" if has_session else "none",
            "retention_days": 30 if has_session else 7,
        }

    def _allow_write(self, environ: dict) -> bool:
        remote = str(environ.get("REMOTE_ADDR", "unknown"))
        digest = hmac.new(self._session_secret, remote.encode("utf-8"), hashlib.sha256).hexdigest()[:24]
        return self.rate_limiter.allow(digest)

    def _read_json_body(self, environ: dict) -> dict:
        raw_length = environ.get("CONTENT_LENGTH", "")
        if raw_length in (None, ""):
            length = 0
        else:
            try:
                length = int(raw_length)
            except (TypeError, ValueError) as exc:
                raise ValidationError("Content-Length must be an integer") from exc
        if length > self.max_body_bytes:
            raise BodyTooLarge
        stream = environ.get("wsgi.input") or io.BytesIO()
        body = stream.read(self.max_body_bytes + 1 if length == 0 else length)
        if len(body) > self.max_body_bytes:
            raise BodyTooLarge
        if not body:
            raise ValidationError("request body is required")
        try:
            value = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValidationError("request body must be valid UTF-8 JSON") from exc
        if not isinstance(value, dict):
            raise ValidationError("request body must be a JSON object")
        return value

    def _file(self, start_response: Callable, path: Path, content_type: str) -> Iterable[bytes]:
        try:
            body = path.read_bytes()
        except OSError:
            return self._json(start_response, 500, {"error": "machine_asset_unavailable"})
        start_response("200 OK", [("Content-Type", content_type), ("Content-Length", str(len(body))), ("Cache-Control", "public, max-age=60")])
        return [body]

    def _json(self, start_response: Callable, status: int, payload: dict, extra_headers: list[tuple[str, str]] | None = None) -> Iterable[bytes]:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        headers = [("Content-Type", "application/json; charset=utf-8"), ("Content-Length", str(len(body))), ("Cache-Control", "no-store")]
        if extra_headers:
            headers.extend(extra_headers)
        phrases = {200: "OK", 202: "Accepted", 400: "Bad Request", 404: "Not Found", 413: "Payload Too Large", 429: "Too Many Requests", 500: "Internal Server Error", 503: "Service Unavailable"}
        start_response(f"{status} {phrases[status]}", headers)
        return [body]

    def _load_json(self, relative: str) -> dict:
        data = json.loads((self.root / relative).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"{relative} must contain a JSON object")
        return data

    def _scan_prohibited(self, value: object, path: str = "$") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                normalized = str(key).lower().replace("-", "_")
                if normalized in PROHIBITED_KEYS:
                    raise ValidationError(f"prohibited sensitive field: {path}.{key}")
                self._scan_prohibited(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                self._scan_prohibited(child, f"{path}[{index}]")

    @staticmethod
    def _reject_unknown_keys(value: dict, allowed: set[str], path: str) -> None:
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValidationError(f"{path} contains unsupported field(s): {', '.join(unknown)}")

    @staticmethod
    def _require_object(value: dict, key: str) -> dict:
        child = value.get(key)
        if not isinstance(child, dict):
            raise ValidationError(f"{key} must be an object")
        return child

    @staticmethod
    def _optional_string(value: dict, key: str, maximum: int) -> None:
        if key in value and (not isinstance(value[key], str) or len(value[key]) > maximum):
            raise ValidationError(f"{key} must be a string of <= {maximum} characters")

    @staticmethod
    def _parse_time(value: object) -> datetime:
        if not isinstance(value, str):
            raise ValidationError("occurred_at must be an ISO 8601 date-time")
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValidationError("occurred_at must be an ISO 8601 date-time") from exc
        if parsed.tzinfo is None:
            raise ValidationError("occurred_at must include a timezone")
        return parsed

    def _now_iso(self) -> str:
        return self.clock().astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _b64(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


class BodyTooLarge(Exception):
    pass


def create_app(**kwargs) -> DiscoveryRuntime:
    """Create a WSGI application. Deployment layers may inject a durable EventSink."""

    return DiscoveryRuntime(**kwargs)


application = create_app()
