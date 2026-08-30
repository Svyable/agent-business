#!/usr/bin/env python3
"""Validate a pooled agent-demand/group-buy lot using Python's standard library."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

VALID_STATUS = {
    "draft", "collecting", "threshold_met", "offer_received", "offer_selected",
    "allocating", "allocated", "closed", "cancelled", "expired",
}
VALID_QUALITY = {
    "synthetic_test", "exploratory_research", "self_declared_intent", "verified_commercial",
}
VALID_OPT_IN = {"interested", "committed", "accepted", "withdrawn", "expired"}
COMMITTED = {"committed", "accepted"}
OFFER_ACTIVE = {"received", "selected"}
BASELINE_TYPES = {"prior_individual_quote", "published_current_price", "current_market_quote"}


def parse_time(value: object, field: str, errors: list[str]) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        errors.append(f"{field} must be an RFC3339 string or null")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{field} is not valid RFC3339")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{field} must include timezone")
        return None
    return parsed.astimezone(timezone.utc)


def require_dict(record: dict, key: str, errors: list[str]) -> dict:
    value = record.get(key)
    if not isinstance(value, dict):
        errors.append(f"{key} must be an object")
        return {}
    return value


def prorata_integer(total: int, weights: dict[str, int]) -> dict[str, int]:
    """Largest-remainder integer allocation with participant-id tie break."""
    if total < 0 or not weights or any(weight < 0 for weight in weights.values()):
        raise ValueError("invalid prorata inputs")
    weight_sum = sum(weights.values())
    if weight_sum <= 0:
        return {key: 0 for key in weights}
    result = {key: total * weight // weight_sum for key, weight in weights.items()}
    remainder = total - sum(result.values())
    ranked = sorted(weights, key=lambda key: (-(total * weights[key] % weight_sum), key))
    for key in ranked[:remainder]:
        result[key] += 1
    return result


def tier_price(tiers: list[dict], quantity: int) -> int | None:
    for tier in tiers:
        minimum = tier.get("min_quantity")
        maximum = tier.get("max_quantity")
        if isinstance(minimum, int) and quantity >= minimum and (maximum is None or quantity <= maximum):
            price = tier.get("unit_price_minor")
            return price if isinstance(price, int) else None
    return None


def validate_record(record: object, allow_draft: bool = False) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["root must be a JSON object"]

    required = [
        "schema_version", "pool_id", "pool_version", "updated_at", "status",
        "normalized_demand", "participants", "thresholds", "seller_offer",
        "allocation", "economics", "authority_boundaries", "disclosure",
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
        errors.append("draft pool requires --allow-draft")

    updated_at = parse_time(record.get("updated_at"), "updated_at", errors)
    demand = require_dict(record, "normalized_demand", errors)
    thresholds = require_dict(record, "thresholds", errors)
    offer = require_dict(record, "seller_offer", errors)
    allocation = require_dict(record, "allocation", errors)
    economics = require_dict(record, "economics", errors)
    boundaries = require_dict(record, "authority_boundaries", errors)
    disclosure = require_dict(record, "disclosure", errors)

    currency = demand.get("currency")
    if not isinstance(currency, str) or not currency:
        errors.append("normalized_demand.currency must be non-empty")
    if not isinstance(demand.get("scope_hash"), str) or not demand.get("scope_hash"):
        errors.append("normalized_demand.scope_hash must be non-empty")
    hard_requirements = demand.get("hard_requirements")
    if not isinstance(hard_requirements, list) or not hard_requirements:
        errors.append("normalized_demand.hard_requirements must be non-empty")
    else:
        ids = [item.get("id") for item in hard_requirements if isinstance(item, dict)]
        if len(ids) != len(hard_requirements) or any(not item for item in ids):
            errors.append("every hard requirement requires an id")
        if len(ids) != len(set(ids)):
            errors.append("hard requirement ids must be unique")
    if not isinstance(demand.get("acceptance_criteria"), list) or not demand.get("acceptance_criteria"):
        errors.append("normalized_demand.acceptance_criteria must be non-empty")

    participants = record.get("participants")
    if not isinstance(participants, list) or len(participants) < 2:
        errors.append("participants must contain at least two buyers")
        participants = []

    by_id: dict[str, dict] = {}
    rfq_ids: set[str] = set()
    related_party_present = False
    related_party_unknown = False
    eligible_commitments: list[dict] = []
    participant_times: dict[str, dict[str, datetime | None]] = {}

    for index, participant in enumerate(participants):
        prefix = f"participants[{index}]"
        if not isinstance(participant, dict):
            errors.append(f"{prefix} must be an object")
            continue
        participant_id = participant.get("participant_id")
        if not isinstance(participant_id, str) or not participant_id:
            errors.append(f"{prefix}.participant_id must be non-empty")
            continue
        if participant_id in by_id:
            errors.append("participant_id must be unique")
        by_id[participant_id] = participant

        rfq = participant.get("rfq_ref")
        if not isinstance(rfq, dict):
            errors.append(f"{prefix}.rfq_ref must be an object")
            rfq = {}
        request_id = rfq.get("request_id")
        if not isinstance(request_id, str) or not request_id:
            errors.append(f"{prefix}.rfq_ref.request_id must be non-empty")
        elif request_id in rfq_ids:
            errors.append("one RFQ cannot be counted twice in the same pool")
        else:
            rfq_ids.add(request_id)
        for field in ("request_version", "request_digest"):
            if not isinstance(rfq.get(field), str) or not rfq.get(field):
                errors.append(f"{prefix}.rfq_ref.{field} must be non-empty")

        quality = participant.get("demand_quality")
        opt_in = participant.get("opt_in_state")
        if quality not in VALID_QUALITY:
            errors.append(f"{prefix}.demand_quality is not recognized")
        if opt_in not in VALID_OPT_IN:
            errors.append(f"{prefix}.opt_in_state is not recognized")

        qmin, qmax, committed = participant.get("quantity_min"), participant.get("quantity_max"), participant.get("committed_quantity")
        if not isinstance(qmin, int) or qmin <= 0:
            errors.append(f"{prefix}.quantity_min must be positive")
        if not isinstance(qmax, int) or qmax <= 0:
            errors.append(f"{prefix}.quantity_max must be positive")
        if isinstance(qmin, int) and isinstance(qmax, int) and qmin > qmax:
            errors.append(f"{prefix}.quantity_min cannot exceed quantity_max")
        if not isinstance(committed, int) or committed < 0:
            errors.append(f"{prefix}.committed_quantity must be a non-negative integer")
        elif isinstance(qmax, int) and committed > qmax:
            errors.append(f"{prefix}.committed_quantity exceeds original quantity_max")

        valid_until = parse_time(participant.get("valid_until"), f"{prefix}.valid_until", errors)
        committed_at = parse_time(participant.get("committed_at"), f"{prefix}.committed_at", errors)
        accepted_at = parse_time(participant.get("accepted_offer_at"), f"{prefix}.accepted_offer_at", errors)
        participant_times[participant_id] = {"valid_until": valid_until, "committed_at": committed_at, "accepted_at": accepted_at}
        if updated_at and valid_until and valid_until <= updated_at and opt_in in {"interested", "committed", "accepted"}:
            errors.append(f"{prefix} active opt-in is expired at updated_at")

        authority = participant.get("authority")
        if not isinstance(authority, dict):
            errors.append(f"{prefix}.authority must be an object")
            authority = {}
        authority_expiry = parse_time(authority.get("expires_at"), f"{prefix}.authority.expires_at", errors)
        participant_times[participant_id]["authority_expiry"] = authority_expiry

        related = participant.get("related_party_to_seller")
        if related == "yes":
            related_party_present = True
        elif related == "unknown":
            related_party_unknown = True
        elif related != "no":
            errors.append(f"{prefix}.related_party_to_seller is not recognized")

        if opt_in in COMMITTED:
            if quality != "verified_commercial":
                errors.append(f"{prefix} committed/accepted volume requires verified_commercial demand")
            if not isinstance(committed, int) or not isinstance(qmin, int) or committed < qmin:
                errors.append(f"{prefix} committed volume must meet quantity_min")
            max_unit = participant.get("max_unit_price_minor")
            budget_cap = participant.get("budget_cap_minor")
            if not isinstance(max_unit, int) or max_unit <= 0:
                errors.append(f"{prefix} committed volume requires positive max_unit_price_minor")
            if not isinstance(budget_cap, int) or budget_cap <= 0:
                errors.append(f"{prefix} committed volume requires positive budget_cap_minor")
            if isinstance(committed, int) and isinstance(max_unit, int) and isinstance(budget_cap, int) and budget_cap < committed * max_unit:
                errors.append(f"{prefix}.budget_cap_minor cannot fund committed quantity at max unit price")
            if authority.get("state") != "current":
                errors.append(f"{prefix} committed volume requires current independent authority")
            if not authority.get("evidence_ref"):
                errors.append(f"{prefix} current authority requires evidence_ref")
            if authority.get("currency") != currency:
                errors.append(f"{prefix} authority currency must match pooled currency")
            auth_max = authority.get("max_total_minor")
            if not isinstance(auth_max, int) or auth_max <= 0:
                errors.append(f"{prefix} current authority requires positive max_total_minor")
            elif isinstance(budget_cap, int) and auth_max < budget_cap:
                errors.append(f"{prefix} authority max_total_minor is below buyer budget cap")
            if updated_at and authority_expiry and authority_expiry <= updated_at:
                errors.append(f"{prefix} current authority is expired at updated_at")
            if committed_at is None:
                errors.append(f"{prefix} committed volume requires committed_at")
            elif updated_at and committed_at > updated_at:
                errors.append(f"{prefix}.committed_at cannot be in the future")
            eligible_commitments.append(participant)
        elif isinstance(committed, int) and committed != 0:
            errors.append(f"{prefix} non-committed buyer must have committed_quantity=0")

        if opt_in == "accepted" and accepted_at is None:
            errors.append(f"{prefix} accepted buyer requires accepted_offer_at")

    computed_buyers = len(eligible_commitments)
    computed_quantity = sum(p["committed_quantity"] for p in eligible_commitments if isinstance(p.get("committed_quantity"), int))
    computed_budget = sum(p["budget_cap_minor"] for p in eligible_commitments if isinstance(p.get("budget_cap_minor"), int))
    expected_values = {
        "computed_committed_buyers": computed_buyers,
        "computed_committed_quantity": computed_quantity,
        "computed_committed_budget_minor": computed_budget,
    }
    for field, expected in expected_values.items():
        if thresholds.get(field) != expected:
            errors.append(f"thresholds.{field} must equal recomputed value {expected}")

    min_buyers = thresholds.get("min_committed_buyers")
    min_quantity = thresholds.get("min_committed_quantity")
    min_budget = thresholds.get("min_committed_budget_minor")
    for field, value in (("min_committed_buyers", min_buyers), ("min_committed_quantity", min_quantity)):
        if not isinstance(value, int) or value <= 0:
            errors.append(f"thresholds.{field} must be positive")
    if min_budget is not None and (not isinstance(min_budget, int) or min_budget <= 0):
        errors.append("thresholds.min_committed_budget_minor must be positive or null")
    threshold_met = (
        isinstance(min_buyers, int) and isinstance(min_quantity, int)
        and computed_buyers >= min_buyers and computed_quantity >= min_quantity
        and (min_budget is None or computed_budget >= min_budget)
    )
    if thresholds.get("state") != ("met" if threshold_met else "not_met"):
        errors.append("thresholds.state does not match recomputed threshold state")
    parse_time(thresholds.get("evaluated_at"), "thresholds.evaluated_at", errors)

    if status in {"threshold_met", "offer_received", "offer_selected", "allocating", "allocated", "closed"} and not threshold_met:
        errors.append(f"{status} state requires thresholds.state=met")

    offer_status = offer.get("status")
    received_at = parse_time(offer.get("received_at"), "seller_offer.received_at", errors)
    selected_at = parse_time(offer.get("selected_at"), "seller_offer.selected_at", errors)
    offer_valid_until = parse_time(offer.get("valid_until"), "seller_offer.valid_until", errors)
    tiers = offer.get("volume_tiers")
    if offer_status == "none":
        for field in ("offer_id", "seller_listing_ref", "seller_listing_version", "received_at", "selected_at", "valid_until", "capacity_ceiling"):
            if offer.get(field) is not None:
                errors.append(f"seller_offer.{field} must be null when status=none")
        if tiers != []:
            errors.append("seller_offer.volume_tiers must be empty when status=none")
    elif offer_status in {"received", "selected", "withdrawn", "expired"}:
        for field in ("offer_id", "seller_listing_ref", "seller_listing_version"):
            if not isinstance(offer.get(field), str) or not offer.get(field):
                errors.append(f"seller_offer.{field} is required when an offer exists")
        capacity = offer.get("capacity_ceiling")
        if not isinstance(capacity, int) or capacity <= 0:
            errors.append("seller_offer.capacity_ceiling must be positive when an offer exists")
        if received_at is None or offer_valid_until is None:
            errors.append("seller offer requires received_at and valid_until")
        elif offer_valid_until <= received_at:
            errors.append("seller_offer.valid_until must be after received_at")
        if offer_status == "selected":
            if not threshold_met:
                errors.append("seller offer cannot be selected before pool threshold is met")
            if selected_at is None:
                errors.append("selected seller offer requires selected_at")
            elif received_at and selected_at < received_at:
                errors.append("seller_offer.selected_at cannot precede received_at")
            elif offer_valid_until and selected_at >= offer_valid_until:
                errors.append("seller offer cannot be selected after expiry")
        elif selected_at is not None and offer_status != "withdrawn":
            errors.append("seller_offer.selected_at requires status=selected or historical withdrawn state")

        if not isinstance(tiers, list) or not tiers:
            errors.append("seller offer requires volume_tiers")
            tiers = []
        previous_max = None
        previous_price = None
        for index, tier in enumerate(tiers):
            prefix = f"seller_offer.volume_tiers[{index}]"
            if not isinstance(tier, dict):
                errors.append(f"{prefix} must be an object")
                continue
            minimum, maximum, price = tier.get("min_quantity"), tier.get("max_quantity"), tier.get("unit_price_minor")
            if not isinstance(minimum, int) or minimum <= 0:
                errors.append(f"{prefix}.min_quantity must be positive")
            if maximum is not None and (not isinstance(maximum, int) or not isinstance(minimum, int) or maximum < minimum):
                errors.append(f"{prefix}.max_quantity must be null or >= min_quantity")
            if not isinstance(price, int) or price < 0:
                errors.append(f"{prefix}.unit_price_minor must be non-negative")
            if previous_max is not None and isinstance(minimum, int) and minimum != previous_max + 1:
                errors.append("seller volume tiers must be contiguous and non-overlapping")
            if previous_max is None and index > 0:
                errors.append("only the final seller volume tier may have max_quantity=null")
            if previous_price is not None and isinstance(price, int) and price > previous_price:
                errors.append("seller unit price must not increase at higher volume")
            previous_max = maximum
            previous_price = price
        if isinstance(capacity, int) and tiers and tier_price(tiers, capacity) is None:
            errors.append("seller capacity_ceiling must be covered by a volume tier")
    else:
        errors.append("seller_offer.status is not recognized")

    if status == "offer_received" and offer_status not in {"received", "selected"}:
        errors.append("offer_received state requires a seller offer")
    if status in {"offer_selected", "allocating", "allocated", "closed"} and offer_status != "selected":
        errors.append(f"{status} state requires seller_offer.status=selected")

    if related_party_present and offer_status in OFFER_ACTIVE and offer.get("related_party_disclosure") != "disclosed":
        errors.append("related-party buyer/seller relationship must be disclosed")
    if (related_party_present or related_party_unknown) and economics.get("market_claims_allowed") is True:
        errors.append("market claims require all buyer/seller related-party states to be no")

    accepted_participants = {
        p["participant_id"]: p for p in participants
        if isinstance(p, dict) and p.get("opt_in_state") == "accepted" and p.get("participant_id")
    }
    if selected_at:
        for participant_id in accepted_participants:
            accepted_at = participant_times.get(participant_id, {}).get("accepted_at")
            if accepted_at and accepted_at < selected_at:
                errors.append(f"{participant_id} accepted the pooled offer before it was selected")
            if accepted_at and offer_valid_until and accepted_at >= offer_valid_until:
                errors.append(f"{participant_id} accepted the pooled offer after it expired")

    allocation_state = allocation.get("state")
    allocations = allocation.get("allocations")
    if not isinstance(allocations, list):
        errors.append("allocation.allocations must be an array")
        allocations = []
    if allocation.get("policy") != "pro_rata_committed_quantity":
        errors.append("allocation.policy must be pro_rata_committed_quantity")
    if allocation_state == "not_started":
        if allocations:
            errors.append("not_started allocation must not contain allocations")
        if allocation.get("allocated_total_quantity") != 0:
            errors.append("not_started allocation must have allocated_total_quantity=0")
        if allocation.get("selected_unit_price_minor") is not None:
            errors.append("not_started allocation must not select a unit price")
    elif allocation_state in {"provisional", "finalized", "cancelled"}:
        if allocation_state == "finalized":
            if offer_status != "selected" or not threshold_met:
                errors.append("finalized allocation requires selected offer and met threshold")
            if not allocation.get("finalized_at"):
                errors.append("finalized allocation requires finalized_at")
            capacity = offer.get("capacity_ceiling")
            total_accepted = sum(p["committed_quantity"] for p in accepted_participants.values())
            if not accepted_participants:
                errors.append("finalized allocation requires independently accepted buyers")
            target_total = min(total_accepted, capacity) if isinstance(capacity, int) else total_accepted
            expected_quantities = prorata_integer(
                target_total,
                {pid: p["committed_quantity"] for pid, p in accepted_participants.items()},
            ) if accepted_participants else {}
            expected_quantities = {pid: qty for pid, qty in expected_quantities.items() if qty > 0}
            actual_by_id: dict[str, dict] = {}
            for item in allocations:
                if not isinstance(item, dict):
                    errors.append("every allocation entry must be an object")
                    continue
                pid = item.get("participant_id")
                if pid in actual_by_id:
                    errors.append("participant cannot appear twice in allocation")
                actual_by_id[pid] = item
                if pid not in accepted_participants:
                    errors.append("allocation cannot include a buyer that did not accept the pooled offer")
            if set(actual_by_id) != set(expected_quantities):
                errors.append("final allocation participants do not match deterministic positive-share allocation")
            for pid, expected_qty in expected_quantities.items():
                item = actual_by_id.get(pid, {})
                if item.get("allocated_quantity") != expected_qty:
                    errors.append(f"{pid} allocated quantity does not match deterministic pro-rata allocation")
                if expected_qty > accepted_participants[pid]["committed_quantity"]:
                    errors.append(f"{pid} allocation exceeds buyer committed quantity")

            actual_total = sum(item.get("allocated_quantity", 0) for item in allocations if isinstance(item, dict) and isinstance(item.get("allocated_quantity"), int))
            if allocation.get("allocated_total_quantity") != actual_total:
                errors.append("allocation.allocated_total_quantity must equal allocation sum")
            if actual_total != target_total:
                errors.append("final allocation total does not match accepted demand/capacity target")
            selected_price = tier_price(tiers if isinstance(tiers, list) else [], actual_total)
            if selected_price is None:
                errors.append("final allocation quantity is not covered by seller volume tiers")
            if allocation.get("selected_unit_price_minor") != selected_price:
                errors.append("allocation.selected_unit_price_minor does not match selected volume tier")

            setup_cost = offer.get("setup_cost_minor")
            if not isinstance(setup_cost, int) or setup_cost < 0:
                errors.append("seller_offer.setup_cost_minor must be non-negative")
                setup_cost = 0
            setup_shares = prorata_integer(setup_cost, expected_quantities) if expected_quantities else {}
            for pid, item in actual_by_id.items():
                qty = item.get("allocated_quantity")
                if item.get("unit_price_minor") != selected_price:
                    errors.append(f"{pid} allocation unit price differs from pool tier price")
                if item.get("setup_share_minor") != setup_shares.get(pid):
                    errors.append(f"{pid} setup share does not match pro-rata allocated quantity")
                expected_total = qty * selected_price + setup_shares.get(pid, 0) if isinstance(qty, int) and isinstance(selected_price, int) else None
                if item.get("total_price_minor") != expected_total:
                    errors.append(f"{pid} total price does not reconcile")
                if item.get("payment_authorized") is not False:
                    errors.append(f"{pid} pool allocation must never authorize payment")
                if not item.get("buyer_deal_plan_ref"):
                    errors.append(f"{pid} final allocation requires per-buyer deal plan reference")
                participant = accepted_participants.get(pid, {})
                if isinstance(selected_price, int) and isinstance(participant.get("max_unit_price_minor"), int) and selected_price > participant["max_unit_price_minor"]:
                    errors.append(f"{pid} pooled unit price exceeds buyer max unit price")
                if isinstance(expected_total, int) and isinstance(participant.get("budget_cap_minor"), int) and expected_total > participant["budget_cap_minor"]:
                    errors.append(f"{pid} pooled total exceeds buyer budget cap")
                authority = participant.get("authority", {})
                if authority.get("state") != "current":
                    errors.append(f"{pid} final allocation requires current independent authority")
                if isinstance(expected_total, int) and isinstance(authority.get("max_total_minor"), int) and expected_total > authority["max_total_minor"]:
                    errors.append(f"{pid} pooled total exceeds buyer authority")
    else:
        errors.append("allocation.state is not recognized")

    if status == "allocated" and allocation_state != "finalized":
        errors.append("allocated status requires allocation.state=finalized")

    if economics.get("baseline_policy") != "comparable_individual_evidence_only":
        errors.append("economics.baseline_policy must remain comparable_individual_evidence_only")
    savings = economics.get("buyer_savings")
    if not isinstance(savings, list):
        errors.append("economics.buyer_savings must be an array")
        savings = []
    allocation_lookup = {item.get("participant_id"): item for item in allocations if isinstance(item, dict)}
    for index, item in enumerate(savings):
        prefix = f"economics.buyer_savings[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        pid = item.get("participant_id")
        if pid not in allocation_lookup:
            errors.append(f"{prefix} must reference an allocated participant")
        if item.get("baseline_source_type") not in BASELINE_TYPES:
            errors.append(f"{prefix}.baseline_source_type must be comparable evidence, not a fabricated list price")
        if not item.get("baseline_source_ref"):
            errors.append(f"{prefix}.baseline_source_ref is required")
        if item.get("comparable_scope_hash") != demand.get("scope_hash"):
            errors.append(f"{prefix}.comparable_scope_hash must match normalized demand scope")
        if item.get("currency") != currency:
            errors.append(f"{prefix}.currency must match pooled currency")
        baseline_total, pooled_total, savings_minor = item.get("baseline_total_minor"), item.get("pooled_total_minor"), item.get("savings_minor")
        if not all(isinstance(value, int) for value in (baseline_total, pooled_total, savings_minor)):
            errors.append(f"{prefix} totals and savings must be integers")
        else:
            if pooled_total != allocation_lookup.get(pid, {}).get("total_price_minor"):
                errors.append(f"{prefix}.pooled_total_minor must equal actual pooled allocation total")
            if savings_minor != baseline_total - pooled_total:
                errors.append(f"{prefix}.savings_minor must equal baseline_total_minor - pooled_total_minor")

    concentration = economics.get("supplier_concentration")
    if not isinstance(concentration, dict):
        errors.append("economics.supplier_concentration must be an object")
    else:
        risk = concentration.get("risk")
        if risk not in {"unknown", "low", "medium", "high"}:
            errors.append("supplier concentration risk is not recognized")
        if offer_status == "selected" and concentration.get("single_supplier") is not True:
            errors.append("selected pooled seller offer must disclose single_supplier=true")
        if risk == "high" and not concentration.get("substitution_plan"):
            errors.append("high supplier concentration requires a substitution plan")

    for field in (
        "shared_wallet", "shared_credentials", "shared_payment_authority",
        "shared_contract_authority", "pool_award_grants_buyer_authority",
        "pool_allocation_executes_payment",
    ):
        if boundaries.get(field) is not False:
            errors.append(f"authority_boundaries.{field} must be false")

    for field in (
        "contains_secrets", "contains_credentials", "contains_private_buyer_identity",
        "contains_confidential_rfq_content", "contains_hidden_budget_data",
    ):
        if disclosure.get(field) is not False:
            errors.append(f"disclosure.{field} must be false")
    if disclosure.get("evidence_classes_kept_separate") is not True:
        errors.append("disclosure.evidence_classes_kept_separate must be true")
    if disclosure.get("aggregate_publication_allowed") is True:
        if computed_buyers < 3:
            errors.append("aggregate publication requires at least three verified committed buyers")
        if related_party_present or related_party_unknown:
            errors.append("aggregate publication requires resolved non-related buyer/seller relationships")

    if economics.get("market_claims_allowed") is True:
        if computed_buyers < 3:
            errors.append("market claims require at least three verified committed buyers")
        if disclosure.get("evidence_classes_kept_separate") is not True:
            errors.append("market claims require evidence-class separation")

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
