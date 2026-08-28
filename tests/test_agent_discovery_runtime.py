#!/usr/bin/env python3
from __future__ import annotations

import io
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from service.agent_discovery_runtime import DiscoveryRuntime, MemoryEventSink

ROOT = Path(__file__).resolve().parents[1]
FIXED_NOW = datetime(2026, 8, 28, 3, 30, tzinfo=timezone.utc)


def hello_payload(**overrides) -> dict:
    payload = {
        "schema_version": "1.0.0",
        "client": {"type": "agent", "runtime": "test-agent", "runtime_version": "1.0"},
        "intent": "start_business",
        "capabilities": {"can_persist_founder_packet": True, "protocols": ["http"]},
        "privacy": {"allow_pseudonymous_session": True, "allow_runtime_analytics": False},
    }
    payload.update(overrides)
    return payload


def event_payload(session_id: str | None = None) -> dict:
    payload = {
        "schema_version": "1.0.0",
        "event_id": "evt_test_12345",
        "event_type": "stage_selected",
        "occurred_at": "2026-08-28T03:30:00Z",
        "actor": {"confidence": "self_declared_agent"},
        "source": {"channel": "website"},
        "resource": {"resource_id": "pick", "stage": 1, "path": "docs/BUSINESS_MODELS.md"},
        "engagement": {"intent": "start_business"},
        "privacy": {
            "raw_ip_retained": False,
            "raw_user_agent_retained": False,
            "contains_prompt_content": False,
            "contains_secrets": False,
            "identifier_policy": "rotating_pseudonymous" if session_id else "none",
            "retention_days": 30 if session_id else 7,
        },
    }
    if session_id:
        payload["session_id"] = session_id
    return payload


def call_wsgi(app, method: str, path: str, payload: dict | bytes | None = None, *, remote: str = "203.0.113.10", headers: dict[str, str] | None = None):
    if isinstance(payload, dict):
        body = json.dumps(payload).encode("utf-8")
    elif isinstance(payload, bytes):
        body = payload
    else:
        body = b""
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "CONTENT_LENGTH": str(len(body)),
        "CONTENT_TYPE": "application/json",
        "REMOTE_ADDR": remote,
        "wsgi.input": io.BytesIO(body),
    }
    for key, value in (headers or {}).items():
        environ["HTTP_" + key.upper().replace("-", "_")] = value
    captured: dict[str, object] = {}

    def start_response(status, response_headers):
        captured["status"] = status
        captured["headers"] = dict(response_headers)

    response_body = b"".join(app(environ, start_response))
    status_code = int(str(captured["status"]).split()[0])
    content_type = captured["headers"].get("Content-Type", "")  # type: ignore[index]
    if str(content_type).startswith("application/json"):
        decoded = json.loads(response_body.decode("utf-8"))
    else:
        decoded = response_body.decode("utf-8")
    return status_code, captured["headers"], decoded


