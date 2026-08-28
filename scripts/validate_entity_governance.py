#!/usr/bin/env python3
"""Validate Agent Business entity-governance evidence without third-party packages."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = {"schema_version", "record_id", "updated_at", "status", "entity", "ownership", "authority", "obligations", "evidence", "privacy", "review"}
STATUS = {"draft", "needs_review", "operational", "suspended", "dissolved"}
EVIDENCE_STATUS = {"current", "stale", "disputed", "superseded", "draft"}
PROHIBITED_KEYS = {
    "password", "secret", "api_key", "access_token", "refresh_token", "authorization",
    "ssn", "social_security_number", "passport_number", "driver_license_number",
    "bank_account_number", "routing_number", "private_key", "signature_image",
}
PLACEHOLDERS = ("replace with", "unknown until", "starter record", "draft-entity")


def fail(message: str) -> None:
    raise SystemExit(f"entity-governance validation failed: {message}")


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


def scan_sensitive(value: object, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in PROHIBITED_KEYS:
                fail(f"prohibited sensitive field: {path}.{key}")
            scan_sensitive(child, f"{path}.{key}")
    elif isinstance(value, list):
        for i, child in enumerate(value):
            scan_sensitive(child, f"{path}[{i}]")


def unique(items: object, label: str) -> dict[str, dict]:
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


def refs_exist(refs: object, evidence: dict[str, dict], label: str) -> list[str]:
    if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
        fail(f"{label} must be a list of evidence ids")
    unknown = sorted(set(refs) - set(evidence))
    if unknown:
        fail(f"{label} references unknown evidence: {', '.join(unknown)}")
    return refs


def require_current(refs: list[str], evidence: dict[str, dict], label: str) -> None:
    bad = [ref for ref in refs if evidence[ref].get("status") != "current"]
    if bad:
        fail(f"{label} references non-current evidence: {', '.join(bad)}")


def validate(record: dict) -> None:
    missing = sorted(REQUIRED - set(record))
    if missing:
        fail(f"missing required fields: {', '.join(missing)}")
    if record.get("schema_version") != "1.0.0":
        fail("schema_version must be 1.0.0")
    status = record.get("status")
    if status not in STATUS:
        fail("status is invalid")
    parse_time(record.get("updated_at"), "updated_at")
    scan_sensitive(record)

    evidence = unique(record.get("evidence"), "evidence")
    now = datetime.now(timezone.utc)
    for evidence_id, item in evidence.items():
        if item.get("status") not in EVIDENCE_STATUS:
            fail(f"evidence {evidence_id} has invalid status")
        observed = parse_time(item.get("observed_at"), f"evidence {evidence_id}.observed_at")
        effective = parse_time(item.get("effective_from"), f"evidence {evidence_id}.effective_from")
        if effective > now:
            fail(f"evidence {evidence_id} cannot be effective in the future")
        expires = item.get("expires_at")
        if expires is not None:
            expiry = parse_time(expires, f"evidence {evidence_id}.expires_at")
            if expiry <= now and item.get("status") == "current":
                fail(f"evidence {evidence_id} is expired but marked current")
        public_url = item.get("public_url")
        if public_url is not None:
            if not isinstance(public_url, str):
                fail(f"evidence {evidence_id}.public_url must be string or null")
            parsed = urlparse(public_url)
            if parsed.scheme != "https" or not parsed.netloc:
                fail(f"evidence {evidence_id}.public_url must be an absolute https URL")
        if item.get("sensitivity") == "private_reference_only" and public_url is not None:
            fail(f"private evidence {evidence_id} must not expose public_url")
        if item.get("sensitivity") == "private_reference_only" and not item.get("private_reference"):
            fail(f"private evidence {evidence_id} needs a privacy-safe private_reference")
        if observed > now:
            fail(f"evidence {evidence_id}.observed_at cannot be in the future")

    entity = record.get("entity")
    ownership = record.get("ownership")
    authority = record.get("authority")
    review = record.get("review")
    privacy = record.get("privacy")
    if not all(isinstance(x, dict) for x in (entity, ownership, authority, review, privacy)):
        fail("entity, ownership, authority, review, and privacy must be objects")

    formation_refs = refs_exist(entity.get("formation_evidence_ids"), evidence, "entity.formation_evidence_ids")
    governing_refs = refs_exist(entity.get("governing_document_evidence_ids", []), evidence, "entity.governing_document_evidence_ids")
    cap_refs = refs_exist(ownership.get("cap_table_evidence_ids"), evidence, "ownership.cap_table_evidence_ids")
    bo_refs = refs_exist(ownership.get("beneficial_ownership_evidence_ids"), evidence, "ownership.beneficial_ownership_evidence_ids")
    signatory_refs = refs_exist(authority.get("signatory_evidence_ids"), evidence, "authority.signatory_evidence_ids")
    delegation_refs = refs_exist(authority.get("delegation_evidence_ids", []), evidence, "authority.delegation_evidence_ids")

    obligations = unique(record.get("obligations"), "obligation")
    for obligation_id, item in obligations.items():
        refs = refs_exist(item.get("evidence_ids"), evidence, f"obligation {obligation_id}.evidence_ids")
        due_at = item.get("due_at")
        if due_at is not None:
            due = parse_time(due_at, f"obligation {obligation_id}.due_at")
            if item.get("status") == "not_due" and due <= now:
                fail(f"obligation {obligation_id} is past due but marked not_due")
        if item.get("status") == "filed":
            if not refs:
                fail(f"filed obligation {obligation_id} requires evidence")
            require_current(refs, evidence, f"filed obligation {obligation_id}")

    actions = unique(record.get("corporate_actions", []), "corporate action")
    for action_id, item in actions.items():
        refs = refs_exist(item.get("approval_evidence_ids"), evidence, f"corporate action {action_id}.approval_evidence_ids")
        if item.get("status") in {"approved", "effective"}:
            if not refs:
                fail(f"{item.get('status')} corporate action {action_id} requires approval evidence")
            require_current(refs, evidence, f"corporate action {action_id}")
        effective_at = item.get("effective_at")
        if item.get("status") == "effective" and effective_at is None:
            fail(f"effective corporate action {action_id} requires effective_at")
        if effective_at is not None:
            parse_time(effective_at, f"corporate action {action_id}.effective_at")

    for field in ("contains_raw_government_id", "contains_signature", "contains_bank_credentials", "contains_private_beneficial_owner_documents", "contains_secrets"):
        if privacy.get(field) is not False:
            fail(f"privacy.{field} must be false")
    if authority.get("material_actions_require_approval") is not True:
        fail("authority.material_actions_require_approval must be true")

    if status == "operational":
        marker_text = json.dumps(record, sort_keys=True).lower()
        marker = next((m for m in PLACEHOLDERS if m in marker_text), None)
        if marker:
            fail(f"operational record contains placeholder text: {marker!r}")
        if not isinstance(entity.get("formation_effective_at"), str):
            fail("operational record requires entity.formation_effective_at")
        parse_time(entity["formation_effective_at"], "entity.formation_effective_at")
        if str(entity.get("formation_jurisdiction", "")).lower() == "unknown":
            fail("operational record cannot have unknown formation jurisdiction")
        if not formation_refs or not governing_refs:
            fail("operational record requires current formation and governing-document evidence")
        require_current(formation_refs, evidence, "formation evidence")
        require_current(governing_refs, evidence, "governing-document evidence")
        if entity.get("good_standing") == "unknown":
            fail("operational record cannot have unknown good-standing status")
        if ownership.get("cap_table_status") == "unknown":
            fail("operational record cannot have unknown cap-table status")
        if ownership.get("cap_table_status") == "current":
            if not cap_refs:
                fail("current cap table requires evidence")
            require_current(cap_refs, evidence, "cap-table evidence")
        if ownership.get("beneficial_ownership_status") in {"unknown", "needs_review"}:
            fail("operational record requires resolved beneficial-ownership status")
        if ownership.get("beneficial_ownership_status") == "current":
            if not bo_refs:
                fail("current beneficial-ownership determination requires evidence")
            require_current(bo_refs, evidence, "beneficial-ownership evidence")
        if authority.get("banking_authority_status") in {"unknown", "needs_review"}:
            fail("operational record requires resolved banking-authority status")
        if authority.get("banking_authority_status") == "current":
            if not signatory_refs:
                fail("current banking authority requires signatory evidence")
            require_current(signatory_refs, evidence, "signatory evidence")
        require_current(delegation_refs, evidence, "delegation evidence")
        unresolved = [oid for oid, item in obligations.items() if item.get("status") in {"unknown", "due", "needs_review"}]
        if unresolved:
            fail(f"operational record has unresolved obligations: {', '.join(unresolved)}")
        if review.get("human_review_required") is True and review.get("reviewed_at") is None:
            fail("operational record requiring human review needs review.reviewed_at")
        if review.get("reviewed_at") is not None:
            parse_time(review.get("reviewed_at"), "review.reviewed_at")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", nargs="?", default="templates/ENTITY_GOVERNANCE_RECORD.json")
    args = parser.parse_args()
    path = (ROOT / args.record).resolve()
    if path != ROOT and ROOT not in path.parents:
        fail("record path must stay inside the repository")
    record = load(path)
    validate(record)
    print(f"entity governance OK: {record['record_id']} status={record['status']} evidence={len(record['evidence'])} obligations={len(record['obligations'])}")


if __name__ == "__main__":
    main()
