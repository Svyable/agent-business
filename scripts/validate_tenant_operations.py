#!/usr/bin/env python3
"""Validate Agent Business tenant operations records without third-party packages."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "agent-index.json"
OPERATIONAL = {"operational", "suspended", "offboarding", "offboarded"}
REQUIRED_LAYERS = {"edge", "orchestrator", "model_session", "retrieval", "memory", "cache", "tools", "queues", "billing", "observability", "release_config"}
REQUIRED_TESTS = {"missing_context", "cross_tenant_retrieval", "memory_collision", "cache_leakage", "unauthorized_tool_routing", "downstream_quota_bypass", "noisy_neighbor", "billing_attribution", "release_leakage"}
PROHIBITED_KEYS = {"password", "secret", "api_key", "access_token", "refresh_token", "authorization", "credential", "credentials", "raw_prompt", "raw_customer_data", "customer_data", "tenant_name", "customer_name", "email"}


def fail(message: str) -> None:
    raise SystemExit(f"tenant-operations validation failed: {message}")


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
    required = {"schema_version","tenant_ref","status","updated_at","deployment","context_propagation","boundaries","quotas","entitlements","cost_attribution","observability","isolation_tests","offboarding","authority","privacy","evidence"}
    missing = sorted(required - set(record))
    if missing:
        fail(f"missing required fields: {', '.join(missing)}")
    if record.get("schema_version") != "1.0.0":
        fail("schema_version must be 1.0.0")
    status = record.get("status")
    if status not in {"needs_review","provisioning","operational","suspended","offboarding","offboarded"}:
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
    for field in ("contains_credentials","contains_private_customer_data","contains_private_prompts","contains_sensitive_tenant_identifiers"):
        if privacy.get(field) is not False:
            fail(f"privacy.{field} must be false")
    if privacy.get("public_disclosure_confirmed") is not True:
        fail("privacy.public_disclosure_confirmed must be true")

    context = record.get("context_propagation")
    if not isinstance(context, dict):
        fail("context_propagation must be an object")
    if context.get("prompt_text_authoritative") is not False:
        fail("prompt text cannot be authoritative tenant identity")
    if status in OPERATIONAL:
        if context.get("identity_source") == "needs_review":
            fail(f"{status} status requires resolved authenticated tenant identity")
        layers = set(context.get("layers", []))
        missing_layers = sorted(REQUIRED_LAYERS - layers)
        if missing_layers:
            fail(f"{status} status missing tenant context layers: {', '.join(missing_layers)}")

    boundaries = record.get("boundaries")
    if not isinstance(boundaries, list) or not boundaries:
        fail("boundaries must be a non-empty list")
    if status in OPERATIONAL:
        required_boundary_layers = {"runtime","retrieval","memory","cache","tools","data_store"}
        seen = {b.get("layer") for b in boundaries if isinstance(b, dict)}
        missing_boundaries = sorted(required_boundary_layers - seen)
        if missing_boundaries:
            fail(f"operational record missing boundaries: {', '.join(missing_boundaries)}")
        for boundary in boundaries:
            if not isinstance(boundary, dict):
                fail("boundary entries must be objects")
            if boundary.get("authorization_checked") is not True or boundary.get("tenant_scoped") is not True:
                fail(f"boundary {boundary.get('layer')} is not tenant-scoped and authorization-checked")
            refs_current(boundary.get("evidence_ids", []), evidence, f"boundary {boundary.get('layer')} evidence")
            if not boundary.get("evidence_ids"):
                fail(f"boundary {boundary.get('layer')} requires current evidence")

    quotas = record.get("quotas")
    if not isinstance(quotas, list) or not quotas:
        fail("quotas must be a non-empty list")
    for quota in quotas:
        if not isinstance(quota, dict):
            fail("quota entries must be objects")
        limit = quota.get("limit")
        if not isinstance(limit, (int, float)) or isinstance(limit, bool) or limit < 0:
            fail("quota limit must be non-negative")
    if status in OPERATIONAL:
        quota_layers = {q.get("layer") for q in quotas if isinstance(q, dict) and q.get("enforced") is True}
        if "edge" not in quota_layers:
            fail("operational record requires enforced edge quota")
        if not quota_layers.intersection({"inference","tools","queue","background_jobs","spend"}):
            fail("edge-only quotas are insufficient; enforce at a consequential downstream layer")
        for quota in quotas:
            if quota.get("enforced") is True:
                refs_current(quota.get("evidence_ids", []), evidence, f"quota {quota.get('layer')} evidence")
                if not quota.get("evidence_ids"):
                    fail(f"enforced quota {quota.get('layer')} requires current evidence")

    entitlements = record.get("entitlements")
    observability = record.get("observability")
    costs = record.get("cost_attribution")
    authority = record.get("authority")
    if not all(isinstance(x, dict) for x in (entitlements, observability, costs, authority)):
        fail("entitlements/observability/cost_attribution/authority must be objects")
    if status in OPERATIONAL:
        if entitlements.get("release_config_scoped") is not True:
            fail("operational tenant requires tenant-scoped release/config resolution")
        if observability.get("tenant_scoped") is not True or observability.get("missing_context_alert") is not True:
            fail("operational tenant requires tenant-scoped observability and missing-context alert")
        direct = ("inference","tools","storage_memory","retrieval","retries","background_jobs","human_review")
        if not any(costs.get(key) is True for key in direct):
            fail("operational tenant requires per-tenant direct cost attribution")
        if costs.get("shared_overhead_method") in {None,"","needs_review"}:
            fail("operational tenant requires resolved shared-overhead allocation method")

    refs_current(authority.get("authority_evidence_ids", []), evidence, "authority evidence")
    if any(authority.get(k) for k in ("can_activate","can_change_entitlements","can_change_quotas","can_offboard")) and not authority.get("authority_evidence_ids"):
        fail("material tenant authority requires current authority evidence")
    if status == "operational" and authority.get("can_activate") is not True:
        fail("operational status requires explicit activation authority")

    tests = record.get("isolation_tests")
    if not isinstance(tests, list):
        fail("isolation_tests must be a list")
    test_map = {}
    for test in tests:
        if not isinstance(test, dict):
            fail("isolation test entries must be objects")
        name = test.get("test")
        parse_time(test.get("observed_at"), f"isolation test {name}.observed_at")
        if name in test_map:
            fail(f"duplicate isolation test: {name}")
        test_map[name] = test
        refs_current(test.get("evidence_ids", []), evidence, f"isolation test {name} evidence")
    if status in OPERATIONAL:
        missing_tests = sorted(REQUIRED_TESTS - set(test_map))
        if missing_tests:
            fail(f"operational tenant missing isolation tests: {', '.join(missing_tests)}")
        for name in REQUIRED_TESTS:
            if test_map[name].get("status") != "pass" or not test_map[name].get("evidence_ids"):
                fail(f"isolation test {name} must pass with current evidence")

    offboarding = record.get("offboarding")
    if not isinstance(offboarding, dict):
        fail("offboarding must be an object")
    if status == "offboarded":
        completion = ("admission_disabled","credentials_revoked","jobs_disabled","data_disposition_complete","memory_cleanup_complete","billing_closed","audit_retention_resolved")
        incomplete = [key for key in completion if offboarding.get(key) is not True]
        if incomplete:
            fail(f"offboarded tenant has incomplete controls: {', '.join(incomplete)}")
        refs_current(offboarding.get("evidence_ids", []), evidence, "offboarding evidence")
        if not offboarding.get("evidence_ids"):
            fail("offboarded status requires current revocation/deletion/billing evidence")
        cleanup = test_map.get("offboarding_cleanup")
        if not cleanup or cleanup.get("status") != "pass":
            fail("offboarded status requires passing offboarding_cleanup test")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", nargs="?", default="templates/TENANT_OPERATIONS_RECORD.json")
    args = parser.parse_args()
    path = (ROOT / args.record).resolve()
    if path != ROOT and ROOT not in path.parents:
        fail("record path must stay inside repository")
    record = load(path)
    validate(record)
    print(f"tenant operations OK: {record['tenant_ref']} status={record['status']} evidence={len(record['evidence'])}")


if __name__ == "__main__":
    main()
