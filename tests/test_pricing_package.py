#!/usr/bin/env python3
from __future__ import annotations

import copy
import unittest

from scripts.validate_pricing_package import validate


def valid_quote() -> dict:
    return {
        "schema_version": "1.0.0",
        "package_id": "support-outcome-growth",
        "updated_at": "2026-08-28T09:50:00Z",
        "status": "quote_ready",
        "currency": "USD",
        "pricing_model": "outcome",
        "customer_segment": "B2B software support teams with 2,000-20,000 monthly conversations",
        "meter": {
            "name": "verified resolution",
            "unit": "resolved_conversation",
            "trigger": "verified_outcome",
            "definition": "One conversation is billable after the configured resolution test passes and no excluded customer-side or provider-failure condition applies.",
            "deduplication_key": "conversation_id",
            "customer_verifiable": True,
            "acceptance_window_hours": 72,
            "exclusions": ["provider retries", "duplicate delivery events", "failed workflows", "internal test traffic"]
        },
        "outcome_policy": {
            "success_definition": "The customer confirms resolution or the agreed 72-hour acceptance window closes without a request for further help.",
            "attribution_rule": "Only the final accepted resolution for one canonical conversation identifier is attributable to this package and billable once.",
            "customer_failure_exclusions": ["customer does not supply required account access"],
            "dispute_window_hours": 168,
            "evidence_ids": ["ev-outcome"]
        },
        "commercial_terms": {
            "billing_period": "monthly",
            "base_fee_minor": 50000,
            "minimum_commitment_minor": 100000,
            "included_units": 500,
            "unit_price_minor": 200,
            "overage_price_minor": 200,
            "hard_spend_cap_minor": 500000,
            "discount_bps": 500,
            "setup_fee_minor": 25000,
            "service_credit_cap_minor": 20000,
            "effective_from": "2026-09-01T00:00:00Z",
            "effective_until": "2027-09-01T00:00:00Z",
            "quote_expires_at": "2026-09-15T00:00:00Z",
            "change_notice_days": 30
        },
        "economics": {
            "expected_cost_per_billable_unit_minor": 70,
            "expected_net_price_per_unit_minor": 190,
            "target_contribution_margin_bps": 6500,
            "minimum_contribution_margin_bps": 5000,
            "workflow_roi_record": "templates/WORKFLOW_ROI_ANALYSIS.json",
            "evidence_ids": ["ev-cost"]
        },
        "budget_controls": {
            "usage_alert_percentages": [50, 80, 95],
            "hard_cap_behavior": "request_approval",
            "overage_requires_approval": False,
            "no_surprise_billing": True
        },
        "authority": {
            "source": "approved commercial policy v3",
            "can_issue_quote": True,
            "max_discount_bps": 1000,
            "can_waive_setup": False,
            "can_change_minimum": False,
            "can_grant_credits": True,
            "max_credit_minor": 50000,
            "can_activate_nonstandard_terms": False,
            "reviewed_at": "2026-08-27T00:00:00Z"
        },
        "evidence": [
            {"id":"ev-outcome","type":"customer_evidence","description":"Pilot acceptance criteria and dispute test were reviewed with the buyer.","status":"current","observed_at":"2026-08-27T00:00:00Z","public_url":None},
            {"id":"ev-cost","type":"workflow_economics","description":"Observed delivery-cost sample supports the base-case cost per accepted outcome.","status":"current","observed_at":"2026-08-27T00:00:00Z","public_url":None}
        ],
        "privacy": {"contains_secrets":False,"contains_payment_credentials":False,"contains_private_customer_data":False}
    }


class PricingPackageTests(unittest.TestCase):
    def test_valid_quote(self):
        validate(valid_quote())

    def test_outcome_pricing_requires_policy(self):
        record = valid_quote(); record["outcome_policy"] = None
        with self.assertRaises(SystemExit): validate(record)

    def test_customer_verifiable_meter_required(self):
        record = valid_quote(); record["meter"]["customer_verifiable"] = False
        with self.assertRaises(SystemExit): validate(record)

    def test_retry_and_duplicate_exclusions_required(self):
        record = valid_quote(); record["meter"]["exclusions"] = ["failed workflows"]
        with self.assertRaises(SystemExit): validate(record)

    def test_stale_economics_evidence_rejected(self):
        record = valid_quote(); record["evidence"][1]["status"] = "stale"
        with self.assertRaises(SystemExit): validate(record)

    def test_negative_margin_quote_rejected(self):
        record = valid_quote(); record["economics"]["expected_cost_per_billable_unit_minor"] = 150
        with self.assertRaises(SystemExit): validate(record)

    def test_discount_over_authority_rejected(self):
        record = valid_quote(); record["commercial_terms"]["discount_bps"] = 1500
        with self.assertRaises(SystemExit): validate(record)

    def test_unauthorized_credit_rejected(self):
        record = valid_quote(); record["authority"]["can_grant_credits"] = False
        with self.assertRaises(SystemExit): validate(record)

    def test_expired_quote_rejected(self):
        record = valid_quote(); record["commercial_terms"]["quote_expires_at"] = "2026-08-27T00:00:00Z"
        with self.assertRaises(SystemExit): validate(record)

    def test_uncapped_overage_needs_approval(self):
        record = valid_quote(); record["commercial_terms"]["hard_spend_cap_minor"] = None; record["budget_controls"]["overage_requires_approval"] = False
        with self.assertRaises(SystemExit): validate(record)

    def test_quote_authority_required(self):
        record = valid_quote(); record["authority"]["can_issue_quote"] = False
        with self.assertRaises(SystemExit): validate(record)

    def test_sensitive_field_rejected(self):
        record = valid_quote(); record["api_key"] = "should-never-be-here"
        with self.assertRaises(SystemExit): validate(record)

    def test_needs_review_starter_can_be_zero_authority(self):
        record = valid_quote()
        record["status"] = "needs_review"
        record["authority"]["can_issue_quote"] = False
        record["authority"]["source"] = None
        record["authority"]["reviewed_at"] = None
        record["commercial_terms"]["discount_bps"] = 0
        record["commercial_terms"]["service_credit_cap_minor"] = 0
        record["economics"]["evidence_ids"] = []
        record["evidence"] = []
        validate(copy.deepcopy(record))


if __name__ == "__main__":
    unittest.main()
