#!/usr/bin/env python3
"""Validate Agent Business outcome benchmark records with the Python standard library."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "agent-index.json"
SCENARIOS = ROOT / "benchmarks" / "BUSINESS_SCENARIOS.json"

EXECUTED = {"executed", "reviewed", "published", "superseded"}
REVIEWED = {"reviewed", "published", "superseded"}
FAILURE_TYPES = {
    "hallucinated_completion", "wrong_tool_success_claim", "policy_violation",
    "timeout", "retry_storm", "partial_side_effect", "stale_data",
    "cross_tenant_leakage", "recovery_failure", "human_takeover", "other",
}
PROHIBITED_KEYS = {
    "password", "api_key", "access_token", "refresh_token", "authorization",
    "credential", "credentials", "raw_prompt", "private_prompt", "answer_key",
    "restricted_fixture", "production_token", "private_customer_record",
}


def fail(message: str) -> None:
    raise SystemExit(f"business-benchmark validation failed: {message}")


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot parse {path}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path} must contain a JSON object")
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


def scan_sensitive(value: object, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in PROHIBITED_KEYS:
                fail(f"prohibited sensitive field: {path}.{key}")
            scan_sensitive(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_sensitive(child, f"{path}[{index}]")


def non_negative_int(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        fail(f"{label} must be a non-negative integer")
    return value


def non_negative_number(value: object, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
        fail(f"{label} must be a non-negative number")
    return float(value)


def validate_scenario_pack() -> dict[str, dict]:
    pack = load(SCENARIOS)
    if pack.get("schema_version") != "1.0.0" or pack.get("pack_version") != "1.0.0":
        fail("scenario pack schema_version and pack_version must be 1.0.0")
    scenarios = pack.get("scenarios")
    if not isinstance(scenarios, list) or len(scenarios) < 5:
        fail("scenario pack must contain at least five scenarios")
    required_classes = {
        "sales_revenue_operations", "customer_support_success", "finance_operations",
        "research_analysis", "multi_agent_coordination",
    }
    seen_ids: set[str] = set()
    seen_classes: set[str] = set()
    result: dict[str, dict] = {}
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            fail("scenario entries must be objects")
        scenario_id = scenario.get("scenario_id")
        if not isinstance(scenario_id, str) or not scenario_id:
            fail("every scenario needs a scenario_id")
        if scenario_id in seen_ids:
            fail(f"duplicate scenario_id: {scenario_id}")
        seen_ids.add(scenario_id)
        seen_classes.add(str(scenario.get("workflow_class")))
        if scenario.get("visibility") not in {"public", "held_out"}:
            fail(f"{scenario_id}: visibility must be public or held_out")
        authority = scenario.get("authority")
        if not isinstance(authority, dict) or authority.get("simulation_only") is not True:
            fail(f"{scenario_id}: benchmark authority must be simulation_only")
        stops = scenario.get("stop_conditions")
        if not isinstance(stops, dict):
            fail(f"{scenario_id}: stop_conditions must be an object")
        for key in ("max_wall_clock_seconds", "max_tool_calls", "max_total_cost_minor"):
            if non_negative_int(stops.get(key), f"{scenario_id}.{key}") <= 0:
                fail(f"{scenario_id}: {key} must be positive")
        if stops.get("stop_on_policy_violation") is not True:
            fail(f"{scenario_id}: stop_on_policy_violation must be true")
        if not scenario.get("success_criteria"):
            fail(f"{scenario_id}: success_criteria must be non-empty")
        result[scenario_id] = scenario
    missing = sorted(required_classes - seen_classes)
    if missing:
        fail("scenario pack is missing required workflow classes: " + ", ".join(missing))
    return result


def validate_evidence(items: object) -> tuple[dict[str, dict], set[str]]:
    if not isinstance(items, list):
        fail("evidence must be a list")
    evidence: dict[str, dict] = {}
    current: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            fail("evidence entries must be objects")
        evidence_id = item.get("id")
        if not isinstance(evidence_id, str) or not evidence_id:
            fail("evidence entries require non-empty ids")
        if evidence_id in evidence:
            fail(f"duplicate evidence id: {evidence_id}")
        if item.get("type") not in {"harness_output", "run_summary", "review_record", "public_artifact"}:
            fail(f"evidence {evidence_id}: unsupported evidence type")
        if item.get("status") not in {"current", "stale"}:
            fail(f"evidence {evidence_id}: status must be current or stale")
        parse_time(item.get("observed_at"), f"evidence {evidence_id}.observed_at")
        url = item.get("public_url")
        if url is not None:
            parsed = urlparse(url)
            if parsed.scheme != "https" or not parsed.netloc:
                fail(f"evidence {evidence_id}.public_url must be absolute https")
        evidence[evidence_id] = item
        if item.get("status") == "current":
            current.add(evidence_id)
    return evidence, current


def expected_component_passes(config: dict) -> dict[str, bool]:
    runs = config["run_count"]
    successes = config["successful_runs"]
    metrics = config["metrics"]
    thresholds = config["thresholds"]
    cost_per_success = metrics["total_cost_minor"] / successes if successes else float("inf")
    review_per_run = metrics["human_review_minutes"] / runs if runs else float("inf")
    attempts = metrics["recovery_attempts"]
    recovery_rate = metrics["successful_recoveries"] / attempts if attempts else 1.0
    return {
        "cost": cost_per_success <= thresholds["max_cost_per_success_minor"],
        "latency": metrics["p95_latency_ms"] <= thresholds["max_p95_latency_ms"],
        "human_review": review_per_run <= thresholds["max_review_minutes_per_run"],
        "policy": metrics["policy_violations"] <= thresholds["max_policy_violations"],
        "recovery": recovery_rate >= thresholds["min_recovery_success_rate"],
    }


def validate_configuration(config: object, status: str) -> str:
    if not isinstance(config, dict):
        fail("configuration entries must be objects")
    config_id = config.get("configuration_id")
    if not isinstance(config_id, str) or not config_id:
        fail("configurations require non-empty configuration_id")
    for label in ("agent_revision", "provider", "model", "prompt_policy_ref"):
        if not isinstance(config.get(label), str) or not config[label]:
            fail(f"{config_id}.{label} must be a non-empty string")
    tools = config.get("tool_versions")
    if not isinstance(tools, list) or any(not isinstance(item, str) or not item for item in tools):
        fail(f"{config_id}.tool_versions must be a list of non-empty strings")

    runs = non_negative_int(config.get("run_count"), f"{config_id}.run_count")
    success = non_negative_int(config.get("successful_runs"), f"{config_id}.successful_runs")
    partial = non_negative_int(config.get("partial_runs"), f"{config_id}.partial_runs")
    failed = non_negative_int(config.get("failed_runs"), f"{config_id}.failed_runs")
    if success + partial + failed != runs:
        fail(f"{config_id}: successful + partial + failed runs must equal run_count")

    failures = config.get("failure_counts")
    if not isinstance(failures, dict) or set(failures) != FAILURE_TYPES:
        fail(f"{config_id}.failure_counts must contain exactly the canonical failure taxonomy")
    for name, value in failures.items():
        if non_negative_int(value, f"{config_id}.failure_counts.{name}") > runs:
            fail(f"{config_id}.failure_counts.{name} cannot exceed run_count")

    metrics = config.get("metrics")
    if not isinstance(metrics, dict):
        fail(f"{config_id}.metrics must be an object")
    for key in ("total_cost_minor", "p50_latency_ms", "p95_latency_ms", "escalations", "policy_violations", "unsafe_side_effects", "recovery_attempts", "successful_recoveries"):
        non_negative_int(metrics.get(key), f"{config_id}.metrics.{key}")
    non_negative_number(metrics.get("human_review_minutes"), f"{config_id}.metrics.human_review_minutes")
    currency = metrics.get("currency")
    if not isinstance(currency, str) or len(currency) != 3 or currency.upper() != currency:
        fail(f"{config_id}.metrics.currency must be a three-letter uppercase currency code")
    if metrics["p95_latency_ms"] < metrics["p50_latency_ms"]:
        fail(f"{config_id}: p95 latency cannot be lower than p50 latency")
    if metrics["successful_recoveries"] > metrics["recovery_attempts"]:
        fail(f"{config_id}: successful recoveries cannot exceed recovery attempts")
    if metrics["policy_violations"] < failures["policy_violation"]:
        fail(f"{config_id}: policy violation metric cannot undercount failure taxonomy")

    thresholds = config.get("thresholds")
    if not isinstance(thresholds, dict):
        fail(f"{config_id}.thresholds must be an object")
    for key in ("max_cost_per_success_minor", "max_p95_latency_ms", "max_policy_violations"):
        non_negative_int(thresholds.get(key), f"{config_id}.thresholds.{key}")
    non_negative_number(thresholds.get("max_review_minutes_per_run"), f"{config_id}.thresholds.max_review_minutes_per_run")
    recovery_floor = thresholds.get("min_recovery_success_rate")
    if not isinstance(recovery_floor, (int, float)) or isinstance(recovery_floor, bool) or not 0 <= recovery_floor <= 1:
        fail(f"{config_id}.thresholds.min_recovery_success_rate must be between 0 and 1")

    score = config.get("capability_score")
    if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 100:
        fail(f"{config_id}.capability_score must be between 0 and 100")
    expected_score = 100 * (success + 0.5 * partial) / runs if runs else 0.0
    if abs(float(score) - expected_score) > 0.01:
        fail(f"{config_id}.capability_score must equal transparent completion formula ({expected_score:.2f})")

    if status in EXECUTED:
        if runs == 0:
            fail(f"{config_id}: executed-or-later records require completed runs")
        for field in ("agent_revision", "provider", "model", "prompt_policy_ref"):
            if config[field] == "unconfigured":
                fail(f"{config_id}.{field} must be configured after execution")
        declared = config.get("component_passes")
        expected = expected_component_passes(config)
        if declared != expected:
            fail(f"{config_id}.component_passes must match measured threshold results: {expected}")
    if status in REVIEWED and runs < 5:
        fail(f"{config_id}: reviewed/published records require at least five repeated runs")
    return config_id


def validate(record: dict) -> None:
    required = {"schema_version", "benchmark_id", "status", "updated_at", "scenario", "provenance", "authority", "configurations", "comparison", "evidence", "privacy"}
    missing = sorted(required - set(record))
    if missing:
        fail("missing required fields: " + ", ".join(missing))
    if record.get("schema_version") != "1.0.0":
        fail("schema_version must be 1.0.0")
    status = record.get("status")
    if status not in {"draft", "scenario_ready", "executed", "reviewed", "published", "superseded"}:
        fail("status is invalid")
    parse_time(record.get("updated_at"), "updated_at")
    scan_sensitive(record)

    resources = {item.get("id") for item in load(INDEX).get("resources", []) if isinstance(item, dict)}
    for resource_id in record.get("repository_resources", []):
        if resource_id not in resources:
            fail(f"unknown repository resource: {resource_id}")

    scenarios = validate_scenario_pack()
    scenario = record.get("scenario")
    if not isinstance(scenario, dict):
        fail("scenario must be an object")
    scenario_id = scenario.get("scenario_id")
    if scenario_id not in scenarios:
        fail(f"unknown scenario_id: {scenario_id}")
    definition = scenarios[scenario_id]
    if scenario.get("pack_id") != "agent-business-core" or scenario.get("pack_version") != "1.0.0":
        fail("scenario pack provenance must match agent-business-core 1.0.0")
    if scenario.get("scenario_version") != definition.get("scenario_version"):
        fail("scenario_version does not match canonical scenario pack")
    if scenario.get("visibility") != definition.get("visibility"):
        fail("scenario visibility does not match canonical scenario pack")
    if not isinstance(scenario.get("fixture_version"), str) or not scenario["fixture_version"]:
        fail("scenario.fixture_version must be a non-empty string")

    authority = record.get("authority")
    if not isinstance(authority, dict) or authority.get("simulation_only") is not True or authority.get("real_world_authority_granted") is not False:
        fail("benchmark authority must be simulation-only and grant no real-world authority")

    provenance = record.get("provenance")
    if not isinstance(provenance, dict):
        fail("provenance must be an object")
    if provenance.get("seed_policy") not in {"fixed", "recorded", "provider_unavailable", "not_applicable"}:
        fail("provenance.seed_policy is invalid")
    start = parse_time(provenance.get("observed_from"), "provenance.observed_from")
    end = parse_time(provenance.get("observed_to"), "provenance.observed_to")
    if end < start:
        fail("provenance.observed_to cannot precede observed_from")
    if status in EXECUTED:
        for field in ("harness_version", "environment_version"):
            if not isinstance(provenance.get(field), str) or provenance[field] in {"", "unconfigured"}:
                fail(f"provenance.{field} must be configured after execution")

    privacy = record.get("privacy")
    if not isinstance(privacy, dict):
        fail("privacy must be an object")
    for field in ("contains_credentials", "contains_private_customer_data", "contains_secret_prompts", "contains_restricted_answer_keys"):
        if privacy.get(field) is not False:
            fail(f"privacy.{field} must be false")
    if privacy.get("public_disclosure_confirmed") is not True:
        fail("privacy.public_disclosure_confirmed must be true")

    configs = record.get("configurations")
    if not isinstance(configs, list) or len(configs) < 2:
        fail("configurations must contain at least two candidates")
    ids: set[str] = set()
    for config in configs:
        config_id = validate_configuration(config, status)
        if config_id in ids:
            fail(f"duplicate configuration_id: {config_id}")
        ids.add(config_id)
    currencies = {config["metrics"]["currency"] for config in configs}
    if len(currencies) != 1:
        fail("all compared configurations must use the same currency")

    evidence, current = validate_evidence(record.get("evidence"))
    if status in EXECUTED:
        if not any(item.get("type") in {"harness_output", "run_summary"} and item.get("status") == "current" for item in evidence.values()):
            fail("executed-or-later records require current harness/run-summary evidence")
    if status in REVIEWED:
        if not any(item.get("type") == "review_record" and item.get("status") == "current" for item in evidence.values()):
            fail("reviewed/published records require a current review record")
        if not current:
            fail("reviewed/published records require current evidence")

    comparison = record.get("comparison")
    if not isinstance(comparison, dict):
        fail("comparison must be an object")
    if not isinstance(comparison.get("measured_result"), str) or not isinstance(comparison.get("interpretation"), str):
        fail("comparison measured_result and interpretation must be strings")
    if not isinstance(comparison.get("estimates"), list) or any(not isinstance(item, str) for item in comparison["estimates"]):
        fail("comparison.estimates must be a list of strings")
    statistical_claim = comparison.get("claims_statistical_superiority")
    if not isinstance(statistical_claim, bool):
        fail("comparison.claims_statistical_superiority must be boolean")
    if statistical_claim:
        if status not in {"reviewed", "published", "superseded"}:
            fail("statistical superiority claims require reviewed-or-later status")
        if any(config["run_count"] < 20 for config in configs):
            fail("statistical superiority claims require at least 20 runs per configuration")
        if not any(item.get("type") == "review_record" and item.get("status") == "current" for item in evidence.values()):
            fail("statistical superiority claims require current review evidence")
    if status == "published" and (not comparison["measured_result"].strip() or not comparison["interpretation"].strip()):
        fail("published records require non-empty measured result and interpretation")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", nargs="?", default="templates/BUSINESS_BENCHMARK_RECORD.json")
    args = parser.parse_args()
    path = (ROOT / args.record).resolve()
    if path != ROOT and ROOT not in path.parents:
        fail("record path must stay inside repository")
    record = load(path)
    validate(record)
    print(f"business benchmark OK: {record['benchmark_id']} status={record['status']} configurations={len(record['configurations'])}")


if __name__ == "__main__":
    main()
