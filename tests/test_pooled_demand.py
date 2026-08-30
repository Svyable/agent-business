import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("pooled", ROOT / "scripts" / "validate_pooled_demand.py")
pooled = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pooled)


def starter():
    return json.loads((ROOT / "templates" / "POOLED_DEMAND_LOT.json").read_text())


def finalized_pool():
    record = starter()
    record["updated_at"] = "2026-08-30T18:30:00Z"
    record["status"] = "allocated"
    for index, participant in enumerate(record["participants"]):
        participant["demand_quality"] = "verified_commercial"
        participant["quantity_min"] = 1
        participant["quantity_max"] = 5
        participant["committed_quantity"] = 5
        participant["max_unit_price_minor"] = 1000
        participant["budget_cap_minor"] = 6000
        participant["valid_until"] = "2026-09-30T00:00:00Z"
        participant["opt_in_state"] = "accepted"
        participant["committed_at"] = f"2026-08-30T18:0{index}:00Z"
        participant["accepted_offer_at"] = f"2026-08-30T18:2{index}:00Z"
        participant["authority"] = {
            "state": "current",
            "evidence_ref": f"authority.{index}",
            "currency": "USD",
            "max_total_minor": 6000,
            "expires_at": "2026-10-01T00:00:00Z",
        }
        participant["related_party_to_seller"] = "no"
    record["thresholds"].update({
        "computed_committed_buyers": 2,
        "computed_committed_quantity": 10,
        "computed_committed_budget_minor": 12000,
        "state": "met",
        "evaluated_at": "2026-08-30T18:10:00Z",
    })
    record["seller_offer"] = {
        "status": "selected",
        "offer_id": "pool-offer.1",
        "seller_listing_ref": "listing.seller",
        "seller_listing_version": "1.0.0",
        "received_at": "2026-08-30T18:12:00Z",
        "selected_at": "2026-08-30T18:15:00Z",
        "valid_until": "2026-09-01T00:00:00Z",
        "capacity_ceiling": 8,
        "volume_tiers": [
            {"min_quantity": 1, "max_quantity": 4, "unit_price_minor": 900},
            {"min_quantity": 5, "max_quantity": 8, "unit_price_minor": 800},
            {"min_quantity": 9, "max_quantity": 20, "unit_price_minor": 700},
        ],
        "setup_cost_minor": 100,
        "setup_allocation_method": "pro_rata_allocated_quantity",
        "dependencies": [],
        "related_party_disclosure": "none_known",
    }
    record["allocation"] = {
        "state": "finalized",
        "policy": "pro_rata_committed_quantity",
        "finalized_at": "2026-08-30T18:25:00Z",
        "selected_unit_price_minor": 800,
        "allocated_total_quantity": 8,
        "allocations": [
            {
                "participant_id": "buyer.example.a",
                "allocated_quantity": 4,
                "unit_price_minor": 800,
                "setup_share_minor": 50,
                "total_price_minor": 3250,
                "buyer_deal_plan_ref": "deal:buyer.example.a:pool-offer.1",
                "payment_authorized": False,
            },
            {
                "participant_id": "buyer.example.b",
                "allocated_quantity": 4,
                "unit_price_minor": 800,
                "setup_share_minor": 50,
                "total_price_minor": 3250,
                "buyer_deal_plan_ref": "deal:buyer.example.b:pool-offer.1",
                "payment_authorized": False,
            },
        ],
    }
    record["economics"] = {
        "baseline_policy": "comparable_individual_evidence_only",
        "market_claims_allowed": False,
        "buyer_savings": [],
        "supplier_concentration": {
            "single_supplier": True,
            "risk": "medium",
            "substitution_plan": "Re-run sourcing if the selected seller cannot deliver.",
        },
    }
    return record


