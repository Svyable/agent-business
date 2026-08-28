#!/usr/bin/env python3
from __future__ import annotations

import copy
import unittest

from scripts.validate_revenue_opportunity import validate


def active_record() -> dict:
    return {
        "schema_version": "1.0.0",
        "opportunity_id": "opp-valid-001",
        "updated_at": "2026-08-28T11:00:00Z",
        "record_status": "active",
        "stage": "qualified_opportunity",
        "account": {"public_alias": "Acme alias", "segment": "mid-market services", "duplicate_key": "acme-alias"},
        "stakeholders": [
            {"role": "champion", "identity_state": "observed", "public_alias": "Champion alias", "evidence_ids": ["buyer-1"]}
        ],
        "qualification": {
            "problem": "observed", "value": "estimated", "timing": "inferred", "decision_process": "inferred",
            "expected_value_minor": 500000, "currency": "USD", "stage_evidence_ids": ["buyer-1"]
        },
        "forecast": {
            "category": "pipeline", "probability_bps": 3000, "close_date": "2026-10-01",
            "seller_confidence": "medium", "evidence_ids": ["buyer-1"]
        },
        "next_action": {
            "type": "meeting", "due_at": "2026-08-30T15:00:00Z", "owner": "founder",
            "requires_external_contact": True, "evidence_ids": ["buyer-1"]
        },
        "commercial": {
            "pricing_package_id": None, "quote_status": "none", "accepted_scope": None,
            "success_criteria": None, "blockers": []
        },
        "authority": {
            "can_write_crm": True, "can_contact": True, "can_change_stage": True,
            "can_send_quote": False, "can_make_pricing_claims": False,
            "can_commit_forecast": False, "can_mark_won_lost": False,
            "source": "founder authority envelope", "reviewed_at": "2026-08-28T10:00:00Z"
        },
        "evidence": [
            {"id": "buyer-1", "type": "buyer_statement", "status": "current", "observed_at": "2026-08-27T15:00:00Z", "description": "Buyer described a painful workflow and agreed to a follow-up meeting.", "public_url": None}
        ],
        "privacy": {"contains_secrets": False, "contains_private_contact_data": False, "contains_raw_customer_content": False, "public_example_safe": True}
    }


class RevenueOpportunityTests(unittest.TestCase):
    def test_valid_qualified_opportunity(self):
        validate(active_record())

    def test_stage_cannot_advance_on_inferred_problem(self):
        record = active_record()
        record["qualification"]["problem"] = "inferred"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("observed problem", str(ctx.exception))

    def test_seller_inference_alone_cannot_support_stage(self):
        record = active_record()
        record["evidence"][0]["type"] = "seller_inference"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("seller inference alone", str(ctx.exception))

    def test_stale_evidence_rejected_for_stage(self):
        record = active_record()
        record["evidence"][0]["status"] = "stale"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("non-current evidence", str(ctx.exception))

    def test_external_contact_needs_contact_authority(self):
        record = active_record()
        record["authority"]["can_contact"] = False
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("can_contact", str(ctx.exception))

    def test_commit_requires_economic_buyer(self):
        record = active_record()
        record["stage"] = "commit"
        record["forecast"].update({"category": "commit", "probability_bps": 8000})
        record["commercial"].update({"pricing_package_id": "package-1", "quote_status": "sent"})
        record["authority"]["can_commit_forecast"] = True
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("economic_buyer", str(ctx.exception))

    def test_commit_forecast_requires_buyer_evidence(self):
        record = active_record()
        record["stage"] = "commit"
        record["stakeholders"].append({"role": "economic_buyer", "identity_state": "observed", "public_alias": "Buyer alias", "evidence_ids": ["buyer-1"]})
        record["forecast"].update({"category": "commit", "probability_bps": 8000, "evidence_ids": ["infer-1"]})
        record["commercial"].update({"pricing_package_id": "package-1", "quote_status": "sent"})
        record["authority"]["can_commit_forecast"] = True
        record["evidence"].append({"id": "infer-1", "type": "seller_inference", "status": "current", "observed_at": "2026-08-28T09:00:00Z", "description": "Agent estimates deal will close.", "public_url": None})
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("seller inference alone", str(ctx.exception))

    def test_quote_action_requires_quote_authority(self):
        record = active_record()
        record["next_action"]["type"] = "quote"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("can_send_quote", str(ctx.exception))

    def test_won_requires_accepted_scope_and_success_criteria(self):
        record = active_record()
        record["stage"] = "won"
        record["record_status"] = "closed"
        record["stakeholders"].append({"role": "economic_buyer", "identity_state": "observed", "public_alias": "Buyer alias", "evidence_ids": ["buyer-1"]})
        record["forecast"].update({"category": "closed", "probability_bps": 10000})
        record["commercial"].update({"pricing_package_id": "package-1", "quote_status": "accepted"})
        record["authority"]["can_mark_won_lost"] = True
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("accepted scope", str(ctx.exception))

    def test_closing_requires_won_lost_authority(self):
        record = active_record()
        record["stage"] = "lost"
        record["record_status"] = "closed"
        record["forecast"]["category"] = "closed"
        record["next_action"]["type"] = "none"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("can_mark_won_lost", str(ctx.exception))

    def test_private_contact_data_rejected(self):
        record = active_record()
        record["privacy"]["contains_private_contact_data"] = True
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("contains_private_contact_data", str(ctx.exception))

    def test_sensitive_field_rejected(self):
        record = active_record()
        record["api_key"] = "not-real"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("prohibited sensitive field", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
