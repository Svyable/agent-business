#!/usr/bin/env python3
from __future__ import annotations

import io
import json
import unittest
from urllib.error import URLError
from urllib.request import Request

from service.deployment import (
    DurableHttpEventSink,
    EventSinkUnavailable,
    SinkConfig,
    create_deployment_app,
    sink_from_environment,
)


class FakeResponse:
    def __init__(self, payload: dict, status: int = 200) -> None:
        self.payload = payload
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, _limit: int = -1) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class FakeOpener:
    def __init__(self, *, health: dict | None = None, ingest_factory=None, fail: bool = False) -> None:
        self.health = health or {"status": "ready", "durable": True}
        self.ingest_factory = ingest_factory or (
            lambda event: {"persisted": True, "event_id": event["event_id"]}
        )
        self.fail = fail
        self.requests: list[tuple[Request, float]] = []

    def __call__(self, request: Request, timeout: float):
        self.requests.append((request, timeout))
        if self.fail:
            raise URLError("offline")
        if request.full_url.endswith("/health"):
            return FakeResponse(self.health)
        body = json.loads((request.data or b"{}").decode("utf-8"))
        return FakeResponse(self.ingest_factory(body))


def call_wsgi(app, method: str, path: str, payload: dict | None = None):
    body = b"" if payload is None else json.dumps(payload).encode("utf-8")
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "CONTENT_LENGTH": str(len(body)),
        "CONTENT_TYPE": "application/json",
        "REMOTE_ADDR": "203.0.113.25",
        "wsgi.input": io.BytesIO(body),
    }
    captured = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)

    raw = b"".join(app(environ, start_response))
    decoded = json.loads(raw.decode("utf-8"))
    return int(captured["status"].split()[0]), captured["headers"], decoded


def production_env() -> dict[str, str]:
    return {
        "AGENT_BUSINESS_ENV": "production",
        "AGENT_BUSINESS_SESSION_SECRET": "0123456789abcdef0123456789abcdef",
        "AGENT_BUSINESS_EVENT_SINK_URL": "https://events.example.test/v1/events",
        "AGENT_BUSINESS_EVENT_SINK_HEALTH_URL": "https://events.example.test/health",
        "AGENT_BUSINESS_EVENT_SINK_TOKEN": "0123456789abcdef0123456789abcdef",
        "AGENT_BUSINESS_EVENT_SINK_HEALTH_CACHE_SECONDS": "10",
    }


def hello_payload() -> dict:
    return {
        "schema_version": "1.0.0",
        "client": {"type": "agent", "runtime": "deployment-test"},
        "intent": "start_business",
        "capabilities": {"can_persist_founder_packet": True, "protocols": ["http"]},
        "privacy": {"allow_pseudonymous_session": True, "allow_runtime_analytics": False},
    }


