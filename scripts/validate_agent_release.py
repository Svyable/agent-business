#!/usr/bin/env python3
"""Validate production agent release/change records without third-party packages."""
from __future__ import annotations
import argparse, json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "agent-index.json"
EXPOSED = {"canary", "rolling_out", "stable"}
ADVANCED = {"evaluated", "approved", "canary", "rolling_out", "stable", "rolled_back", "deprecated", "retired"}
PROHIBITED_KEYS = {
    "password", "secret", "api_key", "access_token", "refresh_token", "authorization",
    "credential", "credentials", "raw_customer_data", "private_prompt", "raw_prompt", "prompt_text"
}
BEHAVIORAL_COMPONENTS = {"models", "tools", "prompts", "policies"}


def fail(message: str) -> None:
    raise SystemExit(f"agent-release validation failed: {message}")


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
    out: dict[str, dict] = {}
    for item in items:
        if not isinstance(item, dict):
            fail("evidence entries must be objects")
        eid = item.get("id")
        if not isinstance(eid, str) or not eid:
            fail("evidence entries need non-empty ids")
        if eid in out:
            fail(f"duplicate evidence id: {eid}")
        parse_time(item.get("observed_at"), f"evidence {eid}.observed_at")
        url = item.get("public_url")
        if url is not None:
            parsed = urlparse(url)
            if parsed.scheme != "https" or not parsed.netloc:
                fail(f"evidence {eid}.public_url must be absolute https")
        out[eid] = item
    return out


def current_refs(refs: object, evidence: dict[str, dict], label: str, required: bool = False) -> None:
    if not isinstance(refs, list):
        fail(f"{label} must be a list")
    if required and not refs:
        fail(f"{label} requires current evidence")
    for ref in refs:
        if ref not in evidence:
            fail(f"{label} references unknown evidence: {ref}")
        if evidence[ref].get("status") != "current":
            fail(f"{label} must reference only current evidence")


