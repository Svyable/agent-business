#!/usr/bin/env python3
"""Validate enterprise vendor-readiness records without third-party packages."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_CATEGORIES = {
    "security",
    "privacy",
    "data",
    "identity_authority",
    "observability",
    "incident_response",
    "reliability",
    "bcp_dr",
    "ai_governance",
}
PROHIBITED_KEYS = {
    "password",
    "secret",
    "api_key",
    "access_token",
    "refresh_token",
    "authorization",
    "private_key",
    "raw_prompt",
    "prompt_content",
    "customer_questionnaire_raw",
    "penetration_test_report_raw",
    "security_report_raw",
}


def fail(message: str) -> None:
    raise SystemExit(f"vendor-readiness validation failed: {message}")


def load_json(path: Path) -> dict:
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


def scan_sensitive(value: object, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in PROHIBITED_KEYS:
                fail(f"prohibited sensitive field: {path}.{key}")
            scan_sensitive(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_sensitive(child, f"{path}[{index}]")


def unique_ids(items: object, label: str) -> dict[str, dict]:
    if not isinstance(items, list):
        fail(f"{label} must be a list")
    result: dict[str, dict] = {}
    for item in items:
        if not isinstance(item, dict):
            fail(f"{label} entries must be objects")
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            fail(f"{label} entries need non-empty ids")
        if item_id in result:
            fail(f"duplicate {label} id: {item_id}")
        result[item_id] = item
    return result


def require_refs(refs: object, evidence: dict[str, dict], label: str, *, current: bool = False) -> None:
    if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
        fail(f"{label} evidence_ids must be a list of ids")
    unknown = sorted(set(refs) - set(evidence))
    if unknown:
        fail(f"{label} references unknown evidence: {', '.join(unknown)}")
    if current:
        if not refs:
            fail(f"{label} requires evidence")
        stale = [ref for ref in refs if evidence[ref].get("status") != "current"]
        if stale:
            fail(f"{label} references non-current evidence: {', '.join(stale)}")


def validate_public_url(value: object, label: str) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        fail(f"{label} must be a string or null")
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        fail(f"{label} must use an absolute https URL")


def validate(record: dict) -> None:
    if record.get("schema_version") != "1.0.0":
        fail("schema_version must be 1.0.0")
    if record.get("readiness_status") not in {"draft", "needs_review", "buyer_ready", "retired"}:
        fail("readiness_status is invalid")
    parse_time(record.get("updated_at"), "updated_at")
    scan_sensitive(record)

    offering = record.get("offering")
    if not isinstance(offering, dict):
        fail("offering must be an object")
    if offering.get("production_authority_granted") is not False:
        fail("vendor readiness never grants production authority")

    privacy = record.get("privacy")
    if not isinstance(privacy, dict) or privacy.get("public_safe") is not True:
        fail("privacy.public_safe must be true")
    for field in (
        "contains_secrets",
        "contains_credentials",
        "contains_private_customer_questionnaire",
        "contains_restricted_security_report",
        "contains_private_architecture",
    ):
        if privacy.get(field) is not False:
            fail(f"privacy.{field} must be false")

    evidence = unique_ids(record.get("evidence"), "evidence")
    now = datetime.now(timezone.utc)
    for evidence_id, item in evidence.items():
        observed = parse_time(item.get("observed_at"), f"evidence {evidence_id}.observed_at")
        if observed > now:
            fail(f"evidence {evidence_id} cannot be observed in the future")
        expires_raw = item.get("expires_at")
        if expires_raw is not None:
            expires = parse_time(expires_raw, f"evidence {evidence_id}.expires_at")
            if expires < observed:
                fail(f"evidence {evidence_id}.expires_at cannot precede observed_at")
            if expires <= now and item.get("status") == "current":
                fail(f"evidence {evidence_id} is expired but marked current")
        validate_public_url(item.get("public_url"), f"evidence {evidence_id}.public_url")

    controls = unique_ids(record.get("controls"), "control")
    if not controls:
        fail("controls must contain at least one item")
    for control_id, item in controls.items():
        status = item.get("status")
        if status not in {"verified", "self_attested", "not_applicable", "missing", "expired"}:
            fail(f"control {control_id} has invalid status")
        require_refs(item.get("evidence_ids"), evidence, f"control {control_id}", current=status in {"verified", "self_attested"})
        if status == "verified":
            refs = item.get("evidence_ids", [])
            if all(evidence[ref].get("type") in {"self_attestation", "internal_reference"} for ref in refs):
                fail(f"verified control {control_id} requires evidence stronger than self-attestation/internal reference")

    for cert in record.get("certifications", []):
        if not isinstance(cert, dict):
            fail("certifications entries must be objects")
        held = cert.get("status") == "held"
        require_refs(cert.get("evidence_ids"), evidence, f"certification {cert.get('name')!r}", current=held)
        if held:
            refs = cert.get("evidence_ids", [])
            if all(evidence[ref].get("type") not in {"third_party_audit", "public_artifact"} for ref in refs):
                fail(f"held certification {cert.get('name')!r} requires third-party/public evidence")

    subprocessors = record.get("subprocessors")
    if not isinstance(subprocessors, list):
        fail("subprocessors must be a list")
    for index, item in enumerate(subprocessors):
        if not isinstance(item, dict):
            fail("subprocessor entries must be objects")
        status = item.get("status")
        require_refs(item.get("evidence_ids"), evidence, f"subprocessor[{index}]", current=status == "current")
        if status == "current" and not item.get("processing_regions"):
            fail(f"subprocessor[{index}] current entry needs processing_regions")

    data = record.get("data_handling")
    if not isinstance(data, dict):
        fail("data_handling must be an object")
    if record.get("readiness_status") == "buyer_ready":
        if data.get("customer_data_used_for_training") == "unknown":
            fail("buyer_ready record cannot leave customer-data training use unknown")
        if "unknown" in str(data.get("residency_claim", "")).lower():
            fail("buyer_ready record cannot make an unknown residency claim")
        require_refs(data.get("evidence_ids"), evidence, "data_handling", current=True)

    governance = record.get("agent_governance")
    if not isinstance(governance, dict):
        fail("agent_governance must be an object")
    if record.get("readiness_status") == "buyer_ready":
        require_refs(governance.get("evidence_ids"), evidence, "agent_governance", current=True)

    answers = record.get("questionnaire_answers")
    if not isinstance(answers, list):
        fail("questionnaire_answers must be a list")
    seen_answers: set[str] = set()
    for answer in answers:
        if not isinstance(answer, dict):
            fail("questionnaire answers must be objects")
        answer_id = answer.get("id")
        if not isinstance(answer_id, str) or not answer_id or answer_id in seen_answers:
            fail("questionnaire answer ids must be unique and non-empty")
        seen_answers.add(answer_id)
        require_refs(answer.get("evidence_ids"), evidence, f"questionnaire answer {answer_id}", current=True)
        if answer.get("answer_type") == "customer_specific" and answer.get("owner_reviewed") is not True:
            fail(f"customer-specific questionnaire answer {answer_id} requires owner review")

    gate = record.get("pilot_to_production")
    if not isinstance(gate, dict):
        fail("pilot_to_production must be an object")
    if gate.get("production_authority_approved") and not (
        gate.get("security_review_complete") and gate.get("legal_commercial_review_complete")
    ):
        fail("production authority approval requires security and legal/commercial review")
    if gate.get("production_data_approved") and not gate.get("security_review_complete"):
        fail("production data approval requires completed security review")

    if record.get("readiness_status") == "buyer_ready":
        categories = {item.get("category") for item in controls.values()}
        missing_categories = sorted(REQUIRED_CATEGORIES - categories)
        if missing_categories:
            fail(f"buyer_ready record missing required control categories: {', '.join(missing_categories)}")
        blockers = [cid for cid, item in controls.items() if item.get("category") in REQUIRED_CATEGORIES and item.get("status") in {"missing", "expired"}]
        if blockers:
            fail(f"buyer_ready record has unresolved required controls: {', '.join(blockers)}")


def ensure_repo_path(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    if path != ROOT and ROOT not in path.parents:
        fail("record path must stay inside repository")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", nargs="?", default="templates/VENDOR_READINESS_RECORD.json")
    args = parser.parse_args()
    path = ensure_repo_path(args.record)
    record = load_json(path)
    validate(record)
    print(
        "vendor readiness OK: "
        f"{record['record_id']} status={record['readiness_status']} "
        f"controls={len(record['controls'])} evidence={len(record['evidence'])}"
    )


if __name__ == "__main__":
    main()
