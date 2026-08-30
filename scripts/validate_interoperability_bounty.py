#!/usr/bin/env python3
"""Validate demand-backed interoperability bounty records with fail-closed semantics."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

SCHEMA_VERSION = "1.0.0"
STATUSES = {"draft", "open", "awarded", "submitted", "accepted", "closed", "cancelled"}
EVIDENCE_CLASSES = {"synthetic_test", "self_declared_intent", "observed_commercial_demand", "verified_commercial_demand"}
COMMERCIAL_CLASSES = {"observed_commercial_demand", "verified_commercial_demand"}
SPONSOR_STATES = {"pledged", "verified", "revoked", "expired"}
BUILDER_STATES = {"none", "proposed", "selected", "submitted"}
PAYOUT_STATES = {"not_earned", "earned", "external_execution_pending", "settled", "failed"}


def parse_time(value: object, field: str, errors: list[str]) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        errors.append(f"{field} must be an RFC3339 timestamp or null")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{field} is not a valid RFC3339 timestamp")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{field} must include a timezone")
        return None
    return parsed


def parse_semver(value: object, field: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{field} must be MAJOR.MINOR.PATCH")
        return
    parts = value.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        errors.append(f"{field} must be MAJOR.MINOR.PATCH")


def valid_range(value: object) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(item, int) and not isinstance(item, bool) and item >= 0 for item in value)
        and value[0] <= value[1]
    )


def required_object(record: dict, key: str, errors: list[str]) -> dict:
    value = record.get(key)
    if not isinstance(value, dict):
        errors.append(f"{key} must be an object")
        return {}
    return value


def validate(record: object, allow_draft: bool = False) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["root must be a JSON object"]

    required = [
        "schema_version", "bounty_id", "status", "target", "demand", "funding",
        "builder", "award", "acceptance", "unlock_verification", "payout",
        "value_attribution", "conflicts", "authority", "privacy",
    ]
    for key in required:
        if key not in record:
            errors.append(f"missing required field: {key}")
    if errors:
        return errors

    if record.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if not record.get("bounty_id"):
        errors.append("bounty_id is required")
    status = record.get("status")
    if status not in STATUSES:
        errors.append("status is not recognized")
        return errors
    if status == "draft" and not allow_draft:
        errors.append("draft bounty requires --allow-draft")

    target = required_object(record, "target", errors)
    demand = required_object(record, "demand", errors)
    funding = required_object(record, "funding", errors)
    builder = required_object(record, "builder", errors)
    award = required_object(record, "award", errors)
    acceptance = required_object(record, "acceptance", errors)
    unlock = required_object(record, "unlock_verification", errors)
    payout = required_object(record, "payout", errors)
    attribution = required_object(record, "value_attribution", errors)
    conflicts = required_object(record, "conflicts", errors)
    authority = required_object(record, "authority", errors)
    privacy = required_object(record, "privacy", errors)

    # Target and immutable acceptance contract.
    if not target.get("convention_id"):
        errors.append("target.convention_id is required")
    parse_semver(target.get("spec_version"), "target.spec_version", errors)
    for key in ("corridor_population_ref", "population_hash", "selection_rule_hash", "acceptance_criteria_hash"):
        if not target.get(key):
            errors.append(f"target.{key} is required")
        elif status != "draft" and "replace" in str(target.get(key)).lower():
            errors.append(f"target.{key} must be stable before publication")
    minimum_unlock = target.get("minimum_incremental_reachable_corridors")
    if not isinstance(minimum_unlock, int) or isinstance(minimum_unlock, bool) or minimum_unlock < 1:
        errors.append("target.minimum_incremental_reachable_corridors must be >= 1")
        minimum_unlock = 1
    tests = target.get("tests")
    if not isinstance(tests, list) or not tests:
        errors.append("target.tests must be a non-empty array")
    else:
        seen_tests: set[str] = set()
        for idx, test in enumerate(tests):
            if not isinstance(test, dict):
                errors.append(f"target.tests[{idx}] must be an object")
                continue
            test_id = test.get("id")
            if not test_id or test_id in seen_tests:
                errors.append(f"target.tests[{idx}].id must be present and unique")
            seen_tests.add(test_id)
            if not test.get("procedure"):
                errors.append(f"target.tests[{idx}].procedure is required")

    if acceptance.get("criteria_hash") != target.get("acceptance_criteria_hash"):
        errors.append("acceptance.criteria_hash must equal target.acceptance_criteria_hash")

    # Demand evidence and commercial-value claims.
    evidence_class = demand.get("evidence_class")
    if evidence_class not in EVIDENCE_CLASSES:
        errors.append("demand.evidence_class is not recognized")
    if not demand.get("snapshot_ref"):
        errors.append("demand.snapshot_ref is required")
    corridor_count = demand.get("corridor_count")
    if not isinstance(corridor_count, int) or isinstance(corridor_count, bool) or corridor_count < 0:
        errors.append("demand.corridor_count must be a non-negative integer")
        corridor_count = 0
    demand_value = demand.get("qualified_value_minor_range")
    demand_currency = demand.get("currency")
    if demand_value is not None:
        if evidence_class not in COMMERCIAL_CLASSES:
            errors.append("only observed/verified commercial demand may carry qualified value")
        if not valid_range(demand_value):
            errors.append("demand.qualified_value_minor_range must be [low, high] non-negative integers")
        if not demand_currency:
            errors.append("demand.currency is required with qualified value")
    elif evidence_class not in COMMERCIAL_CLASSES and demand_currency is not None:
        errors.append("synthetic/self-declared demand must not carry a commercial-value currency")
    evidence_refs = demand.get("evidence_refs")
    if not isinstance(evidence_refs, list):
        errors.append("demand.evidence_refs must be an array")
        evidence_refs = []
    if demand.get("demand_backed_claim") is True:
        if evidence_class not in COMMERCIAL_CLASSES:
            errors.append("demand_backed_claim requires observed/verified commercial demand")
        if corridor_count < 1:
            errors.append("demand_backed_claim requires at least one corridor")
        if not evidence_refs:
            errors.append("demand_backed_claim requires demand evidence_refs")
    elif demand.get("demand_backed_claim") is not False:
        errors.append("demand.demand_backed_claim must be boolean")

    # Funding: commitment, verification, and custody are intentionally distinct.
    if funding.get("repo_custodies_funds") is not False:
        errors.append("funding.repo_custodies_funds must be false")
    funding_currency = funding.get("currency")
    payout_cap = funding.get("payout_cap_minor")
    if not isinstance(payout_cap, int) or isinstance(payout_cap, bool) or payout_cap < 0:
        errors.append("funding.payout_cap_minor must be a non-negative integer")
        payout_cap = 0
    sponsors = funding.get("sponsors")
    if not isinstance(sponsors, list):
        errors.append("funding.sponsors must be an array")
        sponsors = []
    seen_sponsors: set[str] = set()
    active_total = 0
    verified_total = 0
    sponsor_refs: set[str] = set()
    for idx, sponsor in enumerate(sponsors):
        prefix = f"funding.sponsors[{idx}]"
        if not isinstance(sponsor, dict):
            errors.append(f"{prefix} must be an object")
            continue
        ref = sponsor.get("sponsor_ref")
        if not ref or ref in seen_sponsors:
            errors.append(f"{prefix}.sponsor_ref must be present and unique")
        if ref:
            seen_sponsors.add(ref)
            sponsor_refs.add(ref)
        amount = sponsor.get("commitment_minor")
        if not isinstance(amount, int) or isinstance(amount, bool) or amount < 1:
            errors.append(f"{prefix}.commitment_minor must be >= 1")
            amount = 0
        state = sponsor.get("state")
        if state not in SPONSOR_STATES:
            errors.append(f"{prefix}.state is not recognized")
        currency = sponsor.get("currency")
        if not funding_currency or currency != funding_currency:
            errors.append(f"{prefix}.currency must equal funding.currency")
        parse_time(sponsor.get("expires_at"), f"{prefix}.expires_at", errors)
        if state in {"pledged", "verified"}:
            active_total += amount
        if state == "verified":
            verified_total += amount
            if not sponsor.get("verification_evidence_ref"):
                errors.append(f"{prefix} verified funding requires verification_evidence_ref")
    if (payout_cap > 0 or sponsors) and not funding_currency:
        errors.append("funding.currency is required when a payout or sponsor commitment exists")
    if status in {"open", "awarded", "submitted", "accepted", "closed"}:
        if payout_cap < 1:
            errors.append(f"{status} bounty requires a positive payout cap")
        if active_total < 1:
            errors.append(f"{status} bounty requires an active sponsor commitment")
    if status in {"awarded", "submitted", "accepted", "closed"} and verified_total < payout_cap:
        errors.append("awarded-or-later bounty requires verified sponsor commitments covering payout cap")

    custody_state = funding.get("custody_state")
    provider_ref = funding.get("custody_provider_ref")
    custody_evidence = funding.get("custody_evidence_ref")
    if custody_state not in {"none", "external_unverified", "external_verified"}:
        errors.append("funding.custody_state is not recognized")
    elif custody_state == "none" and (provider_ref or custody_evidence):
        errors.append("custody_state none must not claim custody provider/evidence")
    elif custody_state == "external_unverified" and not provider_ref:
        errors.append("external_unverified custody requires custody_provider_ref")
    elif custody_state == "external_verified" and (not provider_ref or not custody_evidence):
        errors.append("external_verified custody requires provider and evidence refs")

    # Builder and conflicts.
    builder_state = builder.get("state")
    if builder_state not in BUILDER_STATES:
        errors.append("builder.state is not recognized")
    builder_ref = builder.get("builder_ref")
    if builder_state == "none":
        if any(builder.get(key) is not None for key in ("builder_ref", "proposal_ref", "implementation_cost_minor_range", "currency", "compatibility_profile_target_ref")):
            errors.append("builder.state none must not claim builder/proposal/cost/profile data")
    else:
        for key in ("builder_ref", "proposal_ref", "compatibility_profile_target_ref"):
            if not builder.get(key):
                errors.append(f"builder.{key} is required when builder.state is {builder_state}")
        cost_range = builder.get("implementation_cost_minor_range")
        if not valid_range(cost_range):
            errors.append("builder.implementation_cost_minor_range must be a valid [low, high] range")
        if not builder.get("currency"):
            errors.append("builder.currency is required when a builder exists")
        elif funding_currency and builder.get("currency") != funding_currency:
            errors.append("builder.currency must equal funding.currency for comparable bounty economics")
    submission_refs = builder.get("submission_evidence_refs")
    if not isinstance(submission_refs, list):
        errors.append("builder.submission_evidence_refs must be an array")
        submission_refs = []
    if builder_state == "submitted" and not submission_refs:
        errors.append("submitted builder requires submission_evidence_refs")

    related = builder_ref is not None and builder_ref in sponsor_refs
    disclosed_related = conflicts.get("builder_related_to_sponsors")
    disclosure = conflicts.get("disclosure")
    if related and disclosed_related is not True:
        errors.append("builder matching a sponsor must be disclosed as related")
    if disclosed_related is True and (not isinstance(disclosure, str) or len(disclosure.strip()) < 10):
        errors.append("related-party builder requires substantive conflict disclosure")
    if disclosed_related not in {True, False}:
        errors.append("conflicts.builder_related_to_sponsors must be boolean")

    # Award freezes acceptance criteria.
    award_state = award.get("state")
    if award_state not in {"not_awarded", "awarded"}:
        errors.append("award.state is not recognized")
    awarded_at = parse_time(award.get("awarded_at"), "award.awarded_at", errors) if award.get("awarded_at") else None
    locked_at = parse_time(acceptance.get("criteria_locked_at"), "acceptance.criteria_locked_at", errors) if acceptance.get("criteria_locked_at") else None
    if award_state == "not_awarded":
        if any(award.get(key) is not None for key in ("builder_ref", "acceptance_criteria_hash", "awarded_at")):
            errors.append("not_awarded state must not claim award details")
    else:
        if builder_state not in {"selected", "submitted"}:
            errors.append("awarded bounty requires selected/submitted builder")
        if not builder_ref or award.get("builder_ref") != builder_ref:
            errors.append("award.builder_ref must match builder.builder_ref")
        if award.get("acceptance_criteria_hash") != target.get("acceptance_criteria_hash"):
            errors.append("award acceptance criteria hash must equal frozen target hash")
        if acceptance.get("criteria_hash") != award.get("acceptance_criteria_hash"):
            errors.append("acceptance criteria hash must equal award snapshot hash")
        if awarded_at is None or locked_at is None:
            errors.append("awarded bounty requires awarded_at and criteria_locked_at")
        elif locked_at > awarded_at:
            errors.append("acceptance criteria must be locked no later than award time")

    # Acceptance and marginal unlock.
    acceptance_state = acceptance.get("state")
    if acceptance_state not in {"not_started", "failed", "passed"}:
        errors.append("acceptance.state is not recognized")
    if acceptance_state in {"failed", "passed"}:
        if not acceptance.get("test_evidence_refs"):
            errors.append(f"acceptance {acceptance_state} requires test_evidence_refs")
        if parse_time(acceptance.get("evaluated_at"), "acceptance.evaluated_at", errors) is None:
            errors.append(f"acceptance {acceptance_state} requires evaluated_at")
    elif acceptance.get("evaluated_at") is not None or acceptance.get("test_evidence_refs"):
        errors.append("not_started acceptance must not claim evaluation evidence")

    unlock_state = unlock.get("state")
    if unlock_state not in {"not_started", "failed", "verified"}:
        errors.append("unlock_verification.state is not recognized")
    incremental = unlock.get("incremental_reachable_corridors")
    if not isinstance(incremental, int) or isinstance(incremental, bool) or incremental < 0:
        errors.append("unlock_verification.incremental_reachable_corridors must be non-negative integer")
        incremental = 0
    if unlock_state == "verified":
        for key in ("baseline_snapshot_ref", "post_snapshot_ref", "evidence_ref", "verified_at"):
            if not unlock.get(key):
                errors.append(f"verified unlock requires {key}")
        if unlock.get("same_population_confirmed") is not True:
            errors.append("verified unlock requires same_population_confirmed true")
        if unlock.get("same_selection_rule_confirmed") is not True:
            errors.append("verified unlock requires same_selection_rule_confirmed true")
        if incremental < minimum_unlock:
            errors.append("verified unlock does not meet minimum incremental reachable corridors")
        if unlock.get("verified_at"):
            parse_time(unlock.get("verified_at"), "unlock_verification.verified_at", errors)

    # Lifecycle consistency.
    if status == "open":
        if award_state != "not_awarded" or builder_state not in {"none", "proposed"} or acceptance_state != "not_started" or unlock_state != "not_started":
            errors.append("open bounty must remain pre-award/pre-acceptance")
    if status == "awarded":
        if award_state != "awarded" or builder_state != "selected" or acceptance_state != "not_started" or unlock_state != "not_started":
            errors.append("awarded bounty requires selected builder and no acceptance result")
    if status == "submitted":
        if award_state != "awarded" or builder_state != "submitted" or acceptance_state == "passed" or unlock_state == "verified":
            errors.append("submitted bounty must await successful acceptance/unlock verification")
    if status in {"accepted", "closed"}:
        if award_state != "awarded" or builder_state != "submitted" or acceptance_state != "passed" or unlock_state != "verified":
            errors.append(f"{status} bounty requires awarded submitted builder, passed tests, and verified unlock")

    # Payout is a separate economic transition.
    payout_state = payout.get("state")
    if payout_state not in PAYOUT_STATES:
        errors.append("payout.state is not recognized")
    payout_amount = payout.get("amount_minor")
    if not isinstance(payout_amount, int) or isinstance(payout_amount, bool) or payout_amount < 0:
        errors.append("payout.amount_minor must be non-negative integer")
        payout_amount = 0
    if payout_amount > payout_cap:
        errors.append("payout.amount_minor cannot exceed funding payout cap")
    if payout_amount > 0:
        if payout.get("currency") != funding_currency:
            errors.append("payout.currency must equal funding.currency")
        if payout_amount > verified_total:
            errors.append("payout amount cannot exceed verified sponsor commitments")
    if payout_state == "not_earned":
        if payout_amount != 0 or any(payout.get(key) for key in ("payout_authority_ref", "payment_ref", "settlement_evidence_ref")):
            errors.append("not_earned payout must have zero amount and no execution/settlement refs")
    elif payout_state in {"earned", "external_execution_pending", "settled", "failed"}:
        if status not in {"accepted", "closed"}:
            errors.append(f"payout state {payout_state} requires accepted/closed bounty")
        if payout_amount < 1:
            errors.append(f"payout state {payout_state} requires positive amount")
    if payout_state in {"external_execution_pending", "settled"}:
        if not payout.get("payout_authority_ref"):
            errors.append(f"{payout_state} requires independent payout_authority_ref")
        if not payout.get("payment_ref"):
            errors.append(f"{payout_state} requires external payment_ref")
    if payout_state == "settled" and not payout.get("settlement_evidence_ref"):
        errors.append("settled payout requires independent settlement_evidence_ref")
    if status == "accepted" and payout_state == "not_earned":
        errors.append("accepted bounty must explicitly record earned/pending/settled/failed payout state")
    if status == "closed" and payout_state != "settled":
        errors.append("closed bounty requires externally settled payout")
    if status == "cancelled" and payout_state == "settled":
        errors.append("cancelled bounty cannot claim settled payout")

    # Overlap attribution prevents double-counting public-good value.
    overlap_policy = attribution.get("overlap_policy")
    if overlap_policy not in {"shared_population_do_not_sum", "disjoint_population", "independent_no_value_claim"}:
        errors.append("value_attribution.overlap_policy is not recognized")
    exclusive = attribution.get("claims_exclusive_incremental_value")
    if exclusive is True:
        if overlap_policy != "disjoint_population":
            errors.append("exclusive incremental value requires disjoint_population overlap policy")
        if not attribution.get("overlap_group_id") or not attribution.get("overlap_check_evidence_ref"):
            errors.append("exclusive incremental value requires overlap group and evidence")
    elif exclusive is not False:
        errors.append("claims_exclusive_incremental_value must be boolean")
    if overlap_policy == "shared_population_do_not_sum" and not attribution.get("overlap_group_id"):
        errors.append("shared_population_do_not_sum requires overlap_group_id")

    # Bounty artifacts never grant real-world authority.
    for key in ("acceptance_grants_authority", "acceptance_executes_payment", "bounty_grants_deployment_authority"):
        if authority.get(key) is not False:
            errors.append(f"authority.{key} must be false")
    for key in ("contains_credentials", "contains_payment_secrets", "contains_private_counterparty_data", "contains_confidential_deal_terms"):
        if privacy.get(key) is not False:
            errors.append(f"privacy.{key} must be false")
    if privacy.get("public_disclosure_confirmed") is not True:
        errors.append("privacy.public_disclosure_confirmed must be true")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--allow-draft", action="store_true")
    args = parser.parse_args()
    try:
        record = json.loads(args.record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate(record, allow_draft=args.allow_draft)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    assert isinstance(record, dict)
    sponsors = record.get("funding", {}).get("sponsors", [])
    verified = sum(item.get("commitment_minor", 0) for item in sponsors if isinstance(item, dict) and item.get("state") == "verified")
    print(f"interoperability bounty OK: {record.get('bounty_id')} status={record.get('status')} verified_funding={verified} payout={record.get('payout', {}).get('state')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
