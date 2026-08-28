#!/usr/bin/env python3
"""Validate Agent Business fiscal transaction evidence without third-party packages."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPERATIONAL_STATES = {"ready_to_invoice", "issued", "corrected"}
PROHIBITED_KEYS = {
    "password",
    "secret",
    "client_secret",
    "api_key",
    "access_token",
    "refresh_token",
    "authorization",
    "card_number",
    "cvv",
    "payment_credential",
    "private_prompt",
    "prompt_content",
}


def fail(message: str) -> None:
    raise SystemExit(f"fiscal-evidence validation failed: {message}")


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


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot parse {path}: {exc}")
    if not isinstance(value, dict):
        fail("record must be a JSON object")
    return value


def safe_path(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    if path != ROOT and ROOT not in path.parents:
        fail("record path must stay inside the repository")
    return path


def scan_prohibited(value: object, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in PROHIBITED_KEYS:
                fail(f"prohibited sensitive field: {path}.{key}")
            scan_prohibited(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_prohibited(child, f"{path}[{index}]")


def required_object(record: dict, key: str) -> dict:
    value = record.get(key)
    if not isinstance(value, dict):
        fail(f"{key} must be an object")
    return value


def evidence_map(record: dict) -> dict[str, dict]:
    items = record.get("evidence")
    if not isinstance(items, list):
        fail("evidence must be a list")
    result: dict[str, dict] = {}
    for item in items:
        if not isinstance(item, dict):
            fail("evidence entries must be objects")
        evidence_id = item.get("id")
        if not isinstance(evidence_id, str) or not evidence_id:
            fail("evidence entries require non-empty ids")
        if evidence_id in result:
            fail(f"duplicate evidence id: {evidence_id}")
        observed = parse_time(item.get("observed_at"), f"evidence {evidence_id}.observed_at")
        valid_until = item.get("valid_until")
        if valid_until is not None:
            expires = parse_time(valid_until, f"evidence {evidence_id}.valid_until")
            if expires <= observed:
                fail(f"evidence {evidence_id}.valid_until must be after observed_at")
        if item.get("status") not in {"current", "stale", "disputed", "superseded"}:
            fail(f"evidence {evidence_id} has invalid status")
        result[evidence_id] = item
    return result


def check_refs(owner: dict, field: str, evidence: dict[str, dict], label: str, *, require_current: bool) -> None:
    refs = owner.get(field)
    if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
        fail(f"{label}.{field} must be a list of evidence ids")
    if len(refs) != len(set(refs)):
        fail(f"{label}.{field} contains duplicate evidence ids")
    unknown = sorted(set(refs) - set(evidence))
    if unknown:
        fail(f"{label} references unknown evidence: {', '.join(unknown)}")
    if require_current:
        bad = [ref for ref in refs if evidence[ref].get("status") != "current"]
        if bad:
            fail(f"{label} references non-current evidence: {', '.join(bad)}")


def validate(record: dict) -> None:
    required = {
        "schema_version", "record_id", "updated_at", "status", "transaction", "parties",
        "jurisdiction", "tax_determination", "invoice", "currency", "evidence", "approvals", "privacy"
    }
    missing = sorted(required - set(record))
    if missing:
        fail(f"missing required fields: {', '.join(missing)}")
    if record.get("schema_version") != "1.0.0":
        fail("schema_version must be 1.0.0")
    if record.get("status") not in {"draft", "needs_review", "ready_to_invoice", "issued", "corrected", "voided"}:
        fail("status is invalid")
    parse_time(record.get("updated_at"), "updated_at")
    scan_prohibited(record)

    status = record["status"]
    operational = status in OPERATIONAL_STATES
    evidence = evidence_map(record)

    transaction = required_object(record, "transaction")
    parse_time(transaction.get("occurred_at"), "transaction.occurred_at")
    if transaction.get("currency") != required_object(record, "currency").get("transaction_currency"):
        fail("transaction.currency must equal currency.transaction_currency")
    if transaction.get("type") in {"refund", "credit"} and not transaction.get("original_transaction_id"):
        fail(f"{transaction.get('type')} requires original_transaction_id")

    parties = required_object(record, "parties")
    for side in ("seller", "buyer"):
        party = parties.get(side)
        if not isinstance(party, dict):
            fail(f"parties.{side} must be an object")
        if operational and party.get("country") is None:
            fail(f"operational record requires parties.{side}.country")

    jurisdiction = required_object(record, "jurisdiction")
    check_refs(jurisdiction, "evidence_ids", evidence, "jurisdiction", require_current=operational)
    if operational:
        if jurisdiction.get("determination_status") != "confirmed":
            fail("operational record requires confirmed jurisdiction")
        for field in ("seller_country", "buyer_country", "supply_country", "ruleset"):
            if not jurisdiction.get(field):
                fail(f"operational record requires jurisdiction.{field}")
        if not jurisdiction.get("evidence_ids"):
            fail("operational record requires jurisdiction evidence")
        valid_until = jurisdiction.get("valid_until")
        if valid_until is not None and parse_time(valid_until, "jurisdiction.valid_until") < parse_time(record["updated_at"], "updated_at"):
            fail("operational jurisdiction ruleset is past valid_until")

    tax = required_object(record, "tax_determination")
    check_refs(tax, "evidence_ids", evidence, "tax_determination", require_current=operational)
    if operational:
        if tax.get("status") not in {"confirmed", "not_applicable"}:
            fail("operational record requires confirmed or not-applicable tax determination")
        if tax.get("treatment") == "unknown":
            fail("operational record cannot use unknown tax treatment")
        if tax.get("registration_required") == "unknown":
            fail("operational record requires a resolved registration determination")
        if not tax.get("evidence_ids"):
            fail("operational record requires tax determination evidence")
        if tax.get("status") == "confirmed" and tax.get("tax_type") != "none":
            if tax.get("rate_bps") is None and tax.get("treatment") not in {"exempt", "reverse_charge", "outside_scope", "marketplace_deemed_supplier"}:
                fail("confirmed taxable treatment requires rate_bps unless treatment explains no seller-collected rate")
            if tax.get("tax_amount_minor") is None:
                fail("confirmed tax determination requires tax_amount_minor")

    invoice = required_object(record, "invoice")
    check_refs(invoice, "evidence_ids", evidence, "invoice", require_current=operational)
    if operational:
        if invoice.get("required") == "unknown":
            fail("operational record requires invoice requirement determination")
        if invoice.get("required") == "yes":
            if invoice.get("status") not in {"validated", "issued", "corrected"}:
                fail("required invoice must be validated, issued, or corrected")
            if invoice.get("document_type") == "none":
                fail("required invoice needs a document_type")
            if not invoice.get("invoice_id"):
                fail("required invoice needs invoice_id")
            if not invoice.get("issue_date"):
                fail("required invoice needs issue_date")
            if not invoice.get("format"):
                fail("required invoice needs a declared format")
            if not invoice.get("evidence_ids"):
                fail("required invoice needs invoice-standard or requirement evidence")
        elif invoice.get("required") == "no" and invoice.get("status") != "not_required":
            fail("invoice.status must be not_required when invoice.required is no")
    if status == "corrected" or invoice.get("status") == "corrected":
        if not invoice.get("original_invoice_id"):
            fail("corrected fiscal record requires invoice.original_invoice_id")

    withholding = record.get("withholding")
    if withholding is not None:
        if not isinstance(withholding, dict):
            fail("withholding must be an object or null")
        check_refs(withholding, "evidence_ids", evidence, "withholding", require_current=operational)
        if operational and withholding.get("status") in {"unknown", "provisional"}:
            fail("operational record cannot leave withholding unresolved")
        if withholding.get("status") == "confirmed" and withholding.get("amount_minor") is None:
            fail("confirmed withholding requires amount_minor")

    platform = record.get("platform_reporting")
    if platform is not None:
        if not isinstance(platform, dict):
            fail("platform_reporting must be an object or null")
        check_refs(platform, "evidence_ids", evidence, "platform_reporting", require_current=operational)
        if operational and platform.get("status") in {"unknown", "provisional"}:
            fail("operational record cannot leave platform reporting unresolved")
        if platform.get("status") == "confirmed" and platform.get("seller_reportable") == "unknown":
            fail("confirmed platform reporting requires seller_reportable yes/no")

    currency = required_object(record, "currency")
    check_refs(currency, "evidence_ids", evidence, "currency", require_current=operational)
    fx_required = currency.get("fx_required")
    if not isinstance(fx_required, bool):
        fail("currency.fx_required must be boolean")
    if currency.get("transaction_currency") != currency.get("accounting_currency") and not fx_required:
        fail("fx_required must be true when transaction and accounting currencies differ")
    if fx_required:
        if currency.get("rate") is None or currency.get("rate_source") is None or currency.get("rate_observed_at") is None:
            fail("FX conversion requires rate, rate_source, and rate_observed_at")
        parse_time(currency.get("rate_observed_at"), "currency.rate_observed_at")
        if operational and not currency.get("evidence_ids"):
            fail("operational FX conversion requires source evidence")
    elif currency.get("rate") is not None:
        fail("currency.rate should be null when fx_required is false")

    approvals = required_object(record, "approvals")
    if not isinstance(approvals.get("human_review_required"), bool):
        fail("approvals.human_review_required must be boolean")
    if approvals.get("human_review_required"):
        if operational and approvals.get("review_status") != "approved":
            fail("operational record requiring human review must be approved")
        if approvals.get("review_status") == "approved" and approvals.get("reviewed_at") is None:
            fail("approved review requires reviewed_at")
    elif approvals.get("review_status") not in {"not_required", "approved"}:
        fail("review_status must be not_required or approved when human review is not required")

    unresolved = (
        jurisdiction.get("determination_status") in {"unknown", "provisional"}
        or tax.get("status") in {"unknown", "provisional"}
        or tax.get("registration_required") == "unknown"
        or invoice.get("required") == "unknown"
        or (withholding is not None and withholding.get("status") in {"unknown", "provisional"})
        or (platform is not None and platform.get("status") in {"unknown", "provisional"})
    )
    if unresolved and status not in {"draft", "needs_review"}:
        fail("unresolved fiscal determinations require draft or needs_review status")
    if unresolved and approvals.get("human_review_required") is not True:
        fail("unresolved fiscal determinations require human review")

    privacy = required_object(record, "privacy")
    for field in ("contains_payment_credentials", "contains_secrets", "contains_private_prompts", "contains_unnecessary_personal_data"):
        if privacy.get(field) is not False:
            fail(f"privacy.{field} must be false")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", nargs="?", default="templates/FISCAL_TRANSACTION_EVIDENCE.json")
    args = parser.parse_args()
    path = safe_path(args.record)
    record = load_json(path)
    validate(record)
    print(
        "fiscal evidence OK: "
        f"{record['record_id']} status={record['status']} "
        f"transaction={record['transaction']['transaction_id']} "
        f"evidence={len(record['evidence'])}"
    )


if __name__ == "__main__":
    main()
