#!/usr/bin/env python3
"""Validate an Agent Business demand request / machine RFQ using stdlib only."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

VALID_STATUS = {
    "draft", "published", "invited", "matched", "bids_received", "shortlisted",
    "awarded", "contracted", "paid", "delivered", "accepted", "disputed",
    "closed", "cancelled", "expired",
}
VALID_QUALITY = {"verified_commercial", "self_declared_intent", "exploratory_research", "synthetic_test"}
CONSEQUENTIAL = {"awarded", "contracted", "paid", "delivered", "accepted", "disputed", "closed"}
AWARDED_OR_LATER = CONSEQUENTIAL


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


def require_dict(record: dict, key: str, errors: list[str]) -> dict:
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
        "schema_version", "request_id", "request_version", "updated_at", "status",
        "demand_quality", "buyer", "outcome", "requirements", "budget", "timing",
        "authority", "bidding", "award", "acceptance", "disclosure",
    ]
    for key in required:
        if key not in record:
            errors.append(f"missing required field: {key}")

    if errors:
        return errors

    if record.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0")

    status = record.get("status")
    quality = record.get("demand_quality")
    if status not in VALID_STATUS:
        errors.append("status is not recognized")
    if quality not in VALID_QUALITY:
        errors.append("demand_quality is not recognized")
    if status == "draft" and not allow_draft:
        errors.append("draft requests require --allow-draft")

    updated_at = parse_time(record.get("updated_at"), "updated_at", errors)
    buyer = require_dict(record, "buyer", errors)
    outcome = require_dict(record, "outcome", errors)
    requirements = require_dict(record, "requirements", errors)
    budget = require_dict(record, "budget", errors)
    timing = require_dict(record, "timing", errors)
    authority = require_dict(record, "authority", errors)
    bidding = require_dict(record, "bidding", errors)
    award = require_dict(record, "award", errors)
    acceptance = require_dict(record, "acceptance", errors)
    disclosure = require_dict(record, "disclosure", errors)

    # Disclosure-safe public repository invariant.
    for flag in (
        "contains_secrets", "contains_private_customer_data", "contains_private_prompts",
        "contains_credentials", "contains_confidential_procurement_data",
    ):
        if disclosure.get(flag) is not False:
            errors.append(f"disclosure.{flag} must be false")
    if bidding.get("mode") == "public":
        if disclosure.get("tier") != "public":
            errors.append("public bidding requires disclosure.tier=public")
        if disclosure.get("public_disclosure_confirmed") is not True:
            errors.append("public bidding requires public_disclosure_confirmed=true")
    if disclosure.get("tier") != "public" and bidding.get("mode") == "public":
        errors.append("restricted/confidential requests cannot use public bidding")

    # Coherent ranges.
    qmin, qmax = outcome.get("quantity_min"), outcome.get("quantity_max")
    if qmin is not None and qmax is not None and qmin > qmax:
        errors.append("outcome.quantity_min cannot exceed quantity_max")
    bmin, bmax = budget.get("public_min_minor"), budget.get("public_max_minor")
    if bmin is not None and bmax is not None and bmin > bmax:
        errors.append("budget.public_min_minor cannot exceed public_max_minor")
    if budget.get("budget_disclosed") is False and (bmin is not None or bmax is not None):
        errors.append("undisclosed budget must not expose public budget amounts")
    if budget.get("budget_disclosed") is True and not budget.get("currency"):
        errors.append("disclosed budget requires currency")

    # Bid/deadline ordering.
    opens = parse_time(timing.get("bid_opens_at"), "timing.bid_opens_at", errors)
    closes = parse_time(timing.get("bid_closes_at"), "timing.bid_closes_at", errors)
    due = parse_time(timing.get("delivery_due_at"), "timing.delivery_due_at", errors)
    if opens and closes and closes <= opens:
        errors.append("bid_closes_at must be after bid_opens_at")
    if closes and due and due <= closes:
        errors.append("delivery_due_at must be after bid_closes_at")
    if updated_at and closes and closes < updated_at and status not in {"closed", "cancelled", "expired", "awarded", "contracted", "paid", "delivered", "accepted", "disputed"}:
        errors.append("open sourcing state cannot have a bid window already closed before updated_at")

    # Authority lifecycle.
    auth_state = authority.get("authority_state")
    auth_ref = authority.get("authority_evidence_ref")
    auth_currency = authority.get("authorized_currency")
    auth_max = authority.get("max_authorized_spend_minor")
    auth_effective = parse_time(authority.get("effective_at"), "authority.effective_at", errors)
    auth_expires = parse_time(authority.get("expires_at"), "authority.expires_at", errors)
    if auth_effective and auth_expires and auth_expires <= auth_effective:
        errors.append("authority.expires_at must be after effective_at")
    if auth_state == "current":
        if not auth_ref:
            errors.append("current authority requires authority_evidence_ref")
        if not auth_currency:
            errors.append("current authority requires authorized_currency")
        if not isinstance(auth_max, int) or auth_max <= 0:
            errors.append("current authority requires positive max_authorized_spend_minor")
        if not auth_effective or not auth_expires:
            errors.append("current authority requires effective_at and expires_at")
        if updated_at and auth_effective and auth_effective > updated_at:
            errors.append("authority cannot be current before its effective_at")
        if updated_at and auth_expires and auth_expires <= updated_at:
            errors.append("authority marked current is expired at updated_at")

    # Demand quality cannot be inflated into verified willingness-to-pay.
    if quality == "verified_commercial":
        if auth_state != "current":
            errors.append("verified_commercial demand requires current buyer authority")
        if buyer.get("identity_confidence") in {None, "unverified"}:
            errors.append("verified_commercial demand requires buyer identity evidence")
        if not auth_ref:
            errors.append("verified_commercial demand requires authority evidence")
    if quality in {"exploratory_research", "synthetic_test"}:
        if bidding.get("automatic_award_allowed") is True:
            errors.append("exploratory/synthetic demand cannot enable automatic award")
        if status in CONSEQUENTIAL:
            errors.append("exploratory/synthetic demand cannot enter consequential commercial states")

    # Automatic award is a strict gate, not a ranking preference.
    auto = bidding.get("automatic_award_allowed")
    auto_max = bidding.get("max_autonomous_award_minor")
    if auto is True:
        if quality != "verified_commercial":
            errors.append("automatic award requires verified_commercial demand")
        if auth_state != "current":
            errors.append("automatic award requires current authority")
        if not isinstance(auto_max, int) or auto_max <= 0:
            errors.append("automatic award requires positive max_autonomous_award_minor")
        if isinstance(auth_max, int) and isinstance(auto_max, int) and auto_max > auth_max:
            errors.append("max_autonomous_award_minor exceeds buyer authority")
        if bidding.get("award_method") in {None, "none"}:
            errors.append("automatic award requires an explicit award_method")
        if not requirements.get("hard_constraints"):
            errors.append("automatic award requires explicit hard_constraints")
        if not acceptance.get("criteria"):
            errors.append("automatic award requires acceptance criteria")
        if budget.get("currency") and auth_currency and budget.get("currency") != auth_currency:
            errors.append("budget currency differs from authorized currency")
    elif auto_max is not None:
        errors.append("max_autonomous_award_minor must be null when automatic award is disabled")

    if bidding.get("sponsored_ranking_separated") is not True:
        errors.append("sponsored ranking must remain separate from matching quality")

    # Awarded and later states require a reconstructable selection.
    if status in AWARDED_OR_LATER:
        if bidding.get("award_method") in {None, "none"}:
            errors.append("awarded or later state requires an award_method")
        for field in ("seller_listing_ref", "seller_listing_version", "proposal_ref", "awarded_price_minor", "awarded_currency", "awarded_at"):
            if award.get(field) is None:
                errors.append(f"{status} state requires award.{field}")
        awarded_at = parse_time(award.get("awarded_at"), "award.awarded_at", errors)
        price = award.get("awarded_price_minor")
        if auth_state != "current":
            errors.append("consequential awarded state requires current authority")
        if isinstance(price, int) and isinstance(auth_max, int) and price > auth_max:
            errors.append("awarded price exceeds authorized spend")
        if award.get("awarded_currency") and auth_currency and award.get("awarded_currency") != auth_currency:
            errors.append("awarded currency differs from authorized currency")
        if auth_effective and awarded_at and awarded_at < auth_effective:
            errors.append("award occurred before authority became effective")
        if auth_expires and awarded_at and awarded_at >= auth_expires:
            errors.append("award occurred after authority expired")

    # Payment/delivery never imply acceptance.
    acceptance_state = acceptance.get("acceptance_state")
    if status in {"paid", "delivered"} and acceptance_state == "accepted":
        errors.append(f"{status} state cannot itself be treated as accepted")
    if status == "accepted":
        if acceptance_state != "accepted":
            errors.append("accepted status requires acceptance_state=accepted")
        if not acceptance.get("criteria"):
            errors.append("accepted status requires acceptance criteria")
        if not acceptance.get("accepted_at"):
            errors.append("accepted status requires accepted_at")
    if acceptance_state == "accepted" and not acceptance.get("criteria"):
        errors.append("accepted outcome requires explicit acceptance criteria")

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