class DiscoveryRuntimeTests(unittest.TestCase):
    def make_app(self, *, environment=None, sink=None, secret="0123456789abcdef0123456789abcdef", monotonic=None):
        return DiscoveryRuntime(
            root=ROOT,
            environment=environment or {"AGENT_BUSINESS_ENV": "development"},
            session_secret=secret,
            event_sink=sink or MemoryEventSink(),
            clock=lambda: FIXED_NOW,
            monotonic=monotonic,
        )

    def test_machine_entrypoints_are_served_and_fetches_are_observed(self):
        sink = MemoryEventSink()
        app = self.make_app(sink=sink)
        status, headers, body = call_wsgi(app, "GET", "/llms.txt")
        self.assertEqual(status, 200)
        self.assertIn("Agent Business", body)
        self.assertTrue(headers["Content-Type"].startswith("text/plain"))
        status, _, index = call_wsgi(app, "GET", "/agent-index.json")
        self.assertEqual(status, 200)
        self.assertIn("Svyable/agent-business", index)
        self.assertEqual([event["event_type"] for event in sink.events], ["manifest_fetch", "index_fetch"])
        for event in sink.events:
            self.assertEqual(event["actor"]["confidence"], "unknown")
            self.assertFalse(event["privacy"]["raw_ip_retained"])
            self.assertFalse(event["privacy"]["raw_user_agent_retained"])

    def test_hello_issues_signed_session_and_recommends_indexed_start(self):
        sink = MemoryEventSink()
        app = self.make_app(sink=sink)
        status, _, response = call_wsgi(app, "POST", "/v1/agent/hello", hello_payload())
        self.assertEqual(status, 200)
        self.assertEqual(response["actor_confidence"], "self_declared_agent")
        self.assertEqual(response["verification"], "self_declaration_only")
        self.assertEqual(response["recommended_start"]["resource_id"], "pick")
        self.assertTrue(response["session_id"].startswith("sid."))
        self.assertEqual(len(sink.events), 1)
        event = sink.events[0]
        self.assertEqual(event["event_type"], "agent_hello")
        self.assertEqual(event["actor"], {"confidence": "self_declared_agent"})
        self.assertNotIn("identity_reference", event["actor"])

    def test_runtime_metadata_is_only_emitted_with_explicit_analytics_consent(self):
        sink = MemoryEventSink()
        app = self.make_app(sink=sink)
        payload = hello_payload()
        payload["privacy"]["allow_runtime_analytics"] = True
        status, _, _ = call_wsgi(app, "POST", "/v1/agent/hello", payload)
        self.assertEqual(status, 200)
        self.assertEqual(sink.events[0]["actor"]["declared_runtime"], "test-agent")
        self.assertEqual(sink.events[0]["actor"]["declared_runtime_version"], "1.0")

    def test_unknown_requested_resource_fails_closed(self):
        app = self.make_app()
        payload = hello_payload(requested_start={"resource_id": "does-not-exist"})
        status, _, response = call_wsgi(app, "POST", "/v1/agent/hello", payload)
        self.assertEqual(status, 400)
        self.assertIn("unknown", response["detail"])

    def test_valid_event_with_issued_session_is_accepted(self):
        sink = MemoryEventSink()
        app = self.make_app(sink=sink)
        status, _, response = call_wsgi(app, "POST", "/v1/agent/hello", hello_payload())
        self.assertEqual(status, 200)
        event = event_payload(response["session_id"])
        status, _, accepted = call_wsgi(app, "POST", "/v1/events", event, remote="203.0.113.11")
        self.assertEqual(status, 202)
        self.assertTrue(accepted["accepted"])
        self.assertEqual(sink.events[-1]["event_id"], event["event_id"])

    def test_forged_session_is_rejected(self):
        app = self.make_app()
        event = event_payload("sid.20260828.forged.forged")
        status, _, response = call_wsgi(app, "POST", "/v1/events", event)
        self.assertEqual(status, 400)
        self.assertIn("not issued", response["detail"])

    def test_sensitive_event_fields_are_rejected(self):
        app = self.make_app()
        event = event_payload()
        event["prompt"] = "do not store me"
        status, _, response = call_wsgi(app, "POST", "/v1/events", event)
        self.assertEqual(status, 400)
        self.assertIn("prohibited sensitive field", response["detail"])

    def test_raw_user_agent_retention_is_rejected(self):
        app = self.make_app()
        event = event_payload()
        event["privacy"]["raw_user_agent_retained"] = True
        status, _, response = call_wsgi(app, "POST", "/v1/events", event)
        self.assertEqual(status, 400)
        self.assertIn("raw_user_agent_retained", response["detail"])

    def test_oversize_write_is_rejected_before_parsing(self):
        app = DiscoveryRuntime(
            root=ROOT,
            environment={"AGENT_BUSINESS_ENV": "development", "AGENT_BUSINESS_MAX_BODY_BYTES": "32"},
            session_secret="0123456789abcdef0123456789abcdef",
            event_sink=MemoryEventSink(),
            clock=lambda: FIXED_NOW,
        )
        status, _, response = call_wsgi(app, "POST", "/v1/agent/hello", b"{" + b"x" * 100 + b"}")
        self.assertEqual(status, 413)
        self.assertEqual(response["error"], "payload_too_large")

    def test_write_rate_limit_is_enforced_without_logging_raw_address(self):
        app = DiscoveryRuntime(
            root=ROOT,
            environment={"AGENT_BUSINESS_ENV": "development", "AGENT_BUSINESS_WRITE_RATE_LIMIT_PER_MINUTE": "1"},
            session_secret="0123456789abcdef0123456789abcdef",
            event_sink=MemoryEventSink(),
            clock=lambda: FIXED_NOW,
            monotonic=lambda: 100.0,
        )
        status, _, _ = call_wsgi(app, "POST", "/v1/agent/hello", hello_payload())
        self.assertEqual(status, 200)
        status, _, response = call_wsgi(app, "POST", "/v1/agent/hello", hello_payload())
        self.assertEqual(status, 429)
        self.assertEqual(response["error"], "rate_limited")

    def test_production_fails_closed_without_persistent_session_secret(self):
        app = DiscoveryRuntime(
            root=ROOT,
            environment={"AGENT_BUSINESS_ENV": "production"},
            session_secret=None,
            event_sink=MemoryEventSink(durable=True),
            clock=lambda: FIXED_NOW,
        )
        status, _, health = call_wsgi(app, "GET", "/healthz")
        self.assertEqual(status, 503)
        self.assertFalse(health["production_ready"])
        status, _, response = call_wsgi(app, "POST", "/v1/agent/hello", hello_payload())
        self.assertEqual(status, 503)
        self.assertEqual(response["error"], "production_not_ready")

    def test_production_fails_closed_without_durable_event_sink(self):
        app = DiscoveryRuntime(
            root=ROOT,
            environment={"AGENT_BUSINESS_ENV": "production"},
            session_secret="0123456789abcdef0123456789abcdef",
            event_sink=MemoryEventSink(durable=False),
            clock=lambda: FIXED_NOW,
        )
        status, _, health = call_wsgi(app, "GET", "/healthz")
        self.assertEqual(status, 503)
        self.assertFalse(health["production_ready"])

    def test_production_is_ready_only_with_secret_and_durable_sink(self):
        app = DiscoveryRuntime(
            root=ROOT,
            environment={"AGENT_BUSINESS_ENV": "production", "AGENT_BUSINESS_RELEASE_ID": "test-release"},
            session_secret="0123456789abcdef0123456789abcdef",
            event_sink=MemoryEventSink(durable=True),
            clock=lambda: FIXED_NOW,
        )
        status, _, health = call_wsgi(app, "GET", "/healthz")
        self.assertEqual(status, 200)
        self.assertTrue(health["production_ready"])
        self.assertEqual(health["release_id"], "test-release")

    def test_schema_endpoint_is_available(self):
        app = self.make_app()
        status, headers, body = call_wsgi(app, "GET", "/schemas/agent-hello.schema.json")
        self.assertEqual(status, 200)
        self.assertIn("application/schema+json", headers["Content-Type"])
        self.assertIn("Agent Business Hello Request", body)


if __name__ == "__main__":
    unittest.main()
