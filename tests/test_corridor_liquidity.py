import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("corridor_liquidity", ROOT / "scripts" / "analyze_corridor_liquidity.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


class CorridorLiquidityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "examples" / "CORRIDOR_LIQUIDITY_SYNTHETIC.json").read_text())
        cls.costs = json.loads((ROOT / "examples" / "CORRIDOR_INTEGRATION_COSTS_SYNTHETIC.json").read_text())

    def synthetic_items(self):
        return copy.deepcopy(self.fixture["corridors"])

    def test_synthetic_fixture_validates(self):
        MOD.validate_dataset(copy.deepcopy(self.fixture))
        currency, costs = MOD.validate_costs(copy.deepcopy(self.costs))
        self.assertEqual(currency, "USD")
        self.assertIn("machine-payment-reconciliation", costs)

    def test_baseline_reachability_is_conservative(self):
        report = MOD.analyze_cohort(self.synthetic_items(), 3, None, {})
        self.assertEqual(report["baseline"]["reachable_counterparty_rate"], 0.333333)
        self.assertTrue(report["publishable"])

    def test_payment_integration_unlocks_one_corridor(self):
        report = MOD.analyze_cohort(self.synthetic_items(), 3, None, {})
        row = next(x for x in report["convention_unlocks"] if x["convention"] == "machine-payment-reconciliation")
        self.assertEqual(row["incremental_reachable_corridors"], 1)
        self.assertEqual(row["unlocked_corridor_ids"], ["synthetic-payment-gap"])

    def test_real_authority_gap_is_not_fixed_by_interoperability(self):
        report = MOD.analyze_cohort(self.synthetic_items(), 3, None, {})
        row = next(x for x in report["convention_unlocks"] if x["convention"] == "bounded-authority")
        self.assertNotIn("synthetic-real-authority-gap", row["unlocked_corridor_ids"])
        self.assertIn("synthetic-required-compatibility-gap", row["unlocked_corridor_ids"])

    def test_complementary_pair_detects_synergy_without_double_counting(self):
        report = MOD.analyze_cohort(self.synthetic_items(), 3, None, {})
        pair = next(x for x in report["complementary_pairs"] if set(x["conventions"]) == {"execution-evidence", "machine-payment-reconciliation"})
        self.assertEqual(pair["incremental_reachable_corridors"], 2)
        self.assertEqual(pair["complementarity_gain_over_best_single"], 1)
        self.assertEqual(len(pair["unlocked_corridor_ids"]), len(set(pair["unlocked_corridor_ids"])))

    def test_synthetic_demand_cannot_claim_commercial_value(self):
        data = copy.deepcopy(self.fixture)
        data["corridors"][0]["qualified_demand_value_minor_range"] = [100, 200]
        data["corridors"][0]["currency"] = "USD"
        with self.assertRaisesRegex(ValueError, "only allowed for observed/verified"):
            MOD.validate_dataset(data)

    def test_duplicate_corridor_ids_fail_denominator_integrity(self):
        data = copy.deepcopy(self.fixture)
        data["corridors"][1]["corridor_id"] = data["corridors"][0]["corridor_id"]
        with self.assertRaisesRegex(ValueError, "unique"):
            MOD.validate_dataset(data)

    def test_missing_population_definition_fails(self):
        data = copy.deepcopy(self.fixture)
        data["population_definition"] = ""
        with self.assertRaisesRegex(ValueError, "population_definition"):
            MOD.validate_dataset(data)

    def test_small_cohort_is_not_publishable(self):
        report = MOD.analyze_cohort(self.synthetic_items()[:2], 3, None, {})
        self.assertFalse(report["publishable"])
        self.assertIn("threshold", report["publication_note"])

    def test_roi_requires_commercial_demand_and_same_currency(self):
        item = copy.deepcopy(self.synthetic_items()[1])
        item["corridor_id"] = "observed-payment-gap"
        item["evidence_class"] = "observed_commercial_demand"
        item["qualified_demand_value_minor_range"] = [1000000, 2000000]
        item["currency"] = "USD"
        costs = {
            "machine-payment-reconciliation": {
                "implementation_cost_minor_range": [200000, 300000],
                "annual_maintenance_cost_minor_range": [50000, 100000],
            }
        }
        report = MOD.analyze_cohort([item], 1, "USD", costs)
        row = next(x for x in report["convention_unlocks"] if x["convention"] == "machine-payment-reconciliation")
        self.assertIsNotNone(row["integration_roi"])
        self.assertEqual(row["integration_roi"]["year_one_cost_minor_range"], [250000, 400000])
        self.assertEqual(row["unlocked_qualified_demand_value_minor_range"], [1000000, 2000000])

    def test_deal_plan_summary_must_never_grant_authority(self):
        data = copy.deepcopy(self.fixture)
        data["corridors"][0]["plan"]["action_authorized"] = True
        with self.assertRaisesRegex(ValueError, "must not grant authority"):
            MOD.validate_dataset(data)


if __name__ == "__main__":
    unittest.main()
