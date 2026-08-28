#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.workflow_roi import calculate, iter_estimates, validate

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "WORKFLOW_ROI_ANALYSIS.json"


def template_record() -> dict:
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


def decision_ready_record() -> dict:
    record = template_record()
    record["analysis_id"] = "decision-ready-001"
    record["status"] = "decision_ready"
    record["outcome"] = {
        "name": "Resolved customer request",
        "success_event": "Customer request satisfies the acceptance rubric without rework.",
        "measurement_window": "Trailing 30 days",
        "customer_value_notes": "Value is measured from paid outcomes and documented avoided labor.",
        "founder_outcome_record": None,
    }
    record["evidence"] = [
        {
            "id": "e-current",
            "type": "internal_measurement",
            "description": "Current baseline and workflow measurement exported without customer identifiers.",
            "public_url": None,
            "observed_at": "2026-08-27T00:00:00Z",
            "status": "current",
        }
    ]
    record["assumptions"] = []
    for _, estimate in iter_estimates(record["scenarios"]):
        estimate["basis_ids"] = ["e-current"]
    record["scenarios"][0]["description"] = "Current manual workflow measured over the same outcome definition."
    record["scenarios"][0]["constraints"] = ["Maintain the acceptance rubric during comparison."]
    record["scenarios"][1]["description"] = "Agentic alternative measured against the same customer-visible success event."
    record["scenarios"][1]["constraints"] = ["Review cannot be reduced without quality evidence."]
    record["decision"] = {
        "recommended_scenario_id": "agent-balanced",
        "decision_rule": "Choose the design with higher recurring economic surplus when quality and risk thresholds are met.",
        "notes": "Recommendation is conditional on the documented acceptance rubric and current measurement evidence.",
        "reviewed_at": "2026-08-28T00:00:00Z",
    }
    return record


class WorkflowROIValidationTests(unittest.TestCase):
    def test_safe_template_validates_and_calculates(self):
        record = template_record()
        validate(record)
        report = calculate(record)
        self.assertEqual(report["baseline_scenario_id"], "manual-baseline")
        self.assertEqual(set(report["results"]), {"manual-baseline", "agent-balanced"})
        self.assertEqual(len(report["base_case_ranking"]), 2)

    def test_low_value_high_order_is_required(self):
        record = template_record()
        record["scenarios"][1]["success_rate"] = {
            "value": 0.9,
            "low": 0.95,
            "high": 0.99,
            "classification": "estimate",
            "basis_ids": ["assumption-success"],
        }
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("low <= value <= high", str(ctx.exception))

    def test_unknown_provenance_basis_is_rejected(self):
        record = template_record()
        record["scenarios"][1]["success_rate"]["basis_ids"] = ["missing-evidence"]
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("unknown basis ids", str(ctx.exception))

    def test_observed_fact_cannot_hide_uncertainty_range(self):
        record = template_record()
        estimate = record["scenarios"][0]["annual_requested_outcomes"]
        estimate["classification"] = "observed_fact"
        estimate["low"] = 900
        estimate["value"] = 1000
        estimate["high"] = 1100
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("observed_fact", str(ctx.exception))

    def test_ratio_cannot_exceed_one(self):
        record = template_record()
        record["scenarios"][1]["human_review"]["review_rate"]["high"] = 1.2
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("between 0 and 1", str(ctx.exception))

    def test_attempts_cannot_be_less_than_one(self):
        record = template_record()
        record["scenarios"][1]["average_attempts_per_request"]["low"] = 0.8
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("at least 1", str(ctx.exception))

    def test_decision_ready_requires_recommendation(self):
        record = decision_ready_record()
        record["decision"]["recommended_scenario_id"] = None
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("recommended_scenario_id", str(ctx.exception))

    def test_decision_ready_rejects_stale_referenced_evidence(self):
        record = decision_ready_record()
        record["evidence"][0]["status"] = "stale"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("non-current evidence", str(ctx.exception))

    def test_sensitive_fields_are_rejected(self):
        record = template_record()
        record["api_key"] = "do-not-store-this"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("sensitive field", str(ctx.exception))

    def test_pessimistic_and_optimistic_cases_bound_base_surplus(self):
        record = template_record()
        validate(record)
        report = calculate(record)
        for scenario_id in report["results"]:
            rows = report["results"][scenario_id]
            self.assertLessEqual(
                rows["pessimistic"]["annual_recurring_economic_surplus_minor"],
                rows["base"]["annual_recurring_economic_surplus_minor"],
            )
            self.assertLessEqual(
                rows["base"]["annual_recurring_economic_surplus_minor"],
                rows["optimistic"]["annual_recurring_economic_surplus_minor"],
            )

    def test_retries_increase_attempt_cost(self):
        record = template_record()
        base = calculate(record)["results"]["agent-balanced"]["base"]
        changed = copy.deepcopy(record)
        attempts = changed["scenarios"][1]["average_attempts_per_request"]
        attempts["value"] = 1.75
        attempts["high"] = 2.0
        higher = calculate(changed)["results"]["agent-balanced"]["base"]
        self.assertGreater(higher["attempt_cost_minor"], base["attempt_cost_minor"])
        self.assertGreater(higher["annual_operating_cost_minor"], base["annual_operating_cost_minor"])

    def test_higher_review_rate_increases_fully_loaded_cost(self):
        record = template_record()
        base = calculate(record)["results"]["agent-balanced"]["base"]
        changed = copy.deepcopy(record)
        review = changed["scenarios"][1]["human_review"]["review_rate"]
        review["value"] = 0.4
        review["high"] = 0.6
        higher = calculate(changed)["results"]["agent-balanced"]["base"]
        self.assertGreater(higher["human_review_cost_minor"], base["human_review_cost_minor"])
        self.assertGreater(higher["fully_loaded_cost_per_success_minor"], base["fully_loaded_cost_per_success_minor"])


if __name__ == "__main__":
    unittest.main()