class DurableHttpEventSinkTests(unittest.TestCase):
    def make_sink(self, opener: FakeOpener, *, monotonic=lambda: 100.0):
        return DurableHttpEventSink(
            SinkConfig(
                ingest_url="https://events.example.test/v1/events",
                health_url="https://events.example.test/health",
                token="0123456789abcdef0123456789abcdef",
            ),
            opener=opener,
            monotonic=monotonic,
        )

    def test_health_requires_explicit_durable_attestation(self):
        self.assertTrue(self.make_sink(FakeOpener()).durable)
        self.assertFalse(
            self.make_sink(FakeOpener(health={"status": "ready", "durable": False})).durable
        )
        self.assertFalse(
            self.make_sink(FakeOpener(health={"status": "degraded", "durable": True})).durable
        )

    def test_health_failure_is_not_durable(self):
        self.assertFalse(self.make_sink(FakeOpener(fail=True)).durable)

    def test_health_is_cached_for_bounded_interval(self):
        values = iter([100.0, 105.0, 111.0])
        opener = FakeOpener()
        sink = self.make_sink(opener, monotonic=lambda: next(values))
        self.assertTrue(sink.durable)
        self.assertTrue(sink.durable)
        self.assertTrue(sink.durable)
        health_requests = [r for r, _ in opener.requests if r.full_url.endswith("/health")]
        self.assertEqual(len(health_requests), 2)

    def test_emit_requires_persisted_ack_for_same_event(self):
        opener = FakeOpener()
        sink = self.make_sink(opener)
        sink.emit({"event_id": "evt_12345678", "event_type": "agent_hello"})
        request, timeout = opener.requests[-1]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(timeout, 2.0)
        self.assertEqual(
            request.get_header("Authorization"),
            "Bearer 0123456789abcdef0123456789abcdef",
        )

    def test_emit_rejects_mismatched_ack(self):
        opener = FakeOpener(
            ingest_factory=lambda _event: {"persisted": True, "event_id": "evt_other"}
        )
        with self.assertRaises(EventSinkUnavailable):
            self.make_sink(opener).emit({"event_id": "evt_12345678"})

    def test_emit_rejects_non_persistence_ack(self):
        opener = FakeOpener(
            ingest_factory=lambda event: {"persisted": False, "event_id": event["event_id"]}
        )
        with self.assertRaises(EventSinkUnavailable):
            self.make_sink(opener).emit({"event_id": "evt_12345678"})

    def test_sink_requires_https_and_nontrivial_token(self):
        with self.assertRaises(ValueError):
            DurableHttpEventSink(
                SinkConfig(
                    ingest_url="http://events.example.test/v1/events",
                    health_url="https://events.example.test/health",
                    token="0123456789abcdef",
                )
            )
        with self.assertRaises(ValueError):
            DurableHttpEventSink(
                SinkConfig(
                    ingest_url="https://events.example.test/v1/events",
                    health_url="https://events.example.test/health",
                    token="short",
                )
            )

    def test_partial_environment_configuration_is_rejected(self):
        with self.assertRaises(ValueError):
            sink_from_environment(
                {"AGENT_BUSINESS_EVENT_SINK_URL": "https://events.example.test/v1/events"}
            )


class DeploymentApplicationTests(unittest.TestCase):
    def test_production_health_is_ready_with_persistent_secret_and_live_durable_sink(self):
        opener = FakeOpener()
        app = create_deployment_app(environment=production_env(), opener=opener)
        status, _, health = call_wsgi(app, "GET", "/healthz")
        self.assertEqual(status, 200)
        self.assertTrue(health["production_ready"])
        self.assertTrue(health["durable_telemetry"])

    def test_production_health_fails_closed_when_sink_is_unavailable(self):
        app = create_deployment_app(environment=production_env(), opener=FakeOpener(fail=True))
        status, _, health = call_wsgi(app, "GET", "/healthz")
        self.assertEqual(status, 503)
        self.assertFalse(health["production_ready"])

    def test_production_health_fails_closed_without_session_secret(self):
        env = production_env()
        del env["AGENT_BUSINESS_SESSION_SECRET"]
        app = create_deployment_app(environment=env, opener=FakeOpener())
        status, _, health = call_wsgi(app, "GET", "/healthz")
        self.assertEqual(status, 503)
        self.assertFalse(health["production_ready"])

    def test_hello_is_503_when_persistence_fails_after_readiness(self):
        opener = FakeOpener(
            ingest_factory=lambda event: {"persisted": False, "event_id": event["event_id"]}
        )
        app = create_deployment_app(environment=production_env(), opener=opener)
        status, headers, response = call_wsgi(app, "POST", "/v1/agent/hello", hello_payload())
        self.assertEqual(status, 503)
        self.assertEqual(response["error"], "telemetry_unavailable")
        self.assertEqual(headers["Retry-After"], "30")

    def test_hello_persists_agent_hello_before_success_response(self):
        opener = FakeOpener()
        app = create_deployment_app(environment=production_env(), opener=opener)
        status, _, response = call_wsgi(app, "POST", "/v1/agent/hello", hello_payload())
        self.assertEqual(status, 200)
        self.assertEqual(response["actor_confidence"], "self_declared_agent")
        post_requests = [r for r, _ in opener.requests if r.get_method() == "POST"]
        self.assertEqual(len(post_requests), 1)
        persisted = json.loads((post_requests[0].data or b"{}").decode("utf-8"))
        self.assertEqual(persisted["event_type"], "agent_hello")
        self.assertFalse(persisted["privacy"]["raw_ip_retained"])
        self.assertFalse(persisted["privacy"]["raw_user_agent_retained"])


if __name__ == "__main__":
    unittest.main()
