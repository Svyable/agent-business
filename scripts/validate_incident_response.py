#!/usr/bin/env python3
"""Validate portable Agent Business incident-response records without third-party packages."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADVANCED = {"triaged", "contained", "investigating", "remediating", "recovery_verification", "monitoring", "closed", "reopened"}
RECOVERY_STATES = {"monitoring", "closed"}
PROHIBITED_KEYS = {
    "password", "secret", "api_key", "access_token", "refresh_token", "authorization_header",
    "private_prompt", "raw_prompt", "private_customer_data", "credential", "exploit_payload"
}
AUTHORITY_BY_ACTION = {
    "pause_intake": "can_pause_intake",
    "disable_tool": "can_disable_tool",
    "read_only_mode": "can_pause_intake",
    "isolate_tenant": "can_isolate_tenant",
    "freeze_release": "can_rollback_release",
    "disable_dependency": "can_disable_tool",
    "revoke_authority": "can_revoke_authority",
    "kill_switch": "can_pause_intake",
}


def fail(message: str) -> None:
    raise SystemExit(f"incident-response validation failed: {message}")


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
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        fail(f"{label} must be an ISO-8601 date-time")
    if parsed.tzinfo is None:
        fail(f"{label} must include a timezone")
    return parsed


def scan(value: object, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in PROHIBITED_KEYS:
                fail(f"prohibited sensitive field: {path}.{key}")
            scan(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan(child, f"{path}[{index}]")


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


def require_refs(refs: object, evidence: dict[str, dict], label: str, current: bool = False) -> None:
    if not isinstance(refs, list):
        fail(f"{label} must be a list")
    unknown = [ref for ref in refs if ref not in evidence]
    if unknown:
        fail(f"{label} references unknown evidence: {', '.join(unknown)}")
    if current:
        stale = [ref for ref in refs if evidence[ref].get("status") != "current"]
        if stale:
            fail(f"{label} must reference current evidence: {', '.join(stale)}")


def validate(record: dict) -> None:
    required = {
        "schema_version", "incident_id", "status", "severity", "detected_at", "updated_at",
        "detection", "affected_scope", "impact", "timeline", "evidence", "authority", "containment",
        "investigation", "side_effects", "customer_impact", "recovery", "corrective_actions", "privacy"
    }
    missing = sorted(required - set(record))
    if missing:
        fail(f"missing required fields: {', '.join(missing)}")
    if record.get("schema_version") != "1.0.0":
        fail("schema_version must be 1.0.0")
    if not isinstance(record.get("incident_id"), str) or not record["incident_id"]:
        fail("incident_id must be non-empty")
    status = record.get("status")
    if status not in {"detected", "triaged", "contained", "investigating", "remediating", "recovery_verification", "monitoring", "closed", "reopened"}:
        fail("status is invalid")
    severity = record.get("severity")
    if severity not in {"SEV0", "SEV1", "SEV2", "SEV3", "SEV4", "unclassified"}:
        fail("severity is invalid")
    detected_at = parse_time(record.get("detected_at"), "detected_at")
    updated_at = parse_time(record.get("updated_at"), "updated_at")
    if updated_at < detected_at:
        fail("updated_at cannot precede detected_at")
    scan(record)

    privacy = record.get("privacy")
    if not isinstance(privacy, dict):
        fail("privacy must be an object")
    for field in ("contains_credentials", "contains_private_customer_data", "contains_secret_prompts", "contains_exploit_instructions"):
        if privacy.get(field) is not False:
            fail(f"privacy.{field} must be false for a portable public record")
    if privacy.get("public_disclosure_confirmed") is not True:
        fail("privacy.public_disclosure_confirmed must be true")

    evidence = evidence_map(record.get("evidence"))
    detection = record.get("detection")
    impact = record.get("impact")
    authority = record.get("authority")
    containment = record.get("containment")
    investigation = record.get("investigation")
    customer = record.get("customer_impact")
    recovery = record.get("recovery")
    if not all(isinstance(item, dict) for item in (detection, impact, authority, containment, investigation, customer, recovery)):
        fail("detection/impact/authority/containment/investigation/customer_impact/recovery must be objects")

    require_refs(detection.get("evidence_ids", []), evidence, "detection.evidence_ids")
    severity_refs = impact.get("severity_evidence_ids", [])
    require_refs(severity_refs, evidence, "impact.severity_evidence_ids", current=True)
    if status in ADVANCED:
        if severity == "unclassified":
            fail(f"{status} incidents require a classified severity")
        if not severity_refs:
            fail(f"{status} incidents require current severity evidence")

    timeline = record.get("timeline")
    if not isinstance(timeline, list) or not timeline:
        fail("timeline must contain at least one event")
    previous: datetime | None = None
    for index, item in enumerate(timeline):
        if not isinstance(item, dict):
            fail("timeline entries must be objects")
        at = parse_time(item.get("at"), f"timeline[{index}].at")
        if at < detected_at:
            fail("timeline cannot contain events before detected_at")
        if previous and at < previous:
            fail("timeline must be chronological")
        previous = at
        require_refs(item.get("evidence_ids", []), evidence, f"timeline[{index}].evidence_ids")

    authority_refs = authority.get("evidence_ids", [])
    require_refs(authority_refs, evidence, "authority.evidence_ids", current=True)
    authority_keys = (
        "can_pause_intake", "can_disable_tool", "can_isolate_tenant", "can_revoke_authority",
        "can_rollback_release", "can_contact_customers", "can_issue_credits", "can_move_money"
    )
    material_authority = any(authority.get(key) is True for key in authority_keys)
    if material_authority and not authority_refs:
        fail("material incident authority requires current authority evidence")

    actions = containment.get("actions")
    if not isinstance(actions, list):
        fail("containment.actions must be a list")
    executed_count = 0
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            fail("containment actions must be objects")
        refs = action.get("evidence_ids", [])
        require_refs(refs, evidence, f"containment.actions[{index}].evidence_ids", current=True)
        if action.get("executed") is True:
            executed_count += 1
            if not refs:
                fail("executed containment actions require current evidence")
            action_type = action.get("type")
            authority_key = AUTHORITY_BY_ACTION.get(action_type)
            if action.get("authority_required") is True and authority_key and authority.get(authority_key) is not True:
                fail(f"executed containment action {action_type} lacks declared authority")
    contained_at = containment.get("contained_at")
    if status in {"contained", "investigating", "remediating", "recovery_verification", "monitoring", "closed"}:
        if executed_count == 0 or contained_at is None:
            fail(f"{status} incidents require executed containment and contained_at")
        contained_time = parse_time(contained_at, "containment.contained_at")
        if contained_time < detected_at:
            fail("contained_at cannot precede detected_at")

    facts = investigation.get("facts")
    if not isinstance(facts, list):
        fail("investigation.facts must be a list")
    for index, fact in enumerate(facts):
        if not isinstance(fact, dict):
            fail("investigation facts must be objects")
        refs = fact.get("evidence_ids", [])
        require_refs(refs, evidence, f"investigation.facts[{index}].evidence_ids", current=True)
        if not refs:
            fail("observed facts require current evidence")
    root_status = investigation.get("root_cause_status")
    if root_status not in {"unknown", "hypothesis", "confirmed"}:
        fail("investigation.root_cause_status is invalid")
    root_refs = investigation.get("root_cause_evidence_ids", [])
    require_refs(root_refs, evidence, "investigation.root_cause_evidence_ids", current=True)
    if root_status == "confirmed" and (not investigation.get("root_cause") or not root_refs):
        fail("confirmed root cause requires a statement and current evidence")
    if root_status != "confirmed" and root_refs:
        fail("root-cause evidence may only be asserted when root cause is confirmed")

    side_effects = record.get("side_effects")
    if not isinstance(side_effects, list):
        fail("side_effects must be a list")
    material_uncertain = []
    operation_ids: set[str] = set()
    for index, item in enumerate(side_effects):
        if not isinstance(item, dict):
            fail("side-effect entries must be objects")
        operation_id = item.get("operation_id")
        if not isinstance(operation_id, str) or not operation_id:
            fail("side effects need non-empty operation_id")
        if operation_id in operation_ids:
            fail(f"duplicate side-effect operation_id: {operation_id}")
        operation_ids.add(operation_id)
        refs = item.get("evidence_ids", [])
        require_refs(refs, evidence, f"side_effects[{index}].evidence_ids")
        if item.get("state") != "uncertain" and not refs:
            fail("resolved side effects require evidence")
        if item.get("material") is True and item.get("state") == "uncertain":
            material_uncertain.append(operation_id)

    if customer.get("assessed") is True:
        require_refs(customer.get("evidence_ids", []), evidence, "customer_impact.evidence_ids")
    if status in {"recovery_verification", "monitoring", "closed"} and customer.get("assessed") is not True:
        fail(f"{status} incidents require customer-impact assessment")
    notification = customer.get("notification_decision")
    if notification == "required":
        comms = customer.get("communication_evidence_ids", [])
        require_refs(comms, evidence, "customer_impact.communication_evidence_ids", current=True)
        if status == "closed" and not comms:
            fail("closed incidents requiring customer notification need communication evidence")
    if status == "closed" and notification in {"unknown", "pending_policy_or_legal_review"}:
        fail("closed incidents require a resolved customer notification decision")

    recovery_refs = recovery.get("verification_evidence_ids", [])
    require_refs(recovery_refs, evidence, "recovery.verification_evidence_ids", current=True)
    if status in RECOVERY_STATES:
        gates = (
            "trigger_removed", "identity_authority_healthy", "security_policy_healthy", "data_integrity_healthy",
            "side_effects_reconciled", "observability_healthy", "production_authority_valid"
        )
        failed_gates = [gate for gate in gates if recovery.get(gate) is not True]
        if failed_gates:
            fail(f"{status} incidents have failed recovery gates: {', '.join(failed_gates)}")
        if material_uncertain:
            fail(f"{status} incidents have unresolved material side effects: {', '.join(material_uncertain)}")
        if not recovery_refs or recovery.get("verified_at") is None:
            fail(f"{status} incidents require current recovery verification evidence and verified_at")
        verified_at = parse_time(recovery.get("verified_at"), "recovery.verified_at")
        if verified_at < detected_at:
            fail("recovery.verified_at cannot precede detected_at")

    actions = record.get("corrective_actions")
    if not isinstance(actions, list):
        fail("corrective_actions must be a list")
    seen_actions: set[str] = set()
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            fail("corrective actions must be objects")
        action_id = action.get("id")
        if not isinstance(action_id, str) or not action_id:
            fail("corrective actions need non-empty ids")
        if action_id in seen_actions:
            fail(f"duplicate corrective action id: {action_id}")
        seen_actions.add(action_id)
        parse_time(action.get("due_at"), f"corrective_actions[{index}].due_at")
        refs = action.get("verification_evidence_ids", [])
        require_refs(refs, evidence, f"corrective_actions[{index}].verification_evidence_ids", current=True)
        if action.get("status") == "verified" and not refs:
            fail("verified corrective actions require current verification evidence")
        if action.get("status") == "waived" and not action.get("waiver_reason"):
            fail("waived corrective actions require a waiver reason")
    if status == "closed":
        unresolved = [action.get("id") for action in actions if action.get("status") not in {"verified", "waived"}]
        if unresolved:
            fail(f"closed incidents have unresolved corrective actions: {', '.join(unresolved)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", nargs="?", default="templates/INCIDENT_RESPONSE_RECORD.json")
    args = parser.parse_args()
    path = (ROOT / args.record).resolve()
    if path != ROOT and ROOT not in path.parents:
        fail("record path must stay inside repository")
    record = load(path)
    validate(record)
    print(f"incident response OK: {record['incident_id']} status={record['status']} severity={record['severity']} evidence={len(record['evidence'])}")


if __name__ == "__main__":
    main()
