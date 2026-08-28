#!/usr/bin/env python3
"""Validate and calculate fully loaded economics for agentic workflow alternatives."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ANALYSIS = ROOT / "templates" / "WORKFLOW_ROI_ANALYSIS.json"

TOP_LEVEL_REQUIRED = {
    "schema_version",
    "analysis_id",
    "updated_at",
    "status",
    "currency",
    "outcome",
    "baseline_scenario_id",
    "evidence",
    "assumptions",
    "scenarios",
    "decision",
}
STATUSES = {"draft", "candidate", "decision_ready", "retired"}
CLASSIFICATIONS = {"observed_fact", "self_reported", "estimate", "benchmark"}
EVIDENCE_STATUSES = {"current", "stale", "disputed", "superseded"}
SENSITIVE_KEYS = {
    "password",
    "secret",
    "client_secret",
    "api_key",
    "access_token",
    "refresh_token",
    "authorization",
    "raw_prompt",
    "prompt_content",
    "card_number",
    "cvv",
    "payment_credential",
}
PLACEHOLDER_MARKERS = (
    "replace with",
    "draft starter",
    "draft example",
    "illustrative",
    "placeholder",
)
ESTIMATE_KEYS = {"value", "low", "high", "classification", "basis_ids"}
ATTEMPT_COST_FIELDS = (
    "inference_minor",
    "context_retrieval_minor",
    "tools_api_minor",
    "data_minor",
    "compute_storage_minor",
    "other_minor",
)
FIXED_COST_FIELDS = (
    "infrastructure_minor",
    "orchestration_maintenance_minor",
    "eval_security_compliance_minor",
    "other_minor",
)


def fail(message: str) -> None:
    raise SystemExit(f"workflow-roi validation failed: {message}")


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot parse {path}: {exc}")
    if not isinstance(data, dict):
        fail("analysis must be a JSON object")
    return data


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
            if normalized in SENSITIVE_KEYS:
                fail(f"prohibited sensitive field: {path}.{key}")
            scan_sensitive(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_sensitive(child, f"{path}[{index}]")


def unique_objects(items: object, label: str, *, require_nonempty: bool = False) -> dict[str, dict]:
    if not isinstance(items, list):
        fail(f"{label} must be a list")
    if require_nonempty and not items:
        fail(f"{label} must not be empty")
    result: dict[str, dict] = {}
    for item in items:
        if not isinstance(item, dict):
            fail(f"{label} entries must be objects")
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id.strip():
            fail(f"{label} entries need non-empty ids")
        if item_id in result:
            fail(f"duplicate {label} id: {item_id}")
        result[item_id] = item
    return result


def iter_estimates(value: object, path: str = "$"):
    if isinstance(value, dict):
        if ESTIMATE_KEYS.issubset(value.keys()):
            yield path, value
        for key, child in value.items():
            yield from iter_estimates(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_estimates(child, f"{path}[{index}]")


def validate_estimate(path: str, estimate: dict, valid_basis: set[str], status: str) -> None:
    for field in ("value", "low", "high"):
        number = estimate.get(field)
        if not isinstance(number, (int, float)) or isinstance(number, bool) or not math.isfinite(float(number)):
            fail(f"{path}.{field} must be a finite number")
    low = float(estimate["low"])
    value = float(estimate["value"])
    high = float(estimate["high"])
    if low > value or value > high:
        fail(f"{path} must satisfy low <= value <= high")
    if low < 0:
        fail(f"{path} cannot contain negative economic inputs")
    classification = estimate.get("classification")
    if classification not in CLASSIFICATIONS:
        fail(f"{path}.classification is invalid")
    basis_ids = estimate.get("basis_ids")
    if not isinstance(basis_ids, list) or any(not isinstance(item, str) or not item for item in basis_ids):
        fail(f"{path}.basis_ids must be a list of non-empty ids")
    if len(set(basis_ids)) != len(basis_ids):
        fail(f"{path}.basis_ids contains duplicates")
    unknown = sorted(set(basis_ids) - valid_basis)
    if unknown:
        fail(f"{path} references unknown basis ids: {', '.join(unknown)}")
    if status in {"candidate", "decision_ready"} and not basis_ids:
        fail(f"{path} requires provenance basis for {status} status")
    if classification == "observed_fact" and not (low == value == high):
        fail(f"{path} classified observed_fact must use an exact low/value/high")
    if path.endswith("success_rate") or path.endswith("review_rate"):
        if high > 1:
            fail(f"{path} must stay between 0 and 1")
    if path.endswith("average_attempts_per_request") and low < 1:
        fail(f"{path} must be at least 1")
    if "_minor" in path:
        for field in ("value", "low", "high"):
            if not float(estimate[field]).is_integer():
                fail(f"{path}.{field} must be integer minor currency units")


def contains_placeholder(record: dict) -> str | None:
    text = json.dumps(record, sort_keys=True).lower()
    for marker in PLACEHOLDER_MARKERS:
        if marker in text:
            return marker
    return None


def validate(record: dict) -> None:
    missing = sorted(TOP_LEVEL_REQUIRED - set(record))
    if missing:
        fail(f"missing required fields: {', '.join(missing)}")
    if record.get("schema_version") != "1.0.0":
        fail("schema_version must be 1.0.0")
    status = record.get("status")
    if status not in STATUSES:
        fail("status is invalid")
    currency = record.get("currency")
    if not isinstance(currency, str) or len(currency) != 3 or not currency.isalpha() or currency.upper() != currency:
        fail("currency must be an uppercase three-letter code")
    parse_time(record.get("updated_at"), "updated_at")
    scan_sensitive(record)

    outcome = record.get("outcome")
    if not isinstance(outcome, dict):
        fail("outcome must be an object")
    for field in ("name", "success_event", "measurement_window", "customer_value_notes"):
        if not isinstance(outcome.get(field), str) or not outcome[field].strip():
            fail(f"outcome.{field} must be a non-empty string")

    evidence = unique_objects(record.get("evidence"), "evidence")
    for evidence_id, item in evidence.items():
        if item.get("status") not in EVIDENCE_STATUSES:
            fail(f"evidence {evidence_id} has invalid status")
        parse_time(item.get("observed_at"), f"evidence {evidence_id}.observed_at")
        url = item.get("public_url")
        if url is not None:
            if not isinstance(url, str):
                fail(f"evidence {evidence_id}.public_url must be a string or null")
            parsed = urlparse(url)
            if parsed.scheme != "https" or not parsed.netloc:
                fail(f"evidence {evidence_id}.public_url must be an absolute https URL")

    assumptions = unique_objects(record.get("assumptions"), "assumptions")
    for assumption_id, item in assumptions.items():
        for field in ("description", "reason", "owner", "revisit_trigger"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                fail(f"assumption {assumption_id}.{field} must be non-empty")

    scenarios = unique_objects(record.get("scenarios"), "scenarios", require_nonempty=True)
    if len(scenarios) < 2:
        fail("at least two scenarios are required for comparison")
    baseline_id = record.get("baseline_scenario_id")
    if baseline_id not in scenarios:
        fail("baseline_scenario_id must reference a scenario")

    valid_basis = set(evidence) | set(assumptions)
    estimate_count = 0
    for path, estimate in iter_estimates(record.get("scenarios")):
        estimate_count += 1
        validate_estimate(path, estimate, valid_basis, status)
    if estimate_count == 0:
        fail("scenarios contain no economic estimates")

    decision = record.get("decision")
    if not isinstance(decision, dict):
        fail("decision must be an object")
    recommended = decision.get("recommended_scenario_id")
    if recommended is not None and recommended not in scenarios:
        fail("decision.recommended_scenario_id must reference a scenario or be null")
    for field in ("decision_rule", "notes"):
        if not isinstance(decision.get(field), str) or not decision[field].strip():
            fail(f"decision.{field} must be non-empty")

    if status == "decision_ready":
        if recommended is None:
            fail("decision_ready analysis requires a recommended_scenario_id")
        if decision.get("reviewed_at") is None:
            fail("decision_ready analysis requires decision.reviewed_at")
        parse_time(decision.get("reviewed_at"), "decision.reviewed_at")
        marker = contains_placeholder(record)
        if marker:
            fail(f"decision_ready analysis contains placeholder text: {marker!r}")
        referenced_evidence: set[str] = set()
        for _, estimate in iter_estimates(record.get("scenarios")):
            referenced_evidence.update(set(estimate.get("basis_ids", [])) & set(evidence))
        bad = sorted(
            evidence_id
            for evidence_id in referenced_evidence
            if evidence[evidence_id].get("status") != "current"
        )
        if bad:
            fail(f"decision_ready analysis references non-current evidence: {', '.join(bad)}")


def pick(estimate: dict, case: str, *, benefit: bool) -> float:
    if case == "base":
        return float(estimate["value"])
    if case == "optimistic":
        return float(estimate["high"] if benefit else estimate["low"])
    if case == "pessimistic":
        return float(estimate["low"] if benefit else estimate["high"])
    raise ValueError(case)


def sum_estimates(bucket: dict, fields: tuple[str, ...], case: str) -> float:
    return sum(pick(bucket[field], case, benefit=False) for field in fields)


def calculate_scenario(scenario: dict, case: str) -> dict:
    volume = float(scenario["annual_requested_outcomes"]["value"])
    success_rate = pick(scenario["success_rate"], case, benefit=True)
    attempts_per_request = pick(scenario["average_attempts_per_request"], case, benefit=False)
    revenue_per_success = pick(scenario["revenue_per_success_minor"], case, benefit=True)
    non_revenue_value_per_success = pick(scenario["non_revenue_value_per_success_minor"], case, benefit=True)

    successes = volume * success_rate
    failures = volume - successes
    attempts = volume * attempts_per_request

    attempt_cost_per_attempt = sum_estimates(scenario["attempt_costs"], ATTEMPT_COST_FIELDS, case)
    attempt_cost = attempts * attempt_cost_per_attempt

    review = scenario["human_review"]
    review_rate = pick(review["review_rate"], case, benefit=False)
    minutes_per_review = pick(review["minutes_per_review"], case, benefit=False)
    reviewer_hourly_cost = pick(review["reviewer_hourly_cost_minor"], case, benefit=False)
    human_review_cost = volume * review_rate * (minutes_per_review / 60.0) * reviewer_hourly_cost

    failure_recovery_unit = pick(scenario["failure_recovery_cost_per_failed_request_minor"], case, benefit=False)
    failure_recovery_cost = failures * failure_recovery_unit
    support_unit = pick(scenario["variable_support_cost_per_request_minor"], case, benefit=False)
    variable_support_cost = volume * support_unit
    variable_cost = attempt_cost + human_review_cost + failure_recovery_cost + variable_support_cost

    fixed_cost = sum_estimates(scenario["annual_fixed_costs"], FIXED_COST_FIELDS, case)
    operating_cost = variable_cost + fixed_cost
    implementation_investment = pick(scenario["implementation_investment_minor"], case, benefit=False)
    first_year_cost = operating_cost + implementation_investment

    revenue = successes * revenue_per_success
    non_revenue_value = successes * non_revenue_value_per_success
    total_value = revenue + non_revenue_value
    contribution_profit = revenue - variable_cost
    recurring_economic_surplus = total_value - operating_cost
    first_year_surplus = total_value - first_year_cost

    cost_per_success = operating_cost / successes if successes > 0 else None
    variable_cost_per_success = variable_cost / successes if successes > 0 else None
    contribution_per_success = contribution_profit / successes if successes > 0 else None
    break_even_value_per_success = operating_cost / successes if successes > 0 else None
    first_year_roi = first_year_surplus / first_year_cost if first_year_cost > 0 else None
    review_share = human_review_cost / variable_cost if variable_cost > 0 else 0.0

    return {
        "scenario_id": scenario["id"],
        "case": case,
        "annual_requested_outcomes": volume,
        "expected_successes": successes,
        "success_rate": success_rate,
        "expected_attempts": attempts,
        "average_attempts_per_request": attempts_per_request,
        "attempt_cost_minor": attempt_cost,
        "human_review_cost_minor": human_review_cost,
        "failure_recovery_cost_minor": failure_recovery_cost,
        "variable_support_cost_minor": variable_support_cost,
        "variable_cost_minor": variable_cost,
        "annual_fixed_cost_minor": fixed_cost,
        "annual_operating_cost_minor": operating_cost,
        "implementation_investment_minor": implementation_investment,
        "first_year_cost_minor": first_year_cost,
        "annual_revenue_minor": revenue,
        "annual_non_revenue_value_minor": non_revenue_value,
        "annual_total_value_minor": total_value,
        "annual_contribution_profit_minor": contribution_profit,
        "annual_recurring_economic_surplus_minor": recurring_economic_surplus,
        "first_year_surplus_minor": first_year_surplus,
        "fully_loaded_cost_per_success_minor": cost_per_success,
        "variable_cost_per_success_minor": variable_cost_per_success,
        "contribution_per_success_minor": contribution_per_success,
        "break_even_total_value_per_success_minor": break_even_value_per_success,
        "first_year_roi": first_year_roi,
        "human_review_share_of_variable_cost": review_share,
    }


def calculate(record: dict) -> dict:
    scenario_map = {scenario["id"]: scenario for scenario in record["scenarios"]}
    cases = ("pessimistic", "base", "optimistic")
    results: dict[str, dict[str, dict]] = {
        scenario_id: {case: calculate_scenario(scenario, case) for case in cases}
        for scenario_id, scenario in scenario_map.items()
    }
    baseline_id = record["baseline_scenario_id"]
    baseline = results[baseline_id]

    for scenario_id, scenario_cases in results.items():
        for case in cases:
            row = scenario_cases[case]
            base_row = baseline[case]
            incremental_surplus = (
                row["annual_recurring_economic_surplus_minor"]
                - base_row["annual_recurring_economic_surplus_minor"]
            )
            incremental_investment = max(
                0.0,
                row["implementation_investment_minor"]
                - base_row["implementation_investment_minor"],
            )
            row["incremental_recurring_surplus_vs_baseline_minor"] = incremental_surplus
            row["incremental_operating_cost_vs_baseline_minor"] = (
                row["annual_operating_cost_minor"] - base_row["annual_operating_cost_minor"]
            )
            row["incremental_total_value_vs_baseline_minor"] = (
                row["annual_total_value_minor"] - base_row["annual_total_value_minor"]
            )
            if incremental_surplus > 0 and incremental_investment > 0:
                row["incremental_payback_months"] = incremental_investment / (incremental_surplus / 12.0)
            elif incremental_investment == 0 and incremental_surplus >= 0:
                row["incremental_payback_months"] = 0.0
            else:
                row["incremental_payback_months"] = None

    base_ranking = sorted(
        (results[scenario_id]["base"] for scenario_id in results),
        key=lambda row: row["annual_recurring_economic_surplus_minor"],
        reverse=True,
    )
    return {
        "analysis_id": record["analysis_id"],
        "currency": record["currency"],
        "baseline_scenario_id": baseline_id,
        "results": results,
        "base_case_ranking": [row["scenario_id"] for row in base_ranking],
    }


def money(value: float | None, currency: str) -> str:
    if value is None:
        return "n/a"
    return f"{currency} {value / 100:,.2f}"


def percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def print_human(record: dict, report: dict) -> None:
    currency = record["currency"]
    print(f"Workflow ROI analysis: {record['analysis_id']} ({record['status']})")
    print(f"Outcome: {record['outcome']['name']}")
    print(f"Baseline: {record['baseline_scenario_id']}")
    print()
    header = (
        "scenario",
        "case",
        "success",
        "cost/success",
        "total value",
        "operating cost",
        "recurring surplus",
        "1st-year ROI",
        "payback vs baseline",
    )
    print(" | ".join(header))
    print(" | ".join("---" for _ in header))
    for scenario in record["scenarios"]:
        for case in ("pessimistic", "base", "optimistic"):
            row = report["results"][scenario["id"]][case]
            payback = row["incremental_payback_months"]
            payback_text = "n/a" if payback is None else f"{payback:.1f} mo"
            print(
                " | ".join(
                    (
                        scenario["id"],
                        case,
                        percent(row["success_rate"]),
                        money(row["fully_loaded_cost_per_success_minor"], currency),
                        money(row["annual_total_value_minor"], currency),
                        money(row["annual_operating_cost_minor"], currency),
                        money(row["annual_recurring_economic_surplus_minor"], currency),
                        percent(row["first_year_roi"]),
                        payback_text,
                    )
                )
            )
    print()
    print("Base-case ranking by recurring economic surplus: " + " > ".join(report["base_case_ranking"]))
    if record["status"] != "decision_ready":
        print("WARNING: analysis is not decision_ready; outputs may rely on draft assumptions.")


def resolve_path(raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    if path != ROOT and ROOT not in path.parents:
        fail("analysis path must stay inside the repository")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis", nargs="?", default=str(DEFAULT_ANALYSIS.relative_to(ROOT)))
    parser.add_argument("--json", action="store_true", help="emit calculated output as JSON")
    parser.add_argument("--validate-only", action="store_true", help="validate without calculating")
    args = parser.parse_args()

    path = resolve_path(args.analysis)
    record = load_json(path)
    validate(record)
    if args.validate_only:
        print(
            f"workflow ROI OK: {record['analysis_id']} status={record['status']} "
            f"scenarios={len(record['scenarios'])} evidence={len(record['evidence'])} "
            f"assumptions={len(record['assumptions'])}"
        )
        return
    report = calculate(record)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(record, report)


if __name__ == "__main__":
    main()