def validate(record: dict) -> None:
    required = {
        "schema_version", "release_id", "revision_id", "parent_revision_id", "status", "updated_at",
        "change", "baseline", "dependencies", "authority", "evaluation", "rollout", "customer_impact",
        "compatibility", "rollback", "deprecation", "observability", "evidence", "privacy"
    }
    missing = sorted(required - set(record))
    if missing:
        fail(f"missing required fields: {', '.join(missing)}")
    if record.get("schema_version") != "1.0.0":
        fail("schema_version must be 1.0.0")
    status = record.get("status")
    allowed = {"proposed", "built", "evaluated", "approved", "canary", "rolling_out", "stable", "rolled_back", "deprecated", "retired"}
    if status not in allowed:
        fail("status is invalid")
    parse_time(record.get("updated_at"), "updated_at")
    scan(record)

    if INDEX.exists():
        resources = {x.get("id") for x in load(INDEX).get("resources", []) if isinstance(x, dict)}
        for rid in record.get("repository_resources", []):
            if rid not in resources:
                fail(f"unknown repository resource: {rid}")

    evidence = evidence_map(record.get("evidence"))
    privacy = record.get("privacy", {})
    if not isinstance(privacy, dict):
        fail("privacy must be an object")
    for key in ("contains_credentials", "contains_private_customer_data", "contains_private_prompts"):
        if privacy.get(key) is not False:
            fail(f"privacy.{key} must be false")
    if privacy.get("public_disclosure_confirmed") is not True:
        fail("privacy.public_disclosure_confirmed must be true")

    change = record.get("change", {})
    baseline = record.get("baseline", {})
    authority = record.get("authority", {})
    evaluation = record.get("evaluation", {})
    rollout = record.get("rollout", {})
    impact = record.get("customer_impact", {})
    compatibility = record.get("compatibility", {})
    rollback = record.get("rollback", {})
    deprecation = record.get("deprecation", {})
    observability = record.get("observability", {})
    for obj, label in ((change,"change"),(baseline,"baseline"),(authority,"authority"),(evaluation,"evaluation"),(rollout,"rollout"),(impact,"customer_impact"),(compatibility,"compatibility"),(rollback,"rollback"),(deprecation,"deprecation"),(observability,"observability")):
        if not isinstance(obj, dict):
            fail(f"{label} must be an object")

    revision = record.get("revision_id")
    parent = record.get("parent_revision_id")
    if not isinstance(revision, str) or not revision:
        fail("revision_id must be non-empty")
    if parent == revision:
        fail("revision_id cannot equal parent_revision_id")
    classifications = change.get("classifications")
    if not isinstance(classifications, list) or not classifications:
        fail("change.classifications must be a non-empty list")
    allowed_classes = {"patch", "behavioral", "commercial", "security", "data", "authority", "breaking"}
    if any(x not in allowed_classes for x in classifications):
        fail("change.classifications contains an invalid value")
    affected = change.get("affected_components")
    if not isinstance(affected, dict):
        fail("change.affected_components must be an object")
    behavior_changed = any(bool(affected.get(k)) for k in BEHAVIORAL_COMPONENTS)
    if behavior_changed and "behavioral" not in classifications:
        fail("model/tool/prompt/policy changes must be classified behavioral")

    dependencies = record.get("dependencies")
    if not isinstance(dependencies, list):
        fail("dependencies must be a list")
    for dep in dependencies:
        if not isinstance(dep, dict):
            fail("dependency entries must be objects")
        changed = dep.get("previous_version") != dep.get("new_version")
        if changed and "behavioral" not in classifications:
            fail("model/provider/tool dependency version changes must be classified behavioral")
        if status in ADVANCED and dep.get("compatibility_checked") is not True:
            fail("advanced release status requires dependency compatibility checks")
        current_refs(dep.get("evidence_ids", []), evidence, f"dependency {dep.get('id','?')} evidence", required=status in ADVANCED)

    if status in ADVANCED:
        if not baseline.get("production_revision_id") or baseline.get("production_revision_id") == revision:
            fail("advanced release status requires a distinct production baseline revision")
        current_refs(baseline.get("evidence_ids", []), evidence, "baseline.evidence_ids", required=True)
        for key in ("baseline_compared", "regression_suite_passed", "safety_policy_passed", "tool_use_checked", "latency_delta_checked", "cost_delta_checked", "human_review_delta_checked"):
            if evaluation.get(key) is not True:
                fail(f"advanced release status requires evaluation.{key}=true")
        if evaluation.get("critical_regressions"):
            fail("advanced release status cannot have unresolved critical regressions")
        current_refs(evaluation.get("evidence_ids", []), evidence, "evaluation.evidence_ids", required=True)

    if authority.get("widened") is True:
        if "authority" not in classifications:
            fail("authority widening must be classified authority")
        if authority.get("reapproved") is not True:
            fail("authority widening requires explicit reapproval")
        current_refs(authority.get("evidence_ids", []), evidence, "authority.evidence_ids", required=True)
    elif authority.get("reapproved") is True:
        current_refs(authority.get("evidence_ids", []), evidence, "authority.evidence_ids", required=True)

    if "breaking" in classifications or compatibility.get("breaking_change") is True:
        if compatibility.get("breaking_change") is not True or "breaking" not in classifications:
            fail("breaking classification and compatibility.breaking_change must agree")
        if compatibility.get("migration_path_defined") is not True:
            fail("breaking changes require a migration path")
        current_refs(compatibility.get("evidence_ids", []), evidence, "compatibility.evidence_ids", required=True)

    if status in EXPOSED:
        for key in ("machine_contracts_checked", "stored_state_checked", "integrations_checked", "downstream_consumers_checked"):
            if compatibility.get(key) is not True:
                fail(f"production exposure requires compatibility.{key}=true")
        if rollback.get("defined") is not True or rollback.get("tested") is not True or rollback.get("owner_defined") is not True:
            fail("production exposure requires defined, tested rollback with an owner")
        current_refs(rollback.get("evidence_ids", []), evidence, "rollback.evidence_ids", required=True)
        if rollback.get("irreversible_changes") and rollback.get("state_migration_reversible") is True:
            fail("irreversible changes cannot be marked state-migration reversible")
        if rollout.get("canary_required") is not False and status in {"canary", "rolling_out"}:
            canary = rollout.get("canary_percent")
            if not isinstance(canary, int) or not 0 < canary < 100:
                fail("canary/rolling release requires canary_percent between 1 and 99")
        current = rollout.get("current_percent")
        if not isinstance(current, int) or not 0 < current <= 100:
            fail("production exposure requires current_percent between 1 and 100")
        if not rollout.get("promotion_criteria") or not rollout.get("stop_conditions") or not rollout.get("rollback_revision_id"):
            fail("production exposure requires promotion criteria, stop conditions, and rollback revision")
        if rollout.get("rollback_revision_id") == revision:
            fail("rollback revision must differ from candidate revision")
        current_refs(rollout.get("production_metrics_evidence_ids", []), evidence, "rollout.production_metrics_evidence_ids", required=True)
        if status == "canary" and current > rollout.get("canary_percent", 0):
            fail("canary status cannot exceed configured canary percentage")
        if status == "stable" and current != 100:
            fail("stable status requires 100 percent production traffic")
        for key in ("error_rate", "quality_safety", "latency", "cost_per_success", "escalation_rate", "customer_incidents"):
            if observability.get(key) is not True:
                fail(f"production exposure requires observability.{key}=true")

    material_dims = set(impact.get("dimensions", [])) - {"none"}
    material = impact.get("material") is True or bool(material_dims) or any(x in classifications for x in ("commercial", "breaking", "data"))
    if material:
        if impact.get("material") is not True:
            fail("material customer impact must set customer_impact.material=true")
        if impact.get("communication_required") is not True:
            fail("material customer impact requires customer communication")
        if status in EXPOSED | {"deprecated", "retired"}:
            if impact.get("communication_complete") is not True:
                fail("customer-impacting production/deprecation state requires completed communication")
            current_refs(impact.get("evidence_ids", []), evidence, "customer_impact.evidence_ids", required=True)

    if status in {"deprecated", "retired"}:
        for key in ("notice_required", "notice_complete", "support_window_defined", "migration_path_defined", "sunset_criteria_defined"):
            if deprecation.get(key) is not True:
                fail(f"{status} status requires deprecation.{key}=true")
        current_refs(deprecation.get("evidence_ids", []), evidence, "deprecation.evidence_ids", required=True)
    if status == "retired" and deprecation.get("migration_complete") is not True:
        fail("retired status requires migration_complete=true")

    if status == "rolled_back":
        if rollback.get("defined") is not True or not rollout.get("rollback_revision_id"):
            fail("rolled_back status requires an explicit rollback target")
        current_refs(rollback.get("evidence_ids", []), evidence, "rollback.evidence_ids", required=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", nargs="?", default="templates/AGENT_RELEASE_RECORD.json")
    args = parser.parse_args()
    path = (ROOT / args.record).resolve()
    if path != ROOT and ROOT not in path.parents:
        fail("record path must stay inside repository")
    record = load(path)
    validate(record)
    print(f"agent release OK: {record['release_id']} revision={record['revision_id']} status={record['status']} evidence={len(record['evidence'])}")


if __name__ == "__main__":
    main()
