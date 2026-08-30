#!/usr/bin/env python3
"""Aggregate disclosure-safe deal plans into interoperability liquidity signals."""
from __future__ import annotations

import argparse
import itertools
import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

EVIDENCE_CLASSES = {
    "synthetic_test",
    "self_declared_intent",
    "observed_commercial_demand",
    "verified_commercial_demand",
}
COMMERCIAL_CLASSES = {"observed_commercial_demand", "verified_commercial_demand"}


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include timezone")
    return parsed.astimezone(timezone.utc)


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} root must be an object")
    return value


def validate_dataset(data: dict) -> None:
    required = [
        "schema_version", "dataset_id", "generated_at", "population_definition",
        "selection_rule", "known_exclusions", "synthetic_separated", "corridors",
    ]
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError("missing dataset fields: " + ", ".join(missing))
    if data["schema_version"] != "1.0.0":
        raise ValueError("schema_version must be 1.0.0")
    if not data["population_definition"] or not data["selection_rule"]:
        raise ValueError("population_definition and selection_rule must be explicit")
    if data["synthetic_separated"] is not True:
        raise ValueError("synthetic_separated must be true")
    if not isinstance(data["known_exclusions"], list):
        raise ValueError("known_exclusions must be an array")
    if not isinstance(data["corridors"], list) or not data["corridors"]:
        raise ValueError("corridors must be a non-empty array")

    seen: set[str] = set()
    for item in data["corridors"]:
        if not isinstance(item, dict):
            raise ValueError("each corridor must be an object")
        corridor_id = item.get("corridor_id")
        if not corridor_id or corridor_id in seen:
            raise ValueError("corridor_id must be present and unique")
        seen.add(corridor_id)
        evidence_class = item.get("evidence_class")
        if evidence_class not in EVIDENCE_CLASSES:
            raise ValueError(f"unknown evidence_class for {corridor_id}")
        parse_time(item.get("observed_at", ""))
        plan = item.get("plan")
        if not isinstance(plan, dict):
            raise ValueError(f"{corridor_id}.plan must be an object")
        if plan.get("grants_authority") is not False or plan.get("action_authorized") is not False:
            raise ValueError(f"{corridor_id} deal-plan summary must not grant authority")
        transitions = plan.get("transitions")
        if not isinstance(transitions, list) or not transitions:
            raise ValueError(f"{corridor_id}.plan.transitions must be non-empty")
        for transition in transitions:
            if transition.get("status") not in {"ready", "blocked", "human_review", "unsupported"}:
                raise ValueError(f"{corridor_id} has unknown transition status")
            if not transition.get("convention"):
                raise ValueError(f"{corridor_id} transition missing convention")
        value_range = item.get("qualified_demand_value_minor_range")
        if value_range is not None:
            if evidence_class not in COMMERCIAL_CLASSES:
                raise ValueError("demand value ranges are only allowed for observed/verified commercial demand")
            if not (isinstance(value_range, list) and len(value_range) == 2 and all(isinstance(x, int) and x >= 0 for x in value_range) and value_range[0] <= value_range[1]):
                raise ValueError("qualified_demand_value_minor_range must be [low, high] non-negative integers")
            if not item.get("currency"):
                raise ValueError("currency is required with demand value range")


def transition_solved_by(transition: dict, conventions: set[str], blocker_ids: set[str]) -> bool:
    if transition["status"] == "ready":
        return True
    convention = transition["convention"]
    if convention in conventions and transition["status"] in {"human_review", "unsupported"}:
        return True
    reasons = " ".join(transition.get("reasons", []))
    if transition["status"] == "blocked" and "compatibility handshake" in reasons and blocker_ids and blocker_ids.issubset(conventions):
        return True
    return False


def state_after(plan: dict, conventions: set[str]) -> tuple[bool, bool, int, int, int]:
    blockers = {
        item.get("convention_id")
        for item in plan.get("compatibility", {}).get("blockers", [])
        if item.get("convention_id")
    }
    statuses = []
    for transition in plan["transitions"]:
        statuses.append("ready" if transition_solved_by(transition, conventions, blockers) else transition["status"])
    reachable = not any(status in {"blocked", "unsupported"} for status in statuses)
    structured = reachable and all(status == "ready" for status in statuses)
    return (
        reachable,
        structured,
        sum(status == "human_review" for status in statuses),
        sum(status == "blocked" for status in statuses),
        sum(status == "unsupported" for status in statuses),
    )


def candidate_conventions(plan: dict) -> set[str]:
    result = {
        transition["convention"]
        for transition in plan["transitions"]
        if transition["status"] in {"human_review", "unsupported"}
    }
    result.update(
        item.get("convention_id")
        for item in plan.get("compatibility", {}).get("blockers", [])
        if item.get("convention_id")
    )
    return result


