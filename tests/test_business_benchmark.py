import json
import unittest
from pathlib import Path

from scripts.validate_business_benchmark import validate

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "BUSINESS_BENCHMARK_RECORD.json"
EXAMPLE = ROOT / "examples" / "BUSINESS_BENCHMARK_COMPARISON.json"


class BusinessBenchmarkTests(unittest.TestCase):
    def starter(self):
        return json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def reviewed(self):
        return json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def assert_invalid(self, record, text):
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn(text, str(ctx.exception))

    def test_safe_starter_is_valid(self):
        validate(self.starter())

    def test_worked_reviewed_example_is_valid(self):
        validate(self.reviewed())

    def test_real_world_authority_is_rejected(self):
        r = self.starter()
        r["authority"]["real_world_authority_granted"] = True
        self.assert_invalid(r, "simulation-only")

    def test_unknown_scenario_is_rejected(self):
        r = self.starter()
        r["scenario"]["scenario_id"] = "made-up"
        self.assert_invalid(r, "unknown scenario_id")

    def test_run_accounting_must_balance(self):
        r = self.reviewed()
        r["configurations"][0]["failed_runs"] = 1
        self.assert_invalid(r, "must equal run_count")

    def test_capability_score_is_transparent(self):
        r = self.reviewed()
        r["configurations"][0]["capability_score"] = 99
        self.assert_invalid(r, "transparent completion formula")

    def test_p95_cannot_be_lower_than_p50(self):
        r = self.reviewed()
        r["configurations"][0]["metrics"]["p95_latency_ms"] = 1
        self.assert_invalid(r, "p95 latency cannot be lower")

    def test_recovery_success_cannot_exceed_attempts(self):
        r = self.reviewed()
        r["configurations"][0]["metrics"]["successful_recoveries"] = 2
        self.assert_invalid(r, "cannot exceed recovery attempts")

    def test_component_passes_must_match_metrics(self):
        r = self.reviewed()
        r["configurations"][1]["component_passes"]["human_review"] = True
        self.assert_invalid(r, "must match measured threshold results")

    def test_reviewed_record_requires_repeated_runs(self):
        r = self.reviewed()
        c = r["configurations"][0]
        c["run_count"] = 4
        c["successful_runs"] = 3
        c["partial_runs"] = 1
        c["capability_score"] = 87.5
        self.assert_invalid(r, "at least five repeated runs")

    def test_statistical_claim_requires_twenty_runs(self):
        r = self.reviewed()
        r["comparison"]["claims_statistical_superiority"] = True
        self.assert_invalid(r, "at least 20 runs")

    def test_reviewed_record_requires_review_evidence(self):
        r = self.reviewed()
        r["evidence"] = [item for item in r["evidence"] if item["type"] != "review_record"]
        self.assert_invalid(r, "current review record")

    def test_executed_record_requires_harness_evidence(self):
        r = self.reviewed()
        r["status"] = "executed"
        r["evidence"] = [item for item in r["evidence"] if item["type"] == "review_record"]
        self.assert_invalid(r, "current harness/run-summary evidence")

    def test_cross_currency_comparison_is_rejected(self):
        r = self.reviewed()
        r["configurations"][1]["metrics"]["currency"] = "EUR"
        self.assert_invalid(r, "same currency")

    def test_policy_failure_metric_cannot_undercount_taxonomy(self):
        r = self.reviewed()
        r["configurations"][0]["failure_counts"]["policy_violation"] = 1
        self.assert_invalid(r, "cannot undercount")

    def test_private_customer_material_is_rejected(self):
        r = self.starter()
        r["privacy"]["contains_private_customer_data"] = True
        self.assert_invalid(r, "must be false")

    def test_sensitive_key_is_rejected(self):
        r = self.starter()
        r["api_key"] = "do-not-store"
        self.assert_invalid(r, "prohibited sensitive field")


if __name__ == "__main__":
    unittest.main()
