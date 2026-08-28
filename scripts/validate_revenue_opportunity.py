#!/usr/bin/env python3
"""Validate Agent Business revenue opportunity records without third-party packages."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PROHIBITED_KEYS = {
    "password", "secret", "api_key", "access_token", "refresh_token",
    "authorization", "raw_email", "email_address", "phone_number", "raw_prompt"
}
ADVANCED = {"qualified_opportunity", "evaluation", "commercial_review", "commit", "won"}
CLOSED = {"won", "lost"}
BUYER_EVIDENCE_TYPES = {"buyer_statement", "meeting_note", "contract", "quote", "payment"}


def fail(message: str) -> None:
    raise SystemExit(f"revenue-opportunity validation failed: {message}")


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


def parse_date(value: object, label: str) -> date:
    if not isinstance(value, str):
        fail(f"{label} must be an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError:
        fail(f"{label} must be an ISO date")


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


def evidence_map(items: object) -> dict[str, dict]:
    if not isinstance(items, list):
        fail("evidence must be a list")
    result: dict[str, dict] = {}
    for item in items:
        if not isinstance(item, dict):
            fail("evidence entries must be objects")
        evidence_id = item.get("id")
        if not isinstance(evidence_id, str) or not evidence_id:
            fail("evidence entries require ids")
        if evidence_id in result:
            fail(f"duplicate evidence id: {evidence_id}")
        if item.get("status") not in {"current", "stale", "disputed", "draft"}:
            fail(f"evidence {evidence_id} has invalid status")
        parse_time(item.get("observed_at"), f"evidence {evidence_id}.observed_at")
        url = item.get("public_url")
        if url is not None:
            parsed = urlparse(url) if isinstance(url, str) else None
            if parsed is None or parsed.scheme != "https" or not parsed.netloc:
                fail(f"evidence {evidence_id}.public_url must be an absolute https URL")
        result[evidence_id] = item
    return result


def require_current(refs: object, evidence: dict[str, dict], label: str, *, buyer_only: bool = False) -> None:
    if not isinstance(refs, list) or not refs:
        fail(f"{label} requires evidence")
    for ref in refs:
        if ref not in evidence:
            fail(f"{label} references unknown evidence: {ref!r}")
        item = evidence[ref]
        if item.get("status") != "current":
            fail(f"{label} references non-current evidence: {ref}")
    if buyer_only and not any(evidence[ref].get("type") in BUYER_EVIDENCE_TYPES for ref in refs):
        fail(f"{label} requires at least one buyer/commercial evidence item, not seller inference alone")


def validate(record: dict) -> None:
    required = {
        "schema_version", "opportunity_id", "updated_at", "record_status", "stage",
        "account", "stakeholders", "qualification", "forecast", "next_action",
        "commercial", "authority", "evidence", "privacy"
    }
    missing = sorted(required - set(record))
    if missing:
        fail(f"missing required fields: {', '.join(missing)}")
    if record.get("schema_version") != "1.0.0":
        fail("schema_version must be 1.0.0")
    if record.get("record_status") not in {"draft", "active", "closed"}:
        fail("record_status is invalid")
    stages = {"target_account", "lead", "qualified_opportunity", "evaluation", "commercial_review", "commit", "won", "lost", "nurture"}
    stage = record.get("stage")
    if stage not in stages:
        fail("stage is invalid")
    updated = parse_time(record.get("updated_at"), "updated_at")
    scan_sensitive(record)
    evidence = evidence_map(record.get("evidence"))

    account = record.get("account")
    if not isinstance(account, dict) or not isinstance(account.get("duplicate_key"), str) or not account["duplicate_key"].strip():
        fail("account.duplicate_key is required for duplicate detection")

    stakeholders = record.get("stakeholders")
    if not isinstance(stakeholders, list):
        fail("stakeholders must be a list")
    observed_roles = set()
    for stakeholder in stakeholders:
        if not isinstance(stakeholder, dict):
            fail("stakeholders entries must be objects")
        state = stakeholder.get("identity_state")
        refs = stakeholder.get("evidence_ids")
        if state == "observed":
            require_current(refs, evidence, f"stakeholder {stakeholder.get('role')}", buyer_only=True)
            observed_roles.add(stakeholder.get("role"))
        elif state == "inferred" and refs:
            require_current(refs, evidence, f"inferred stakeholder {stakeholder.get('role')}")
        elif state not in {"unknown", "inferred", "observed"}:
            fail("stakeholder identity_state is invalid")

    qualification = record.get("qualification")
    if not isinstance(qualification, dict):
        fail("qualification must be an object")
    stage_refs = qualification.get("stage_evidence_ids")
    if stage in ADVANCED:
        if qualification.get("problem") != "observed":
            fail(f"stage {stage} requires observed problem evidence")
        require_current(stage_refs, evidence, f"stage {stage}", buyer_only=True)
    if stage in {"commercial_review", "commit", "won"} and "economic_buyer" not in observed_roles:
        fail(f"stage {stage} requires an observed economic_buyer")
    if stage in {"evaluation", "commercial_review", "commit", "won"} and qualification.get("decision_process") == "unknown":
        fail(f"stage {stage} requires a known or observed decision process")

    forecast = record.get("forecast")
    if not isinstance(forecast, dict):
        fail("forecast must be an object")
    probability = forecast.get("probability_bps")
    if not isinstance(probability, int) or not 0 <= probability <= 10000:
        fail("forecast.probability_bps must be 0..10000")
    category = forecast.get("category")
    if category == "commit" or stage == "commit":
        require_current(forecast.get("evidence_ids"), evidence, "commit forecast", buyer_only=True)
        if probability < 5000:
            fail("commit forecast cannot use probability below 5000 bps")
    if stage == "won":
        if category != "closed" or probability != 10000:
            fail("won opportunities require closed forecast at 10000 bps")
        require_current(forecast.get("evidence_ids"), evidence, "won forecast", buyer_only=True)
    if stage == "lost" and category != "closed":
        fail("lost opportunities require closed forecast category")
    close_date = forecast.get("close_date")
    if stage in {"commercial_review", "commit"} and close_date is None:
        fail(f"stage {stage} requires a close_date")
    if close_date is not None:
        parse_date(close_date, "forecast.close_date")

    next_action = record.get("next_action")
    if not isinstance(next_action, dict):
        fail("next_action must be an object")
    if stage not in CLOSED and stage != "nurture" and next_action.get("type") == "none":
        fail("open opportunities require a next action")
    due_at = next_action.get("due_at")
    if due_at is not None:
        parse_time(due_at, "next_action.due_at")

    commercial = record.get("commercial")
    if not isinstance(commercial, dict):
        fail("commercial must be an object")
    quote_status = commercial.get("quote_status")
    if stage in {"commercial_review", "commit", "won"} and not commercial.get("pricing_package_id"):
        fail(f"stage {stage} requires pricing_package_id")
    if stage in {"commit", "won"} and quote_status not in {"sent", "accepted"}:
        fail(f"stage {stage} requires a sent or accepted quote")
    if stage == "won":
        if quote_status != "accepted":
            fail("won opportunity requires accepted quote")
        if not commercial.get("accepted_scope") or not commercial.get("success_criteria"):
            fail("won opportunity requires accepted scope and success criteria for handoff")

    authority = record.get("authority")
    if not isinstance(authority, dict):
        fail("authority must be an object")
    permissions = [
        "can_write_crm", "can_contact", "can_change_stage", "can_send_quote",
        "can_make_pricing_claims", "can_commit_forecast", "can_mark_won_lost"
    ]
    granted = any(authority.get(field) is True for field in permissions)
    if granted:
        if not isinstance(authority.get("source"), str) or not authority["source"].strip():
            fail("granted authority requires provenance source")
        reviewed = parse_time(authority.get("reviewed_at"), "authority.reviewed_at")
        if reviewed > updated:
            fail("authority.reviewed_at cannot be after updated_at")
    if next_action.get("requires_external_contact") is True and authority.get("can_contact") is not True:
        fail("external-contact next action requires can_contact authority")
    if next_action.get("type") == "quote" and authority.get("can_send_quote") is not True:
        fail("quote next action requires can_send_quote authority")
    if category == "commit" and record.get("record_status") == "active" and authority.get("can_commit_forecast") is not True:
        fail("active commit forecast requires can_commit_forecast authority")
    if stage in CLOSED and record.get("record_status") == "closed" and authority.get("can_mark_won_lost") is not True:
        fail("closing an opportunity requires can_mark_won_lost authority")

    privacy = record.get("privacy")
    if not isinstance(privacy, dict):
        fail("privacy must be an object")
    for field in ("contains_secrets", "contains_private_contact_data", "contains_raw_customer_content"):
        if privacy.get(field) is not False:
            fail(f"privacy.{field} must be false")
    if privacy.get("public_example_safe") is not True:
        fail("public repository records require public_example_safe=true")

    if record.get("record_status") == "active" and stage in ADVANCED and not evidence:
        fail("active advanced opportunities require evidence")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", nargs="?", default="templates/REVENUE_OPPORTUNITY_RECORD.json")
    args = parser.parse_args()
    path = (ROOT / args.record).resolve()
    if path != ROOT and ROOT not in path.parents:
        fail("record path must stay inside repository")
    record = load(path)
    validate(record)
    print(
        f"revenue opportunity OK: {record['opportunity_id']} stage={record['stage']} "
        f"status={record['record_status']} evidence={len(record['evidence'])}"
    )


if __name__ == "__main__":
    main()
