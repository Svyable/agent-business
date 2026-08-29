#!/usr/bin/env python3
"""Validate an Agent Business RFQ seller proposal using Python stdlib only."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

VALID_STATUS = {"draft", "submitted", "superseded", "withdrawn", "expired", "selected", "rejected"}
CONSEQUENTIAL = {"submitted", "selected"}


def parse_time(value: object, field: str, errors: list[str]) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        errors.append(f"{field} must be an RFC3339 string or null")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{field} is not a valid RFC3339 timestamp")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{field} must include a timezone")
        return None
    return parsed.astimezone(timezone.utc)


def obj(record: dict, key: str, errors: list[str]) -> dict:
    value = record.get(key)
    if not isinstance(value, dict):
        errors.append(f"{key} must be an object")
        return {}
    return value


def validate_record(record: object, allow_draft: bool = False) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["root must be a JSON object"]

    required = [
        "schema_version", "proposal_id", "proposal_version", "updated_at", "status",
        "request", "seller", "offer", "service_levels", "compatibility", "deviations",
        "eligibility", "payment", "acceptance", "normalization", "selection", "disclosure",
    ]
    for key in required:
        if key not in record:
            errors.append(f"missing required field: {key}")
    if errors:
        return errors

    if record.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0")
    status = record.get("status")
    if status not in VALID_STATUS:
        errors.append("status is not recognized")
    if status == "draft" and not allow_draft:
        errors.append("draft proposals require --allow-draft")

    updated_at = parse_time(record.get("updated_at"), "updated_at", errors)
    request = obj(record, "request", errors)
    seller = obj(record, "seller", errors)
    offer = obj(record, "offer", errors)
    eligibility = obj(record, "eligibility", errors)
    payment = obj(record, "payment", errors)
    acceptance = obj(record, "acceptance", errors)
    normalization = obj(record, "normalization", errors)
    selection = obj(record, "selection", errors)
    disclosure = obj(record, "disclosure", errors)
    deviations = record.get("deviations")
    if not isinstance(deviations, list):
        errors.append("deviations must be an array")
        deviations = []

    for field in ("request_id", "request_version", "request_digest"):
        if not request.get(field):
            errors.append(f"request.{field} is required")
    if eligibility.get("evaluated_against_request_version") != request.get("request_version"):
        errors.append("eligibility must be evaluated against the referenced request version")

    for field in ("listing_id", "listing_version", "listing_updated_at"):
        if not seller.get(field):
            errors.append(f"seller.{field} is required")

    # Public-repository safety.
    for flag in (
        "contains_secrets", "contains_private_customer_data", "contains_private_prompts",
        "contains_credentials", "contains_confidential_bid_data",
    ):
        if disclosure.get(flag) is not False:
            errors.append(f"disclosure.{flag} must be false")
    if disclosure.get("public_disclosure_confirmed") is not True:
        errors.append("public_disclosure_confirmed must be true")

    bid_closes = parse_time(request.get("bid_closes_at"), "request.bid_closes_at", errors)
    listing_updated = parse_time(seller.get("listing_updated_at"), "seller.listing_updated_at", errors)
    evidence_expires = parse_time(seller.get("listing_evidence_expires_at"), "seller.listing_evidence_expires_at", errors)
    auth_effective = parse_time(seller.get("authority_effective_at"), "seller.authority_effective_at", errors)
    auth_expires = parse_time(seller.get("authority_expires_at"), "seller.authority_expires_at", errors)
    valid_until = parse_time(offer.get("valid_until"), "offer.valid_until", errors)
    submitted_at = parse_time(offer.get("submitted_at"), "offer.submitted_at", errors)
    delivery_due = parse_time(offer.get("delivery_due_at"), "offer.delivery_due_at", errors)
    selected_at = parse_time(selection.get("selected_at"), "selection.selected_at", errors)

    if auth_effective and auth_expires and auth_expires <= auth_effective:
        errors.append("seller authority expiry must be after effective time")
    if submitted_at and valid_until and valid_until <= submitted_at:
        errors.append("offer.valid_until must be after submitted_at")
    if submitted_at and delivery_due and delivery_due <= submitted_at:
        errors.append("offer.delivery_due_at must be after submitted_at")
    if submitted_at and bid_closes and submitted_at > bid_closes:
        errors.append("proposal was submitted after the RFQ bid window closed")
    if listing_updated and submitted_at and listing_updated > submitted_at:
        errors.append("seller listing version cannot be newer than the proposal submission")

    # Submitted/selected proposals need fresh listing evidence and current seller authority.
    if status in CONSEQUENTIAL:
        if submitted_at is None:
            errors.append(f"{status} proposal requires offer.submitted_at")
        if valid_until is None:
            errors.append(f"{status} proposal requires offer.valid_until")
        if seller.get("listing_evidence_state") != "current":
            errors.append(f"{status} proposal requires current seller listing evidence")
        if evidence_expires is None:
            errors.append(f"{status} proposal requires listing evidence expiry")
        elif submitted_at and evidence_expires <= submitted_at:
            errors.append("seller listing evidence was stale at submission")
        if seller.get("authority_state") != "current":
            errors.append(f"{status} proposal requires current seller authority")
        if not seller.get("authority_evidence_ref"):
            errors.append(f"{status} proposal requires seller authority evidence")
        if auth_effective is None or auth_expires is None:
            errors.append(f"{status} proposal requires bounded authority validity")
        if submitted_at and auth_effective and submitted_at < auth_effective:
            errors.append("proposal submitted before seller authority became effective")
        if submitted_at and auth_expires and submitted_at >= auth_expires:
            errors.append("proposal submitted after seller authority expired")
        if offer.get("currency") is None or offer.get("total_price_minor") is None:
            errors.append(f"{status} proposal requires a concrete price and currency")
        if offer.get("pricing_basis") in {"undecided", "indicative"}:
            errors.append(f"{status} proposal requires a binding pricing basis")

    # Every hard-requirement deviation must remain explicit and make the bid ineligible.
    hard_deviation_ids: set[str] = set()
    seen_ids: set[str] = set()
    for idx, deviation in enumerate(deviations):
        if not isinstance(deviation, dict):
            errors.append(f"deviations[{idx}] must be an object")
            continue
        deviation_id = deviation.get("id")
        if not deviation_id:
            errors.append(f"deviations[{idx}].id is required")
            continue
        if deviation_id in seen_ids:
            errors.append(f"duplicate deviation id: {deviation_id}")
        seen_ids.add(deviation_id)
        if deviation.get("severity") == "hard_requirement":
            hard_deviation_ids.add(deviation_id)
            if deviation.get("buyer_approval_required") is not True:
                errors.append(f"hard-requirement deviation {deviation_id} must require buyer approval")

    unresolved = eligibility.get("unresolved_hard_requirement_ids")
    if not isinstance(unresolved, list):
        errors.append("eligibility.unresolved_hard_requirement_ids must be an array")
        unresolved = []
    unresolved_set = set(unresolved)
    missing = hard_deviation_ids - unresolved_set
    if missing:
        errors.append("hard-requirement deviations must appear in unresolved_hard_requirement_ids")
    if eligibility.get("all_hard_requirements_satisfied") is True and unresolved:
        errors.append("all_hard_requirements_satisfied cannot be true with unresolved hard requirements")
    if eligibility.get("all_hard_requirements_satisfied") is False and not unresolved:
        errors.append("unsatisfied hard requirements require explicit unresolved IDs")
    if eligibility.get("eligible_for_award") is True:
        if eligibility.get("all_hard_requirements_satisfied") is not True:
            errors.append("eligible_for_award requires all hard requirements satisfied")
        if unresolved:
            errors.append("eligible_for_award requires no unresolved hard requirements")
        if hard_deviation_ids:
            errors.append("eligible_for_award cannot contain hard-requirement deviations")
        if acceptance.get("request_criteria_acknowledged") is not True:
            errors.append("eligible_for_award requires acceptance criteria acknowledgement")

    # Comparison fields must not silently rewrite commercial truth.
    comparison_currency = normalization.get("comparison_currency")
    comparable_total = normalization.get("comparable_total_minor")
    normalization_method = str(normalization.get("normalization_method", "")).strip().lower()
    if comparable_total is not None and comparison_currency is None:
        errors.append("normalized total requires comparison_currency")
    if offer.get("currency") == comparison_currency and offer.get("total_price_minor") is not None and comparable_total is not None:
        if offer.get("total_price_minor") != comparable_total and not normalization_method.startswith(("adjusted:", "fx:")):
            errors.append("same-currency normalized total differs without an explicit adjustment method")

    if payment.get("asset_or_currency") and offer.get("currency") and payment.get("asset_or_currency") != offer.get("currency"):
        if not any(isinstance(d, dict) and d.get("dimension") == "payment" for d in deviations):
            errors.append("payment currency/asset difference requires an explicit payment deviation")

    # Selection is not a contract or payment authority; it must be buyer-evidenced.
    if status == "selected":
        if eligibility.get("eligible_for_award") is not True:
            errors.append("selected proposal must be eligible_for_award")
        if not selection.get("buyer_selection_ref"):
            errors.append("selected proposal requires buyer_selection_ref")
        if selected_at is None:
            errors.append("selected proposal requires selected_at")
        if valid_until and selected_at and selected_at >= valid_until:
            errors.append("proposal was selected after quote validity expired")
    elif selection.get("buyer_selection_ref") is not None or selection.get("selected_at") is not None:
        errors.append("selection evidence must be null unless status is selected")

    if status == "superseded" and record.get("proposal_version") in {None, ""}:
        errors.append("superseded proposal requires a version")

    if updated_at and submitted_at and submitted_at > updated_at:
        errors.append("submitted_at cannot be after updated_at")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--allow-draft", action="store_true")
    args = parser.parse_args()
    try:
        record = json.loads(args.path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_record(record, allow_draft=args.allow_draft)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
