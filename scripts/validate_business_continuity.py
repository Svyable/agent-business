#!/usr/bin/env python3
"""Validate Agent Business continuity and disaster-recovery records."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "agent-index.json"
READY = {"recovery_ready", "incident", "degraded", "recovering", "recovered"}
RETURNING = {"recovered"}
CONTROL_ORDER = ["identity","policy","data","credentials","models_tools","retrieval","agents","queues","billing","traffic"]
REQUIRED_DRILLS = {
    "restore_failure", "stale_config", "dependency_unavailable", "retrieval_corruption",
    "partial_memory", "control_plane_outage", "duplicate_replay", "economic_action_replay",
    "premature_traffic", "premature_failback",
}
PROHIBITED_KEYS = {
    "password", "secret", "api_key", "access_token", "refresh_token", "authorization",
    "recovery_key", "recovery_keys", "raw_backup", "raw_backups", "raw_customer_data",
    "private_customer_data", "private_prompt", "private_prompts", "credential_value",
}


def fail(message: str) -> None:
    raise SystemExit(f"business-continuity validation failed: {message}")


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
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            fail("evidence entries need non-empty ids")
        if item_id in result:
            fail(f"duplicate evidence id: {item_id}")
        parse_time(item.get("observed_at"), f"evidence {item_id}.observed_at")
        url = item.get("public_url")
        if url is not None:
            parsed = urlparse(url)
            if parsed.scheme != "https" or not parsed.netloc:
                fail(f"evidence {item_id}.public_url must be absolute https")
        result[item_id] = item
    return result


def refs_current(refs: object, evidence: dict[str, dict], label: str) -> None:
    if not isinstance(refs, list):
        fail(f"{label} must be a list")
    for ref in refs:
        if ref not in evidence:
            fail(f"{label} references unknown evidence: {ref}")
        if evidence[ref].get("status") != "current":
            fail(f"{label} must reference current evidence: {ref}")


def validate(record: dict) -> None:
    required = {"schema_version","continuity_id","status","updated_at","service","state_inventory","recovery_strategy","degraded_mode","authority","drills","recovery_gate","privacy","evidence"}
    missing = sorted(required - set(record))
    if missing:
        fail(f"missing required fields: {', '.join(missing)}")
    if record.get("schema_version") != "1.0.0":
        fail("schema_version must be 1.0.0")
    status = record.get("status")
    if status not in {"needs_review","planned","recovery_ready","incident","degraded","recovering","recovered"}:
        fail("status is invalid")
    parse_time(record.get("updated_at"), "updated_at")
    scan(record)

    resources = {item.get("id") for item in load(INDEX).get("resources", []) if isinstance(item, dict)}
    for resource_id in record.get("repository_resources", []):
        if resource_id not in resources:
            fail(f"unknown repository resource: {resource_id}")

    evidence = evidence_map(record.get("evidence"))
    privacy = record.get("privacy")
    if not isinstance(privacy, dict):
        fail("privacy must be an object")
    for field in ("contains_secrets","contains_raw_backups","contains_private_customer_data","contains_private_prompts","contains_recovery_keys"):
        if privacy.get(field) is not False:
            fail(f"privacy.{field} must be false")
    if privacy.get("public_disclosure_confirmed") is not True:
        fail("privacy.public_disclosure_confirmed must be true")

    service = record.get("service")
    strategy = record.get("recovery_strategy")
    degraded = record.get("degraded_mode")
    authority = record.get("authority")
    gate = record.get("recovery_gate")
    if not all(isinstance(x, dict) for x in (service, strategy, degraded, authority, gate)):
        fail("service/recovery_strategy/degraded_mode/authority/recovery_gate must be objects")

    rto = service.get("rto_minutes")
    rpo = service.get("rpo_minutes")
    mtd = service.get("maximum_tolerable_downtime_minutes")
    for label, value in (("rto_minutes", rto), ("rpo_minutes", rpo), ("maximum_tolerable_downtime_minutes", mtd)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            fail(f"service.{label} must be a non-negative integer")
    if rto > mtd:
        fail("RTO cannot exceed maximum tolerable downtime")

    inventory = record.get("state_inventory")
    if not isinstance(inventory, list) or not inventory:
        fail("state_inventory must be a non-empty list")
    seen_components: set[str] = set()
    for item in inventory:
        if not isinstance(item, dict):
            fail("state inventory entries must be objects")
        component = item.get("component")
        if component in seen_components:
            fail(f"duplicate state component: {component}")
        seen_components.add(component)
        if status in READY:
            if item.get("recovery_owner") in {None,"","needs_review"}:
                fail(f"{component} requires a resolved recovery owner")
            if item.get("recovery_class") in {"reconstructable","backed_up","replicated"}:
                if item.get("procedure_defined") is not True:
                    fail(f"{component} requires a defined recovery procedure")
                refs = item.get("evidence_ids", [])
                refs_current(refs, evidence, f"{component} recovery evidence")
                if not refs:
                    fail(f"{component} requires current recovery evidence")
            if item.get("contains_customer_state") and item.get("recovery_class") == "ephemeral":
                fail(f"customer state {component} cannot be silently classified as ephemeral")

    order = strategy.get("dependency_order")
    if not isinstance(order, list) or order != CONTROL_ORDER:
        fail("dependency_order must restore identity/policy/data controls before traffic")
    for field in ("queue_replay_requires_idempotency","economic_actions_require_reconciliation","failback_requires_convergence"):
        if strategy.get(field) is not True:
            fail(f"recovery_strategy.{field} must be true")
    if status in READY and strategy.get("secondary_failure_domain") in {None,"","needs_review"}:
        fail(f"{status} requires a resolved secondary failure domain or recovery target")

    if service.get("degraded_mode_required"):
        if status in READY and (degraded.get("defined") is not True or degraded.get("authority_bounded") is not True):
            fail(f"{status} requires a defined, authority-bounded degraded mode")
    if status in {"degraded","recovering","recovered"} and degraded.get("customer_impact_recorded") is not True:
        fail(f"{status} requires customer-impact recording")

    auth_refs = authority.get("authority_evidence_ids", [])
    refs_current(auth_refs, evidence, "recovery authority evidence")
    material = any(authority.get(k) for k in ("can_failover","can_restore","can_replay_work","can_switch_provider","can_resume_normal_traffic","can_failback"))
    if material and not auth_refs:
        fail("material recovery authority requires current authority evidence")
    if status == "recovery_ready":
        if authority.get("can_restore") is not True:
            fail("recovery_ready requires explicit restore/reconstruction authority")
        if strategy.get("mode") != "cold" and authority.get("can_failover") is not True:
            fail("non-cold recovery_ready strategy requires failover authority")

    drills = record.get("drills")
    if not isinstance(drills, list):
        fail("drills must be a list")
    drill_map: dict[str, dict] = {}
    for drill in drills:
        if not isinstance(drill, dict):
            fail("drill entries must be objects")
        scenario = drill.get("scenario")
        if scenario in drill_map:
            fail(f"duplicate drill scenario: {scenario}")
        drill_map[scenario] = drill
        parse_time(drill.get("observed_at"), f"drill {scenario}.observed_at")
        refs = drill.get("evidence_ids", [])
        refs_current(refs, evidence, f"drill {scenario} evidence")
        for label in ("recovery_time_minutes","recovered_rpo_minutes"):
            value = drill.get(label)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                fail(f"drill {scenario}.{label} must be a non-negative integer")
    if status in READY:
        missing_drills = sorted(REQUIRED_DRILLS - set(drill_map))
        if missing_drills:
            fail(f"{status} missing recovery drills: {', '.join(missing_drills)}")
        for scenario in REQUIRED_DRILLS:
            drill = drill_map[scenario]
            if drill.get("status") != "pass" or drill.get("integrity_ok") is not True or drill.get("reconciliation_ok") is not True:
                fail(f"drill {scenario} must pass integrity and reconciliation checks")
            if not drill.get("evidence_ids"):
                fail(f"drill {scenario} requires current evidence")
            if drill.get("recovery_time_minutes") > rto:
                fail(f"drill {scenario} exceeds declared RTO")
            if drill.get("recovered_rpo_minutes") > rpo:
                fail(f"drill {scenario} exceeds declared RPO")

    if status in RETURNING or authority.get("can_resume_normal_traffic"):
        required_gate = ("identity_ok","policy_ok","authority_ok","data_integrity_ok","dependencies_ok","retrieval_ok","queue_reconciled","billing_reconciled","customer_impact_handoff_ready")
        failed = [key for key in required_gate if gate.get(key) is not True]
        if failed:
            fail(f"normal traffic blocked by recovery gate: {', '.join(failed)}")
        if authority.get("can_resume_normal_traffic") is not True:
            fail("recovered status requires explicit authority to resume normal traffic")

    if authority.get("can_failback") and strategy.get("failback_requires_convergence") is not True:
        fail("failback authority requires convergence/reconciliation control")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", nargs="?", default="templates/BUSINESS_CONTINUITY_RECORD.json")
    args = parser.parse_args()
    path = (ROOT / args.record).resolve()
    if path != ROOT and ROOT not in path.parents:
        fail("record path must stay inside repository")
    record = load(path)
    validate(record)
    print(f"business continuity OK: {record['continuity_id']} status={record['status']} evidence={len(record['evidence'])}")


if __name__ == "__main__":
    main()
