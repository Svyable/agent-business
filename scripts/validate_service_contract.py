#!/usr/bin/env python3
"""Dependency-free semantic checks for an Agent Business service contract pack."""

import json
import sys
from pathlib import Path


ALLOWED_STATUS = {"draft", "proposed", "approved", "active", "suspended", "terminated", "expired"}
AUTHORIZED_STATUS = {"approved", "active", "suspended", "terminated", "expired"}


def fail(errors, message):
    errors.append(message)


def require(obj, key, errors, path="root"):
    if key not in obj:
        fail(errors, f"{path}: missing required field '{key}'")
        return None
    return obj[key]


def unique_ids(items, key, errors, path):
    seen = set()
    for index, item in enumerate(items):
        value = item.get(key)
        if not value:
            fail(errors, f"{path}[{index}]: missing {key}")
        elif value in seen:
            fail(errors, f"{path}: duplicate {key} '{value}'")
        seen.add(value)
    return seen


def validate(contract):
    errors = []
    warnings = []

    if contract.get("schema_version") != "1.0":
        fail(errors, "root: schema_version must be '1.0'")

    status = require(contract, "status", errors)
    if status and status not in ALLOWED_STATUS:
        fail(errors, f"root: unknown status '{status}'")

    parties = require(contract, "parties", errors) or {}
    buyer = parties.get("buyer", {})
    seller = parties.get("seller", {})
    for name, party in (("buyer", buyer), ("seller", seller)):
        if not party.get("party_id"):
            fail(errors, f"parties.{name}: party_id is required")
        if status in AUTHORIZED_STATUS and not party.get("authority_reference"):
            fail(errors, f"parties.{name}: authority_reference is required once contract is {status}")

    service = require(contract, "service", errors) or {}
    deliverables = service.get("deliverables", [])
    if not deliverables:
        fail(errors, "service.deliverables: at least one deliverable is required")
    deliverable_ids = unique_ids(deliverables, "deliverable_id", errors, "service.deliverables")

    acceptance = require(contract, "acceptance", errors) or {}
    criteria = acceptance.get("criteria", [])
    if not criteria:
        fail(errors, "acceptance.criteria: at least one criterion is required")
    criterion_ids = unique_ids(criteria, "criterion_id", errors, "acceptance.criteria")
    for deliverable in deliverables:
        for criterion_id in deliverable.get("acceptance_criterion_ids", []):
            if criterion_id not in criterion_ids:
                fail(errors, f"deliverable '{deliverable.get('deliverable_id')}' references unknown criterion '{criterion_id}'")

    commercials = require(contract, "commercials", errors) or {}
    spend_ceiling = commercials.get("spend_ceiling")
    rates = commercials.get("rates", [])
    if spend_ceiling is None or spend_ceiling < 0:
        fail(errors, "commercials.spend_ceiling must be >= 0")
    for rate in rates:
        if rate.get("amount", -1) < 0:
            fail(errors, f"commercials.rates '{rate.get('rate_id')}' has negative amount")

    authority = require(contract, "authority", errors) or {}
    auto = authority.get("auto_approve_below")
    human = authority.get("human_approval_required_above")
    if auto is None or human is None:
        fail(errors, "authority: both auto_approve_below and human_approval_required_above are required")
    elif auto > human:
        fail(errors, "authority: auto_approve_below cannot exceed human_approval_required_above")
    if spend_ceiling is not None and auto is not None and auto > spend_ceiling:
        fail(errors, "authority: auto_approve_below cannot exceed commercials.spend_ceiling")
    if status in AUTHORIZED_STATUS:
        if not authority.get("buyer_approval_id"):
            fail(errors, f"authority: buyer_approval_id is required once contract is {status}")
        if not authority.get("seller_authority_id"):
            fail(errors, f"authority: seller_authority_id is required once contract is {status}")

    slos = require(contract, "service_levels", errors) or []
    unique_ids(slos, "slo_id", errors, "service_levels")
    for slo in slos:
        if not slo.get("measurement_source"):
            fail(errors, f"SLO '{slo.get('slo_id')}' needs a measurement_source")

    change_control = require(contract, "change_control", errors) or {}
    if status in AUTHORIZED_STATUS and not change_control.get("requires_change_order"):
        warnings.append("active/approved contract allows material changes without a change order")
    unique_ids(change_control.get("change_orders", []), "change_order_id", errors, "change_control.change_orders")

    billing = require(contract, "billing", errors) or {}
    if billing.get("acceptance_required_before_charge") and not acceptance.get("criteria"):
        fail(errors, "billing requires acceptance before charge but no acceptance criteria exist")

    disputes = require(contract, "disputes", errors) or {}
    if not disputes.get("required_evidence"):
        fail(errors, "disputes.required_evidence must not be empty")
    if not disputes.get("escalation_path"):
        fail(errors, "disputes.escalation_path must not be empty")

    receipts = contract.get("receipts", [])
    receipt_ids = unique_ids(receipts, "receipt_id", errors, "receipts")
    del receipt_ids
    for receipt in receipts:
        deliverable_id = receipt.get("deliverable_id")
        if deliverable_id not in deliverable_ids:
            fail(errors, f"receipt '{receipt.get('receipt_id')}' references unknown deliverable '{deliverable_id}'")
        evidence = receipt.get("evidence_refs", [])
        if receipt.get("acceptance_status") == "accepted" and not evidence:
            fail(errors, f"accepted receipt '{receipt.get('receipt_id')}' has no evidence_refs")
        if receipt.get("billable_event_id") and receipt.get("acceptance_status") != "accepted" and billing.get("acceptance_required_before_charge"):
            fail(errors, f"receipt '{receipt.get('receipt_id')}' has a billable_event_id before acceptance")

    if status in {"approved", "active"} and spend_ceiling == 0:
        warnings.append("approved/active contract has a zero spend ceiling")
    if status == "draft" and any((authority.get("buyer_approval_id"), authority.get("seller_authority_id"))):
        warnings.append("draft contract contains authority IDs; validator does not treat them as consent")

    return errors, warnings


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/validate_service_contract.py path/to/contract.json", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    try:
        contract = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: unable to read valid JSON: {exc}", file=sys.stderr)
        return 2

    errors, warnings = validate(contract)
    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"FAIL: {len(errors)} semantic validation error(s)", file=sys.stderr)
        return 1

    print(f"PASS: {path} is semantically consistent ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
