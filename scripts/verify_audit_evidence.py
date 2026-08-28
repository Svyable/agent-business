#!/usr/bin/env python3
"""Validate and verify portable Agent Business audit-evidence records."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "agent-index.json"

PROHIBITED_KEYS = {
    "password", "secret", "api_key", "access_token", "refresh_token", "authorization_header",
    "credential", "credentials", "raw_prompt", "private_prompt", "private_customer_data", "executable_command"
}
CONSEQUENTIAL_EVENTS = {"tool_call", "side_effect", "billing_metering"}
SIGNED_MODES = {"signed_hash_chain", "external_anchor"}


def fail(message: str) -> None:
    raise SystemExit(f"audit-evidence verification failed: {message}")


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot parse {path}: {exc}")
    if not isinstance(value, dict):
        fail("record must be a JSON object")
    return value


def parse_time(value: object, label: str) -> datetime:
    if not isinstance(value, str):
        fail(f"{label} must be an ISO-8601 date-time")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        fail(f"{label} must be an ISO-8601 date-time")
    if result.tzinfo is None:
        fail(f"{label} must include a timezone")
    return result


def scan(value: object, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in PROHIBITED_KEYS:
                fail(f"prohibited sensitive field: {path}.{key}")
            scan(child, f"{path}.{key}")
    elif isinstance(value, list):
        for i, child in enumerate(value):
            scan(child, f"{path}[{i}]")


def evidence_map(items: object) -> dict[str, dict]:
    if not isinstance(items, list):
        fail("evidence must be a list")
    result: dict[str, dict] = {}
    for item in items:
        if not isinstance(item, dict):
            fail("evidence entries must be objects")
        evidence_id = item.get("id")
        if not isinstance(evidence_id, str) or not evidence_id:
            fail("evidence entries need non-empty ids")
        if evidence_id in result:
            fail(f"duplicate evidence id: {evidence_id}")
        parse_time(item.get("observed_at"), f"evidence {evidence_id}.observed_at")
        if item.get("status") not in {"current", "superseded", "unverified"}:
            fail(f"evidence {evidence_id}.status is invalid")
        reference = item.get("reference")
        if not isinstance(reference, str) or not reference:
            fail(f"evidence {evidence_id}.reference must be non-empty")
        result[evidence_id] = item
    return result


def require_current_refs(refs: object, evidence: dict[str, dict], label: str) -> None:
    if not isinstance(refs, list):
        fail(f"{label} must be a list")
    for ref in refs:
        if ref not in evidence:
            fail(f"{label} references unknown evidence: {ref}")
        if evidence[ref].get("status") != "current":
            fail(f"{label} must reference current evidence: {ref}")


def canonical_event_hash(event: dict) -> str:
    fields = [
        event.get("sequence"), event.get("event_id"), event.get("occurred_at"), event.get("event_type"),
        event.get("run_id"), event.get("tenant_ref"), event.get("authority_ref"), event.get("prev_hash"),
        event.get("payload_digest")
    ]
    material = "|".join("" if value is None else str(value) for value in fields)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def validate(record: dict) -> None:
    required = {
        "schema_version", "policy_id", "status", "updated_at", "scope", "integrity", "roles",
        "retention", "export", "completeness", "evidence", "events", "privacy"
    }
    missing = sorted(required - set(record))
    if missing:
        fail(f"missing required fields: {', '.join(missing)}")
    if record.get("schema_version") != "1.0.0":
        fail("schema_version must be 1.0.0")
    if record.get("status") not in {"draft", "active", "suspended", "retired"}:
        fail("status is invalid")
    parse_time(record.get("updated_at"), "updated_at")
    scan(record)

    privacy = record.get("privacy")
    if not isinstance(privacy, dict):
        fail("privacy must be an object")
    for field in ("contains_credentials", "contains_raw_prompts", "contains_private_customer_data", "contains_executable_commands"):
        if privacy.get(field) is not False:
            fail(f"privacy.{field} must be false for portable public evidence")
    if privacy.get("public_disclosure_confirmed") is not True:
        fail("privacy.public_disclosure_confirmed must be true")

    export = record.get("export")
    if not isinstance(export, dict):
        fail("export must be an object")
    for field in ("cross_tenant_allowed", "include_raw_prompts", "include_credentials", "include_private_customer_data"):
        if export.get(field) is not False:
            fail(f"export.{field} must be false")
    if export.get("chain_of_custody_required") is not True:
        fail("export.chain_of_custody_required must be true")

    resources = {item.get("id") for item in load(INDEX).get("resources", []) if isinstance(item, dict)}
    for resource_id in record.get("repository_resources", []):
        if resource_id not in resources:
            fail(f"unknown repository resource: {resource_id}")

    evidence = evidence_map(record.get("evidence"))

    roles = record.get("roles")
    if not isinstance(roles, dict):
        fail("roles must be an object")
    authority_refs = roles.get("authority_evidence_ids", [])
    require_current_refs(authority_refs, evidence, "roles.authority_evidence_ids")
    privileged = any(roles.get(key) is True for key in ("can_delete", "can_change_retention", "can_release_hold"))
    if privileged and not authority_refs:
        fail("retention/deletion authority requires current authority evidence")
    if roles.get("runtime_writer") == roles.get("evidence_custodian") and record.get("status") == "active":
        fail("active records must separate runtime writer from evidence custodian")

    retention = record.get("retention")
    if not isinstance(retention, dict):
        fail("retention must be an object")
    classes = retention.get("classes")
    if not isinstance(classes, list) or not classes:
        fail("retention.classes must be a non-empty list")
    seen_classes: set[str] = set()
    for item in classes:
        if not isinstance(item, dict):
            fail("retention classes must be objects")
        class_id = item.get("id")
        if not isinstance(class_id, str) or not class_id or class_id in seen_classes:
            fail("retention class ids must be unique and non-empty")
        seen_classes.add(class_id)
        minimum = item.get("min_days")
        maximum = item.get("max_days")
        if not isinstance(minimum, int) or minimum < 0:
            fail("retention min_days must be a non-negative integer")
        if maximum is not None and (not isinstance(maximum, int) or maximum < minimum):
            fail("retention max_days must be null or >= min_days")
    if retention.get("active_hold") is True:
        if not retention.get("hold_reference"):
            fail("active retention hold requires hold_reference")
        if retention.get("deletion_requested") is True:
            fail("deletion must fail closed while an evidence hold is active")
    if retention.get("deletion_requested") is True and roles.get("can_delete") is not True:
        fail("deletion request requires explicit deletion authority")

    integrity = record.get("integrity")
    if not isinstance(integrity, dict):
        fail("integrity must be an object")
    mode = integrity.get("mode")
    level = integrity.get("level")
    if mode not in {"none", "hash_chain", "signed_hash_chain", "external_anchor"}:
        fail("integrity.mode is invalid")
    if level not in {"observed_unverified", "internally_checked", "independently_verifiable", "externally_anchored"}:
        fail("integrity.level is invalid")
    verification_refs = integrity.get("verification_evidence_ids", [])
    require_current_refs(verification_refs, evidence, "integrity.verification_evidence_ids")
    if integrity.get("integrity_proven") is True and (mode == "none" or not verification_refs):
        fail("integrity_proven requires a configured mechanism and current verification evidence")
    if mode in SIGNED_MODES:
        if level not in {"independently_verifiable", "externally_anchored"}:
            fail("signed/external integrity modes require independently verifiable or anchored level")
        types = {evidence[ref].get("type") for ref in verification_refs}
        needed = "external_anchor" if mode == "external_anchor" else "signature_verification"
        if needed not in types:
            fail(f"{mode} requires current {needed} evidence")
    if mode == "hash_chain" and integrity.get("algorithm") != "sha256":
        fail("hash_chain mode requires sha256 algorithm")
    if mode == "none" and integrity.get("algorithm") != "none":
        fail("none integrity mode requires none algorithm")

    events = record.get("events")
    if not isinstance(events, list):
        fail("events must be a list")
    scope = record.get("scope")
    if not isinstance(scope, dict):
        fail("scope must be an object")
    tenant_scope = scope.get("tenant_scope")
    event_classes = set(scope.get("event_classes", []))
    seen_ids: set[str] = set()
    expected_sequence = 1
    previous_hash = "GENESIS"
    previous_time: datetime | None = None
    missing_authority = 0
    tool_events = 0

    for index, event in enumerate(events):
        if not isinstance(event, dict):
            fail("events must contain objects")
        event_id = event.get("event_id")
        if not isinstance(event_id, str) or not event_id or event_id in seen_ids:
            fail("event ids must be unique and non-empty")
        seen_ids.add(event_id)
        if event.get("sequence") != expected_sequence:
            fail(f"event sequence must be contiguous: expected {expected_sequence}")
        expected_sequence += 1
        occurred_at = parse_time(event.get("occurred_at"), f"events[{index}].occurred_at")
        if previous_time is not None and occurred_at < previous_time:
            fail("events must be chronological")
        previous_time = occurred_at
        if event.get("tenant_ref") != tenant_scope:
            fail("portable evidence stream cannot mix tenant scope")
        event_type = event.get("event_type")
        if event_type not in event_classes:
            fail(f"event type not declared in scope: {event_type}")
        if event_type == "tool_call":
            tool_events += 1
        if event_type in CONSEQUENTIAL_EVENTS and not event.get("authority_ref"):
            missing_authority += 1
        if event_type == "side_effect" and not event.get("side_effect_receipt_ref"):
            fail("side-effect events require a receipt/reference")
        digest = event.get("payload_digest")
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            fail("payload_digest must be a lowercase SHA-256 hex digest")

        if mode in {"hash_chain", "signed_hash_chain", "external_anchor"}:
            if event.get("prev_hash") != previous_hash:
                fail(f"broken hash chain at event {event_id}")
            expected_hash = canonical_event_hash(event)
            if event.get("event_hash") != expected_hash:
                fail(f"event hash mismatch at event {event_id}")
            previous_hash = expected_hash
        else:
            if event.get("prev_hash") or event.get("event_hash"):
                fail("unverified mode must not pretend event hashes are verified")

    completeness = record.get("completeness")
    if not isinstance(completeness, dict):
        fail("completeness must be an object")
    captured = completeness.get("captured_event_count")
    if captured != len(events):
        fail("captured_event_count must equal actual event count")
    if completeness.get("missing_authority_links") != missing_authority:
        fail("missing_authority_links does not match consequential events")
    claim = completeness.get("claim")
    expected = completeness.get("expected_event_count")
    if claim == "complete_for_declared_scope":
        if expected is None or expected != captured:
            fail("complete scope claim requires expected_event_count == captured_event_count")
        if completeness.get("orphan_tool_calls") != 0 or missing_authority != 0:
            fail("complete scope claim cannot have orphan tool calls or missing authority links")
        if not completeness.get("scope_start") or not completeness.get("scope_end"):
            fail("complete scope claim requires explicit scope_start and scope_end")
        start = parse_time(completeness.get("scope_start"), "completeness.scope_start")
        end = parse_time(completeness.get("scope_end"), "completeness.scope_end")
        if end < start:
            fail("completeness scope_end cannot precede scope_start")
        coverage_refs = [item for item in evidence.values() if item.get("type") == "coverage_report" and item.get("status") == "current"]
        if not coverage_refs:
            fail("complete scope claim requires current coverage-report evidence")
    if claim not in {"unknown", "partial", "complete_for_declared_scope"}:
        fail("completeness.claim is invalid")

    if record.get("status") == "active":
        if not events:
            fail("active audit policy requires captured events")
        if mode == "none":
            fail("active audit policy requires an integrity mechanism")
        if integrity.get("integrity_proven") is not True:
            fail("active audit policy requires proven integrity under its declared trust model")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", nargs="?", default="templates/AUDIT_EVIDENCE_RECORD.json")
    args = parser.parse_args()
    path = (ROOT / args.record).resolve()
    if path != ROOT and ROOT not in path.parents:
        fail("record path must stay inside repository")
    record = load(path)
    validate(record)
    print(
        f"audit evidence OK: {record['policy_id']} status={record['status']} "
        f"events={len(record['events'])} completeness={record['completeness']['claim']}"
    )


if __name__ == "__main__":
    main()