def summarize(items: list[dict], implementations: set[str] | None = None) -> dict:
    implementations = implementations or set()
    states = [state_after(item["plan"], implementations) for item in items]
    transition_count = sum(len(item["plan"]["transitions"]) for item in items)
    minimum_work = [
        sum(1 for transition in item["plan"]["transitions"] if not transition_solved_by(
            transition,
            implementations,
            {b.get("convention_id") for b in item["plan"].get("compatibility", {}).get("blockers", []) if b.get("convention_id")},
        ))
        for item in items
    ]
    return {
        "sample_size": len(items),
        "reachable_counterparty_rate": round(sum(s[0] for s in states) / len(states), 6),
        "structured_corridor_rate": round(sum(s[1] for s in states) / len(states), 6),
        "manual_handoffs_per_deal": round(sum(s[2] for s in states) / len(states), 6),
        "blocked_transition_rate": round(sum(s[3] for s in states) / transition_count, 6),
        "unsupported_transition_rate": round(sum(s[4] for s in states) / transition_count, 6),
        "median_minimum_work_items": statistics.median(minimum_work),
    }


def demand_range(items: list[dict], unlocked_ids: set[str]) -> tuple[str | None, list[int] | None]:
    chosen = [item for item in items if item["corridor_id"] in unlocked_ids and item.get("qualified_demand_value_minor_range")]
    if not chosen:
        return None, None
    currencies = {item["currency"] for item in chosen}
    if len(currencies) != 1:
        return None, None
    return next(iter(currencies)), [
        sum(item["qualified_demand_value_minor_range"][0] for item in chosen),
        sum(item["qualified_demand_value_minor_range"][1] for item in chosen),
    ]


def analyze_cohort(items: list[dict], min_sample: int) -> dict:
    baseline = summarize(items)
    candidates = sorted(set().union(*(candidate_conventions(item["plan"]) for item in items)))
    single = []
    baseline_reachable = {item["corridor_id"] for item in items if state_after(item["plan"], set())[0]}
    for convention in candidates:
        implementations = {convention}
        after = summarize(items, implementations)
        unlocked = {
            item["corridor_id"] for item in items
            if item["corridor_id"] not in baseline_reachable and state_after(item["plan"], implementations)[0]
        }
        currency, value = demand_range(items, unlocked)
        single.append({
            "convention": convention,
            "incremental_reachable_corridors": len(unlocked),
            "incremental_reachable_rate": round(len(unlocked) / len(items), 6),
            "reachable_counterparty_rate_after": after["reachable_counterparty_rate"],
            "manual_handoffs_removed_per_deal": round(baseline["manual_handoffs_per_deal"] - after["manual_handoffs_per_deal"], 6),
            "unlocked_corridor_ids": sorted(unlocked),
            "unlocked_qualified_demand_currency": currency,
            "unlocked_qualified_demand_value_minor_range": value,
        })
    single.sort(key=lambda x: (-x["incremental_reachable_corridors"], x["convention"]))

    pairs = []
    for left, right in itertools.combinations(candidates, 2):
        implementations = {left, right}
        unlocked = {
            item["corridor_id"] for item in items
            if item["corridor_id"] not in baseline_reachable and state_after(item["plan"], implementations)[0]
        }
        best_single = max(
            (next((x["incremental_reachable_corridors"] for x in single if x["convention"] == c), 0) for c in implementations),
            default=0,
        )
        synergy = len(unlocked) - best_single
        if unlocked and synergy > 0:
            pairs.append({"conventions": [left, right], "incremental_reachable_corridors": len(unlocked), "complementarity_gain_over_best_single": synergy, "unlocked_corridor_ids": sorted(unlocked)})
    pairs.sort(key=lambda x: (-x["complementarity_gain_over_best_single"], -x["incremental_reachable_corridors"], x["conventions"]))
    return {"publishable": len(items) >= min_sample, "baseline": baseline, "convention_unlocks": single, "complementary_pairs": pairs}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--min-sample", type=int, default=3)
    parser.add_argument("--max-age-days", type=int, default=90)
    parser.add_argument("--as-of", default=None, help="RFC3339 evaluation time; defaults to now")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        data = load(args.dataset)
        validate_dataset(data)
        as_of = parse_time(args.as_of) if args.as_of else datetime.now(timezone.utc)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    cutoff = as_of - timedelta(days=args.max_age_days)
    fresh, stale = [], []
    for item in data["corridors"]:
        (fresh if parse_time(item["observed_at"]) >= cutoff else stale).append(item)
    cohorts: dict[str, list[dict]] = defaultdict(list)
    for item in fresh:
        cohorts[item["evidence_class"]].append(item)
    report = {
        "schema_version": "1.0.0",
        "dataset_id": data["dataset_id"],
        "as_of": as_of.isoformat().replace("+00:00", "Z"),
        "population_definition": data["population_definition"],
        "selection_rule": data["selection_rule"],
        "known_exclusions": data["known_exclusions"],
        "included_corridors": len(fresh),
        "stale_corridors_excluded": len(stale),
        "evidence_classes_kept_separate": True,
        "authority_inference": False,
        "cohorts": {key: analyze_cohort(items, args.min_sample) for key, items in sorted(cohorts.items())},
        "interpretation": "Reachable means no blocked or unsupported transition after the modeled interoperability change. It does not mean authorized, contracted, paid, delivered, or accepted.",
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
