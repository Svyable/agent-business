#!/usr/bin/env python3
from __future__ import annotations

import unittest

from scripts.validate_growth_experiment import validate


def current_evidence(eid: str, etype: str) -> dict:
    return {
        "id": eid,
        "type": etype,
        "status": "current",
        "description": f"Current {etype} evidence",
        "observed_at": "2026-08-28T12:00:00Z",
        "public_url": None,
    }


def valid_record() -> dict:
    return {
        "schema_version": "1.0.0",
        "experiment_id": "growth-valid-001",
        "status": "analyzed",
        "updated_at": "2026-08-28T12:00:00Z",
        "owner": "growth owner",
        "repository_resources": ["sell", "revenue-ops", "ip-data-rights"],
        "hypothesis": {
            "statement": "A narrower problem-led search campaign will produce qualified opportunities within the declared budget.",
            "primary_metric": "qualified_opportunities",
            "success_threshold": ">= 2 qualified opportunities",
            "guardrails": ["No suppressed-contact outreach"]
        },
        "audience": {
            "icp": "Service businesses with a documented workflow pain",
            "source": "Authorized contextual targeting",
            "consent_basis": "not_required",
            "suppression_enforced": True,
            "customer_data_use": "none"
        },
        "channel": {
            "type": "paid_search",
            "account_or_surface": "public search campaign",
            "claims_reviewed": True,
            "brand_assets_authorized": True
        },
        "metrics": {
            "spend_minor": 50000,
            "currency": "USD",
            "impressions": 10000,
            "clicks": 400,
            "qualified_leads": 8,
            "qualified_opportunities": 2,
            "observed_revenue_minor": 0,
            "platform_attributed_revenue_minor": 120000,
            "revenue_opportunity_ids": ["opp-001", "opp-002"]
        },
        "budget": {
            "daily_cap_minor": 10000,
            "lifetime_cap_minor": 75000,
            "reallocation_cap_bps": 2000,
            "stop_loss_minor": 60000
        },
        "attribution": {
            "source_platform": "Example Ads",
            "model": "platform_model",
            "lookback_window_days": 30,
            "identity_resolution": "Platform click identifier joined to authorized CRM conversion events.",
            "incrementality_method": "none",
            "causal_claim": False,
            "known_blind_spots": ["Cross-device identity is incomplete."]
        },
        "authority": {
            "can_publish": True,
            "can_spend": True,
            "max_spend_minor": 75000,
            "can_reallocate_budget": True,
            "can_change_audience": False,
            "can_change_claims": False,
            "authority_evidence_ids": ["auth"]
        },
        "evidence": [
            current_evidence("auth", "authority_record"),
            current_evidence("platform", "platform_report"),
            current_evidence("analysis", "experiment_output")
        ],
        "decision": {
            "action": "scale",
            "reason": "Qualified opportunity threshold was met within budget; attribution remains platform-reported, not causal.",
            "evidence_ids": ["platform", "analysis"]
        },
        "privacy": {
            "contains_raw_contacts": False,
            "contains_credentials": False,
            "contains_private_customer_data": False,
            "public_disclosure_confirmed": True
        }
    }


class GrowthExperimentValidationTests(unittest.TestCase):
    def test_valid_record(self):
        validate(valid_record())

    def test_spend_over_lifetime_cap_rejected(self):
        record = valid_record(); record["metrics"]["spend_minor"] = 80000
        with self.assertRaises(SystemExit): validate(record)

    def test_spend_authority_must_cover_cap(self):
        record = valid_record(); record["authority"]["max_spend_minor"] = 50000
        with self.assertRaises(SystemExit): validate(record)

    def test_material_authority_requires_current_evidence(self):
        record = valid_record(); record["evidence"][0]["status"] = "stale"
        with self.assertRaises(SystemExit): validate(record)

    def test_outbound_requires_consent_and_suppression(self):
        record = valid_record(); record["channel"]["type"] = "email"; record["audience"]["consent_basis"] = "unknown"
        with self.assertRaises(SystemExit): validate(record)

    def test_active_paid_media_requires_spend_authority(self):
        record = valid_record(); record["status"] = "running"; record["authority"]["can_spend"] = False
        with self.assertRaises(SystemExit): validate(record)

    def test_platform_attribution_requires_platform_evidence(self):
        record = valid_record(); record["evidence"] = [record["evidence"][0], record["evidence"][2]]
        with self.assertRaises(SystemExit): validate(record)

    def test_observed_revenue_requires_non_platform_evidence(self):
        record = valid_record(); record["metrics"]["observed_revenue_minor"] = 10000
        with self.assertRaises(SystemExit): validate(record)

    def test_causal_claim_rejects_pre_post(self):
        record = valid_record(); record["attribution"]["causal_claim"] = True; record["attribution"]["incrementality_method"] = "pre_post"
        with self.assertRaises(SystemExit): validate(record)

    def test_causal_claim_requires_experiment_output(self):
        record = valid_record(); record["attribution"]["causal_claim"] = True; record["attribution"]["incrementality_method"] = "randomized_holdout"; record["evidence"] = record["evidence"][:2]
        with self.assertRaises(SystemExit): validate(record)

    def test_scale_requires_budget_reallocation_authority_for_paid_media(self):
        record = valid_record(); record["authority"]["can_reallocate_budget"] = False
        with self.assertRaises(SystemExit): validate(record)

    def test_scale_rejects_stale_decision_evidence(self):
        record = valid_record(); record["evidence"][1]["status"] = "stale"
        with self.assertRaises(SystemExit): validate(record)

    def test_scale_rejects_stop_loss_with_no_opportunities(self):
        record = valid_record(); record["metrics"]["qualified_opportunities"] = 0; record["metrics"]["revenue_opportunity_ids"] = []; record["metrics"]["spend_minor"] = 60000
        with self.assertRaises(SystemExit): validate(record)

    def test_advanced_state_rejects_unknown_customer_data_use(self):
        record = valid_record(); record["audience"]["customer_data_use"] = "unknown"
        with self.assertRaises(SystemExit): validate(record)

    def test_unreviewed_claims_rejected_for_advanced_state(self):
        record = valid_record(); record["channel"]["claims_reviewed"] = False
        with self.assertRaises(SystemExit): validate(record)

    def test_sensitive_field_rejected(self):
        record = valid_record(); record["api_key"] = "should-never-be-here"
        with self.assertRaises(SystemExit): validate(record)

    def test_unknown_repository_resource_rejected(self):
        record = valid_record(); record["repository_resources"] = ["does-not-exist"]
        with self.assertRaises(SystemExit): validate(record)


if __name__ == "__main__":
    unittest.main()
