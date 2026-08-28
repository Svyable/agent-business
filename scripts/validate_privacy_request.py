#!/usr/bin/env python3
"""Validate Agent Business privacy-request records without third-party packages."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "agent-index.json"

STATUSES = {"received","identity_scope_review","mapped","executing","downstream_pending","verification","fulfilled","partially_fulfilled","denied_with_basis","escalated"}
TERMINAL = {"fulfilled","partially_fulfilled","denied_with_basis","escalated"}
EXECUTION = {"executing","downstream_pending","verification","fulfilled","partially_fulfilled"}
ERASURE_ACTIONS = {"delete","redact","tombstone","rebuild","key_destroy","downstream_request","expire"}
DERIVED_SURFACES = {"derived_summary","vector_index","cache","tool_output","analytics","training_pipeline"}
PROHIBITED_KEYS = {
    "password","secret","api_key","access_token","refresh_token","authorization","credential",
    "raw_prompt","private_prompt","private_customer_data","raw_subject_identifier","email","phone_number","government_id"
}


def fail(message: str) -> None:
    raise SystemExit(f"privacy-request validation failed: {message}")


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


def validate_refs(refs: object, known: dict[str, dict], label: str, current_only: bool = False) -> None:
    if not isinstance(refs, list) or any(not isinstance(ref, str) or not ref for ref in refs):
        fail(f"{label} must be a list of evidence ids")
    for ref in refs:
        if ref not in known:
            fail(f"{label} references unknown evidence: {ref}")
        if current_only and known[ref].get("status") != "current":
            fail(f"{label} must reference current evidence: {ref}")


def validate(record: dict) -> None:
    required = {"schema_version","request_id","status","updated_at","subject_ref","request_type","policy_basis","scope","systems","consent","authority","evidence","verification","downstream","exceptions","response","privacy"}
    missing = sorted(required - set(record))
    if missing:
        fail(f"missing required fields: {', '.join(missing)}")
    if record.get("schema_version") != "1.0.0":
        fail("schema_version must be 1.0.0")
    status = record.get("status")
    if status not in STATUSES:
        fail("status is invalid")
    parse_time(record.get("updated_at"), "updated_at")
    if not isinstance(record.get("request_id"), str) or not record.get("request_id"):
        fail("request_id must be a non-empty string")
    if not isinstance(record.get("subject_ref"), str) or not record.get("subject_ref"):
        fail("subject_ref must be a non-empty opaque reference")
    if record.get("request_type") not in {"access","correction","erasure","consent_withdrawal","restriction","portability"}:
        fail("request_type is invalid")
    scan(record)

    resources = {item.get("id") for item in load(INDEX).get("resources", []) if isinstance(item, dict)}
    for resource_id in record.get("repository_resources", []):
        if resource_id not in resources:
            fail(f"unknown repository resource: {resource_id}")

    evidence = evidence_map(record.get("evidence"))
    policy = record.get("policy_basis")
    scope = record.get("scope")
    consent = record.get("consent")
    authority = record.get("authority")
    verification = record.get("verification")
    response = record.get("response")
    privacy = record.get("privacy")
    if not all(isinstance(item, dict) for item in (policy, scope, consent, authority, verification, response, privacy)):
        fail("policy_basis/scope/consent/authority/verification/response/privacy must be objects")

    for field in ("contains_personal_data","contains_credentials","contains_private_prompts","contains_raw_subject_identifier"):
        if privacy.get(field) is not False:
            fail(f"privacy.{field} must be false")
    if privacy.get("public_disclosure_confirmed") is not True:
        fail("privacy.public_disclosure_confirmed must be true")

    deadline = policy.get("deadline_at")
    if deadline is not None:
        parse_time(deadline, "policy_basis.deadline_at")
        if not policy.get("deadline_source_ref"):
            fail("a supplied deadline requires deadline_source_ref; do not invent statutory deadlines")
    for suspicious in ("statutory_days","legal_deadline_days","gdpr_days","ccpa_days"):
        if suspicious in policy:
            fail(f"policy_basis.{suspicious} is not allowed; reference the applicable policy/legal determination")

    if status != "received" and not scope.get("identity_scope_verified"):
        fail(f"{status} requires verified identity/scope")
    if status in EXECUTION:
        if not authority.get("can_access_subject_data") or not authority.get("can_execute_privacy_action"):
            fail(f"{status} requires explicit data-access and privacy-action authority")
        validate_refs(authority.get("authority_evidence_ids", []), evidence, "authority.authority_evidence_ids", current_only=True)
        if not authority.get("authority_evidence_ids"):
            fail("execution authority requires current authority evidence")

    systems = record.get("systems")
    if not isinstance(systems, list):
        fail("systems must be a list")
    system_ids: set[str] = set()
    for system in systems:
        if not isinstance(system, dict):
            fail("systems entries must be objects")
        system_id = system.get("id")
        if not isinstance(system_id, str) or not system_id or system_id in system_ids:
            fail("systems require unique non-empty ids")
        system_ids.add(system_id)
        if system.get("surface") not in {"raw_conversation","structured_memory","derived_summary","vector_index","cache","tool_output","analytics","export","training_pipeline","subprocessor","backup_recovery","other"}:
            fail(f"system {system_id}: invalid surface")
        if system.get("action") not in {"none","map","delete","redact","tombstone","rebuild","key_destroy","correct","restrict","export","downstream_request","expire","escalate"}:
            fail(f"system {system_id}: invalid action")
        if system.get("status") not in {"unmapped","mapped","pending","executed","verified_not_present","corrected","restricted","exported","not_applicable","unverifiable","blocked"}:
            fail(f"system {system_id}: invalid status")
        validate_refs(system.get("evidence_ids", []), evidence, f"system {system_id}.evidence_ids")
        if system.get("status") in {"executed","verified_not_present","corrected","restricted","exported"} and not system.get("evidence_ids"):
            fail(f"system {system_id}: asserted action/result requires evidence")

    mapped = verification.get("mapped_surface_count")
    verified = verification.get("verified_surface_count")
    residue = verification.get("retrieval_residue_count")
    for label, value in (("mapped_surface_count", mapped),("verified_surface_count", verified),("retrieval_residue_count", residue)):
        if not isinstance(value, int) or value < 0:
            fail(f"verification.{label} must be a non-negative integer")
    if mapped != len(systems):
        fail("verification.mapped_surface_count must equal the systems inventory length")
    if verified > mapped:
        fail("verified_surface_count cannot exceed mapped_surface_count")
    if verification.get("state") not in {"not_started","partial","passed","failed","not_applicable"}:
        fail("verification.state is invalid")
    validate_refs(verification.get("evidence_ids", []), evidence, "verification.evidence_ids")

    downstream = record.get("downstream")
    if not isinstance(downstream, list):
        fail("downstream must be a list")
    for item in downstream:
        if not isinstance(item, dict) or not item.get("processor_ref"):
            fail("downstream entries require processor_ref")
        if item.get("status") not in {"not_sent","sent","acknowledged","not_applicable","unverifiable","rejected"}:
            fail("downstream status is invalid")
        validate_refs(item.get("evidence_ids", []), evidence, f"downstream {item.get('processor_ref')}.evidence_ids")
        if item.get("status") == "acknowledged" and not item.get("evidence_ids"):
            fail("downstream acknowledgement requires evidence")

    exceptions = record.get("exceptions")
    if not isinstance(exceptions, list):
        fail("exceptions must be a list")
    unresolved = []
    for item in exceptions:
        if not isinstance(item, dict) or not item.get("id"):
            fail("exceptions require ids")
        validate_refs(item.get("evidence_ids", []), evidence, f"exception {item.get('id')}.evidence_ids")
        if not item.get("resolved"):
            unresolved.append(item.get("id"))
        elif not item.get("decision_ref") or not item.get("evidence_ids"):
            fail(f"resolved exception {item.get('id')} requires decision_ref and evidence")

    if record.get("request_type") == "consent_withdrawal" and status in TERMINAL:
        if not consent.get("withdrawal_propagation_complete"):
            fail("terminal consent-withdrawal request requires propagation completion")
        if not consent.get("non_consent_processing_review_ref"):
            fail("consent withdrawal requires a separate review of non-consent processing bases")

    if record.get("request_type") in {"access","portability"} and status == "fulfilled":
        if not response.get("export_tenant_isolated") or not response.get("export_redaction_reviewed"):
            fail("fulfilled access/portability export requires tenant isolation and redaction review")

    if record.get("request_type") == "erasure" and status == "fulfilled":
        unresolved_downstream = [item.get("processor_ref") for item in downstream if item.get("required") and item.get("status") not in {"acknowledged","not_applicable"}]
        bad_systems = [item.get("id") for item in systems if item.get("status") not in {"verified_not_present","not_applicable"}]
        if bad_systems:
            fail("fulfilled erasure requires every mapped surface to be verified_not_present or not_applicable")
        if unresolved_downstream:
            fail("fulfilled erasure cannot have unresolved required downstream processors")
        if unresolved:
            fail("fulfilled erasure cannot have unresolved exceptions")
        if verification.get("state") != "passed" or verified != mapped:
            fail("fulfilled erasure requires passed verification of every mapped surface")
        if residue != 0:
            fail("fulfilled erasure requires zero retrieval residue in the declared test scope")
        if any(item.get("surface") in DERIVED_SURFACES for item in systems) and not verification.get("derived_memory_tested"):
            fail("fulfilled erasure with derived surfaces requires derived-memory resurfacing tests")
        if any(item.get("surface") == "backup_recovery" for item in systems) and not verification.get("restore_resurrection_tested"):
            fail("fulfilled erasure with recovery copies requires a restore-resurrection test")
        if verification.get("known_unverifiable_surfaces"):
            fail("fulfilled erasure cannot claim completion with known unverifiable surfaces")

    if record.get("request_type") == "erasure" and status in EXECUTION:
        for system in systems:
            if system.get("action") in ERASURE_ACTIONS and system.get("surface") == "backup_recovery" and system.get("restore_protection") == "not_assessed":
                fail("erasure affecting recovery copies requires restore-protection assessment")

    if status == "fulfilled":
        if not response.get("finalized"):
            fail("fulfilled request requires finalized response")
        validate_refs(response.get("final_evidence_ids", []), evidence, "response.final_evidence_ids", current_only=True)
        if not response.get("final_evidence_ids"):
            fail("fulfilled request requires current final-response evidence")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", nargs="?", default="templates/PRIVACY_REQUEST_RECORD.json")
    args = parser.parse_args()
    path = (ROOT / args.record).resolve()
    if path != ROOT and ROOT not in path.parents:
        fail("record path must stay inside repository")
    record = load(path)
    validate(record)
    print(f"privacy request OK: {record['request_id']} status={record['status']} systems={len(record['systems'])}")


if __name__ == "__main__":
    main()
