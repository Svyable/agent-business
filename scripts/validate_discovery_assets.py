#!/usr/bin/env python3
"""Validate Agent Business discovery/hello machine assets without third-party packages."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVENT = ROOT / "templates" / "AGENT_DISCOVERY_EVENT.json"
HELLO = ROOT / "templates" / "AGENT_HELLO.json"
EVENT_SCHEMA = ROOT / "schemas" / "agent-discovery-event.schema.json"
HELLO_SCHEMA = ROOT / "schemas" / "agent-hello.schema.json"
INDEX = ROOT / "agent-index.json"

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


def fail(message: str) -> None:
    raise SystemExit(f"discovery asset validation failed: {message}")


def load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot parse {path.relative_to(ROOT)}: {exc}")
    if not isinstance(data, dict):
        fail(f"{path.relative_to(ROOT)} must contain a JSON object")
    return data


def scan_prohibited(value: object, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = key.lower().replace("-", "_")
            if normalized in PROHIBITED_KEYS:
                fail(f"prohibited sensitive field {path}.{key}")
            scan_prohibited(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_prohibited(child, f"{path}[{index}]")


def validate_event(event: dict) -> None:
    if event.get("schema_version") != "1.0.0":
        fail("discovery event schema_version must be 1.0.0")
    if event.get("event_type") not in EVENT_TYPES:
        fail("discovery event has unsupported event_type")
    event_id = event.get("event_id")
    if not isinstance(event_id, str) or len(event_id) < 8:
        fail("discovery event needs a stable event_id of at least 8 characters")
    occurred_at = event.get("occurred_at")
    if not isinstance(occurred_at, str) or "T" not in occurred_at:
        fail("discovery event occurred_at must be an ISO-like date-time string")

    actor = event.get("actor")
    if not isinstance(actor, dict) or actor.get("confidence") not in ACTOR_CONFIDENCE:
        fail("discovery event actor.confidence is invalid")

    source = event.get("source")
    if not isinstance(source, dict) or source.get("channel") not in CHANNELS:
        fail("discovery event source.channel is invalid")

    privacy = event.get("privacy")
    if not isinstance(privacy, dict):
        fail("discovery event requires privacy controls")
    for field in ("raw_ip_retained", "contains_prompt_content", "contains_secrets"):
        if privacy.get(field) is not False:
            fail(f"discovery event privacy.{field} must be false")

    scan_prohibited(event)


def validate_hello(hello: dict, index: dict) -> None:
    if hello.get("schema_version") != "1.0.0":
        fail("agent hello schema_version must be 1.0.0")
    client = hello.get("client")
    if not isinstance(client, dict) or client.get("type") != "agent":
        fail("agent hello client.type must be agent")
    if hello.get("intent") not in INTENTS:
        fail("agent hello intent is invalid")

    capabilities = hello.get("capabilities")
    if not isinstance(capabilities, dict):
        fail("agent hello requires capabilities")
    if not isinstance(capabilities.get("can_persist_founder_packet"), bool):
        fail("agent hello capabilities.can_persist_founder_packet must be boolean")
    protocols = capabilities.get("protocols")
    if not isinstance(protocols, list) or any(not isinstance(item, str) or not item for item in protocols):
        fail("agent hello capabilities.protocols must be a list of non-empty strings")

    privacy = hello.get("privacy")
    if not isinstance(privacy, dict) or not isinstance(privacy.get("allow_pseudonymous_session"), bool):
        fail("agent hello requires explicit privacy.allow_pseudonymous_session")

    requested = hello.get("requested_start")
    if requested is not None:
        if not isinstance(requested, dict):
            fail("agent hello requested_start must be an object")
        resources = {resource.get("id"): resource for resource in index.get("resources", []) if isinstance(resource, dict)}
        resource_id = requested.get("resource_id")
        if resource_id is not None and resource_id not in resources:
            fail(f"agent hello requested_start references unknown resource {resource_id}")
        stage = requested.get("stage")
        if resource_id in resources and stage is not None and resources[resource_id].get("stage") != stage:
            fail("agent hello requested_start stage does not match indexed resource")

    scan_prohibited(hello)


def validate_schema_shape(schema: dict, name: str) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail(f"{name} must declare JSON Schema draft 2020-12")
    if schema.get("type") != "object":
        fail(f"{name} top-level type must be object")
    required = schema.get("required")
    if not isinstance(required, list) or not required:
        fail(f"{name} must declare required fields")


def main() -> None:
    event = load(EVENT)
    hello = load(HELLO)
    event_schema = load(EVENT_SCHEMA)
    hello_schema = load(HELLO_SCHEMA)
    index = load(INDEX)

    validate_schema_shape(event_schema, EVENT_SCHEMA.name)
    validate_schema_shape(hello_schema, HELLO_SCHEMA.name)
    validate_event(event)
    validate_hello(hello, index)

    print("discovery assets OK: schemas parse, templates are semantically safe, indexed hello start is valid")


if __name__ == "__main__":
    main()
