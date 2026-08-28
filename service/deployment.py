#!/usr/bin/env python3
"""Production adapter for the Agent Business discovery runtime.

This module keeps cloud-specific state outside the reference runtime. It can be used as
a Vercel Python entrypoint and only reports durable telemetry when an external HTTPS
sink explicitly attests durable readiness and acknowledges each event as persisted.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from service.agent_discovery_runtime import DiscoveryRuntime, EventSink, JsonLineEventSink


class EventSinkUnavailable(RuntimeError):
    """Raised when durable telemetry cannot safely accept an event."""


@dataclass(frozen=True)
class SinkConfig:
    ingest_url: str
    health_url: str
    token: str
    timeout_seconds: float = 2.0
    max_response_bytes: int = 8192
    health_cache_seconds: float = 10.0


class DurableHttpEventSink(EventSink):
    """HTTPS sink with explicit durability health and per-event persistence acks.

    Health response contract:
        {"status": "ready", "durable": true}

    Ingest response contract:
        {"persisted": true, "event_id": "<submitted event id>"}

    A 2xx response alone is never treated as proof of persistence.
    """

    def __init__(
        self,
        config: SinkConfig,
        *,
        opener: Callable = urlopen,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.config = config
        self.opener = opener
        self.monotonic = monotonic
        self._health_checked_at: float | None = None
        self._health_value = False
        self._validate_config()

    @property
    def durable(self) -> bool:
        now = self.monotonic()
        if (
            self._health_checked_at is not None
            and now - self._health_checked_at < self.config.health_cache_seconds
        ):
            return self._health_value
        self._health_value = self._check_health()
        self._health_checked_at = now
        return self._health_value

    def emit(self, event: dict) -> None:
        event_id = event.get("event_id")
        if not isinstance(event_id, str) or not event_id:
            raise EventSinkUnavailable("event is missing event_id")
        payload = self._request_json(
            self.config.ingest_url,
            method="POST",
            body=event,
        )
        if payload.get("persisted") is not True:
            raise EventSinkUnavailable("telemetry sink did not attest persistence")
        if payload.get("event_id") != event_id:
            raise EventSinkUnavailable("telemetry sink acknowledged a different event_id")

    def _check_health(self) -> bool:
        try:
            payload = self._request_json(self.config.health_url, method="GET")
        except EventSinkUnavailable:
            return False
        return payload.get("status") == "ready" and payload.get("durable") is True

    def _request_json(self, url: str, *, method: str, body: dict | None = None) -> dict:
        encoded = None if body is None else json.dumps(
            body, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        request = Request(
            url,
            data=encoded,
            method=method,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self.config.token}",
                **({"Content-Type": "application/json"} if encoded is not None else {}),
            },
        )
        try:
            with self.opener(request, timeout=self.config.timeout_seconds) as response:
                status = getattr(response, "status", 200)
                if status < 200 or status >= 300:
                    raise EventSinkUnavailable(f"telemetry sink returned HTTP {status}")
                raw = response.read(self.config.max_response_bytes + 1)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise EventSinkUnavailable("telemetry sink request failed") from exc
        if len(raw) > self.config.max_response_bytes:
            raise EventSinkUnavailable("telemetry sink response exceeded size limit")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise EventSinkUnavailable("telemetry sink returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise EventSinkUnavailable("telemetry sink response must be a JSON object")
        return payload

    def _validate_config(self) -> None:
        for name, url in (
            ("ingest_url", self.config.ingest_url),
            ("health_url", self.config.health_url),
        ):
            parsed = urlparse(url)
            if parsed.scheme != "https" or not parsed.netloc:
                raise ValueError(f"{name} must be an absolute HTTPS URL")
        if not self.config.token or len(self.config.token) < 16:
            raise ValueError("event sink token must be at least 16 characters")
        if not 0.1 <= self.config.timeout_seconds <= 10.0:
            raise ValueError("event sink timeout must be between 0.1 and 10 seconds")
        if not 256 <= self.config.max_response_bytes <= 65536:
            raise ValueError("event sink max response bytes must be 256-65536")
        if not 0 <= self.config.health_cache_seconds <= 60:
            raise ValueError("health cache seconds must be 0-60")


class DeploymentApplication:
    """Translate durable-sink failures into an explicit 503 response."""

    def __init__(self, runtime: DiscoveryRuntime) -> None:
        self.runtime = runtime

    def __call__(self, environ: dict, start_response: Callable):
        try:
            return self.runtime(environ, start_response)
        except EventSinkUnavailable:
            body = b'{"error":"telemetry_unavailable"}'
            start_response(
                "503 Service Unavailable",
                [
                    ("Content-Type", "application/json; charset=utf-8"),
                    ("Content-Length", str(len(body))),
                    ("Cache-Control", "no-store"),
                    ("Retry-After", "30"),
                ],
            )
            return [body]


def sink_from_environment(
    environment: Mapping[str, str],
    *,
    opener: Callable = urlopen,
    monotonic: Callable[[], float] = time.monotonic,
) -> EventSink:
    """Build a durable sink only when the complete server-side contract is present."""

    ingest_url = environment.get("AGENT_BUSINESS_EVENT_SINK_URL")
    health_url = environment.get("AGENT_BUSINESS_EVENT_SINK_HEALTH_URL")
    token = environment.get("AGENT_BUSINESS_EVENT_SINK_TOKEN")
    configured = [bool(ingest_url), bool(health_url), bool(token)]
    if any(configured) and not all(configured):
        raise ValueError(
            "AGENT_BUSINESS_EVENT_SINK_URL, AGENT_BUSINESS_EVENT_SINK_HEALTH_URL, "
            "and AGENT_BUSINESS_EVENT_SINK_TOKEN must be configured together"
        )
    if not all(configured):
        return JsonLineEventSink()

    config = SinkConfig(
        ingest_url=str(ingest_url),
        health_url=str(health_url),
        token=str(token),
        timeout_seconds=float(environment.get("AGENT_BUSINESS_EVENT_SINK_TIMEOUT_SECONDS", "2")),
        max_response_bytes=int(environment.get("AGENT_BUSINESS_EVENT_SINK_MAX_RESPONSE_BYTES", "8192")),
        health_cache_seconds=float(environment.get("AGENT_BUSINESS_EVENT_SINK_HEALTH_CACHE_SECONDS", "10")),
    )
    return DurableHttpEventSink(config, opener=opener, monotonic=monotonic)


def create_deployment_app(
    *,
    environment: Mapping[str, str] | None = None,
    opener: Callable = urlopen,
    monotonic: Callable[[], float] = time.monotonic,
) -> DeploymentApplication:
    env = dict(os.environ if environment is None else environment)
    sink = sink_from_environment(env, opener=opener, monotonic=monotonic)
    runtime = DiscoveryRuntime(
        environment=env,
        event_sink=sink,
        monotonic=monotonic,
    )
    return DeploymentApplication(runtime)


application = create_deployment_app()