class PooledDemandTests(unittest.TestCase):
    def errors(self, record, allow_draft=False):
        return pooled.validate_record(record, allow_draft=allow_draft)

    def test_safe_starter_passes_only_with_allow_draft(self):
        record = starter()
        self.assertEqual(self.errors(record, allow_draft=True), [])
        self.assertIn("draft pool requires --allow-draft", self.errors(record))

    def test_valid_finalized_pool_passes(self):
        self.assertEqual(self.errors(finalized_pool()), [])

    def test_duplicate_rfq_cannot_be_counted_twice(self):
        record = starter()
        record["participants"][1]["rfq_ref"]["request_id"] = record["participants"][0]["rfq_ref"]["request_id"]
        self.assertTrue(any("one RFQ cannot be counted twice" in error for error in self.errors(record, True)))

    def test_synthetic_volume_cannot_be_committed_commercial_demand(self):
        record = starter()
        p = record["participants"][0]
        p["opt_in_state"] = "committed"
        p["committed_quantity"] = 1
        p["max_unit_price_minor"] = 100
        p["budget_cap_minor"] = 100
        p["committed_at"] = "2026-08-30T18:40:00Z"
        p["authority"] = {"state": "current", "evidence_ref": "x", "currency": "USD", "max_total_minor": 100, "expires_at": "2026-10-01T00:00:00Z"}
        self.assertTrue(any("requires verified_commercial" in error for error in self.errors(record, True)))

    def test_threshold_cannot_count_phantom_volume(self):
        record = starter()
        record["thresholds"]["computed_committed_buyers"] = 2
        record["thresholds"]["computed_committed_quantity"] = 10
        record["thresholds"]["state"] = "met"
        errors = self.errors(record, True)
        self.assertTrue(any("recomputed value 0" in error for error in errors))
        self.assertIn("thresholds.state does not match recomputed threshold state", errors)

    def test_quantity_cannot_expand_past_original_rfq_bound(self):
        record = finalized_pool()
        record["participants"][0]["committed_quantity"] = 6
        self.assertTrue(any("exceeds original quantity_max" in error for error in self.errors(record)))

    def test_volume_tiers_must_be_contiguous(self):
        record = finalized_pool()
        record["seller_offer"]["volume_tiers"][1]["min_quantity"] = 6
        self.assertTrue(any("contiguous" in error for error in self.errors(record)))

    def test_higher_volume_cannot_raise_unit_price(self):
        record = finalized_pool()
        record["seller_offer"]["volume_tiers"][1]["unit_price_minor"] = 950
        self.assertTrue(any("must not increase" in error for error in self.errors(record)))

    def test_related_party_demand_requires_disclosure(self):
        record = finalized_pool()
        record["participants"][0]["related_party_to_seller"] = "yes"
        self.assertIn("related-party buyer/seller relationship must be disclosed", self.errors(record))

    def test_market_claims_require_resolved_non_related_parties(self):
        record = finalized_pool()
        record["economics"]["market_claims_allowed"] = True
        self.assertTrue(any("market claims require" in error for error in self.errors(record)))

    def test_buyer_cannot_accept_before_pool_offer_selected(self):
        record = finalized_pool()
        record["participants"][0]["accepted_offer_at"] = "2026-08-30T18:14:00Z"
        self.assertTrue(any("before it was selected" in error for error in self.errors(record)))

    def test_allocation_cannot_include_non_accepting_buyer(self):
        record = finalized_pool()
        record["participants"][1]["opt_in_state"] = "committed"
        record["participants"][1]["accepted_offer_at"] = None
        self.assertTrue(any("did not accept" in error or "deterministic" in error for error in self.errors(record)))

    def test_pro_rata_allocation_is_deterministic(self):
        record = finalized_pool()
        record["participants"][0]["committed_quantity"] = 5
        record["participants"][1]["committed_quantity"] = 3
        record["thresholds"]["computed_committed_quantity"] = 8
        record["thresholds"]["min_committed_quantity"] = 8
        record["seller_offer"]["capacity_ceiling"] = 5
        record["allocation"]["allocated_total_quantity"] = 5
        record["allocation"]["selected_unit_price_minor"] = 800
        # 5/8 * 5 = 3.125 and 3/8 * 5 = 1.875 => 3 and 2.
        record["allocation"]["allocations"][0].update({"allocated_quantity": 3, "setup_share_minor": 60, "total_price_minor": 2460})
        record["allocation"]["allocations"][1].update({"allocated_quantity": 2, "setup_share_minor": 40, "total_price_minor": 1640})
        self.assertEqual(self.errors(record), [])

    def test_setup_cost_must_reconcile(self):
        record = finalized_pool()
        record["allocation"]["allocations"][0]["setup_share_minor"] = 51
        self.assertTrue(any("setup share" in error for error in self.errors(record)))

    def test_pool_allocation_never_authorizes_payment(self):
        record = finalized_pool()
        record["allocation"]["allocations"][0]["payment_authorized"] = True
        self.assertTrue(any("must never authorize payment" in error for error in self.errors(record)))

    def test_pooled_price_cannot_exceed_buyer_unit_cap(self):
        record = finalized_pool()
        record["participants"][0]["max_unit_price_minor"] = 700
        self.assertTrue(any("exceeds buyer max unit price" in error for error in self.errors(record)))

    def test_pooled_total_cannot_exceed_buyer_budget(self):
        record = finalized_pool()
        record["participants"][0]["budget_cap_minor"] = 3200
        record["participants"][0]["authority"]["max_total_minor"] = 6000
        self.assertTrue(any("exceeds buyer budget cap" in error for error in self.errors(record)))

    def test_savings_require_comparable_evidence(self):
        record = finalized_pool()
        record["economics"]["buyer_savings"] = [{
            "participant_id": "buyer.example.a",
            "baseline_source_type": "fabricated_list_price",
            "baseline_source_ref": "none",
            "comparable_scope_hash": record["normalized_demand"]["scope_hash"],
            "currency": "USD",
            "baseline_total_minor": 4000,
            "pooled_total_minor": 3250,
            "savings_minor": 750,
        }]
        self.assertTrue(any("comparable evidence" in error for error in self.errors(record)))

    def test_savings_scope_must_match_pool_scope(self):
        record = finalized_pool()
        record["economics"]["buyer_savings"] = [{
            "participant_id": "buyer.example.a",
            "baseline_source_type": "prior_individual_quote",
            "baseline_source_ref": "quote.1",
            "comparable_scope_hash": "sha256:different",
            "currency": "USD",
            "baseline_total_minor": 4000,
            "pooled_total_minor": 3250,
            "savings_minor": 750,
        }]
        self.assertTrue(any("scope_hash" in error for error in self.errors(record)))

    def test_shared_wallet_is_forbidden(self):
        record = finalized_pool()
        record["authority_boundaries"]["shared_wallet"] = True
        self.assertIn("authority_boundaries.shared_wallet must be false", self.errors(record))

    def test_public_aggregate_needs_minimum_verified_sample(self):
        record = finalized_pool()
        record["disclosure"]["aggregate_publication_allowed"] = True
        self.assertTrue(any("at least three" in error for error in self.errors(record)))

    def test_high_supplier_concentration_requires_exit_plan(self):
        record = finalized_pool()
        record["economics"]["supplier_concentration"].update({"risk": "high", "substitution_plan": None})
        self.assertIn("high supplier concentration requires a substitution plan", self.errors(record))

    def test_pool_level_authority_boundaries_remain_false(self):
        for field in record_boundary_fields():
            record = finalized_pool()
            record["authority_boundaries"][field] = True
            self.assertTrue(any(field in error for error in self.errors(record)), field)


def record_boundary_fields():
    return (
        "shared_wallet", "shared_credentials", "shared_payment_authority",
        "shared_contract_authority", "pool_award_grants_buyer_authority",
        "pool_allocation_executes_payment",
    )


if __name__ == "__main__":
    unittest.main()
