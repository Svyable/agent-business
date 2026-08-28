#!/usr/bin/env python3
from __future__ import annotations

import copy
import unittest

from scripts.validate_ip_rights import validate


def commercial_record() -> dict:
    return {
        "schema_version": "1.0.0",
        "record_id": "ip-case-valid-001",
        "updated_at": "2026-08-28T08:00:00Z",
        "status": "commercial_ready",
        "intended_use": {
            "product": "Paid customer agent service",
            "commercial": True,
            "redistribution": False,
            "training_or_finetuning": False,
            "customer_deliverable": True,
        },
        "assets": [
            {
                "id": "model-001",
                "kind": "model_weights",
                "name": "Model dependency",
                "source": "Public provider model page",
                "rights_status": "licensed",
                "commercial_use": "allowed",
                "redistribution": "prohibited",
                "derivatives": "conditional",
                "training_reuse": "conditional",
                "customer_input": False,
                "attribution_required": "no",
                "attribution_text_reference": None,
                "terms_version": "2026-04",
                "effective_at": "2026-04-02T00:00:00Z",
                "expires_at": None,
                "evidence_ids": ["ev-model"],
                "conflicts": [],
            }
        ],
        "customer_terms": {
            "input_use": "allowed_for_service",
            "training_reuse": "prohibited",
            "deliverable_ownership_promise": "license",
            "provider_pass_through_reviewed": True,
            "evidence_ids": ["ev-customer"],
        },
        "output_rights": {
            "provider_claim": "provider_disclaims_ownership",
            "founder_claim": "license_only",
            "infringement_review_required": True,
            "human_contribution_relevant": True,
            "evidence_ids": ["ev-model", "ev-customer"],
        },
        "evidence": [
            {
                "id": "ev-model",
                "type": "provider_terms",
                "description": "Public provider terms and exact model/version reviewed.",
                "public_url": "https://example.com/model-terms",
                "private_reference": None,
                "observed_at": "2026-08-20T00:00:00Z",
                "expires_at": None,
                "status": "current",
            },
            {
                "id": "ev-customer",
                "type": "customer_contract_reference",
                "description": "Private contract metadata reference; no agreement text stored here.",
                "public_url": None,
                "private_reference": "contract-record-123",
                "observed_at": "2026-08-20T00:00:00Z",
                "expires_at": None,
                "status": "current",
            },
        ],
        "review": {
            "legal_review_required": True,
            "owner_review_required": True,
            "reviewed_at": "2026-08-21T00:00:00Z",
            "blockers": [],
        },
        "privacy": {
            "public_safe": True,
            "contains_secret": False,
            "contains_private_contract_text": False,
            "contains_private_customer_content": False,
            "contains_restricted_dataset_content": False,
            "contains_private_prompt": False,
        },
    }


class IPRightsValidationTests(unittest.TestCase):
    def test_valid_commercial_record(self):
        validate(commercial_record())

    def test_unknown_commercial_rights_block_ready(self):
        record = commercial_record()
        record["assets"][0]["commercial_use"] = "unknown"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("commercial-use permission", str(ctx.exception))

    def test_noncommercial_asset_blocks_paid_product(self):
        record = commercial_record()
        record["assets"][0]["commercial_use"] = "prohibited"
        with self.assertRaises(SystemExit):
            validate(record)

    def test_unknown_rights_status_blocks_ready(self):
        record = commercial_record()
        record["assets"][0]["rights_status"] = "unknown"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("unresolved/incompatible rights", str(ctx.exception))

    def test_stale_evidence_blocks_ready(self):
        record = commercial_record()
        record["evidence"][0]["status"] = "stale"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("non-current evidence", str(ctx.exception))

    def test_attribution_obligation_needs_reference(self):
        record = commercial_record()
        record["assets"][0]["attribution_required"] = "yes"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("attribution reference", str(ctx.exception))

    def test_redistribution_permission_required_when_shipping_asset(self):
        record = commercial_record()
        record["intended_use"]["redistribution"] = True
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("redistribution permission", str(ctx.exception))

    def test_customer_training_reuse_must_be_resolved(self):
        record = commercial_record()
        record["intended_use"]["training_or_finetuning"] = True
        record["assets"][0]["training_reuse"] = "allowed"
        record["customer_terms"]["training_reuse"] = "unknown"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("customer data", str(ctx.exception))

    def test_customer_input_rights_cannot_be_unknown(self):
        record = commercial_record()
        record["customer_terms"]["input_use"] = "unknown"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("input-use rights", str(ctx.exception))

    def test_output_ownership_claim_must_be_resolved(self):
        record = commercial_record()
        record["output_rights"]["founder_claim"] = "unknown"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("output-rights claims", str(ctx.exception))

    def test_provider_pass_through_must_be_reviewed(self):
        record = commercial_record()
        record["customer_terms"]["provider_pass_through_reviewed"] = False
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("pass-through review", str(ctx.exception))

    def test_unresolved_conflict_blocks_ready(self):
        record = commercial_record()
        record["assets"][0]["conflicts"] = ["Customer promise conflicts with provider restriction."]
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("unresolved rights conflicts", str(ctx.exception))

    def test_private_contract_text_flag_is_rejected(self):
        record = commercial_record()
        record["privacy"]["contains_private_contract_text"] = True
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("contains_private_contract_text", str(ctx.exception))

    def test_raw_contract_text_field_is_rejected(self):
        record = commercial_record()
        record["contract_text"] = "private terms"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("prohibited sensitive/content field", str(ctx.exception))

    def test_needs_review_allows_unknown_rights(self):
        record = commercial_record()
        record["status"] = "needs_review"
        record["assets"][0]["rights_status"] = "unknown"
        record["assets"][0]["commercial_use"] = "unknown"
        record["assets"][0]["evidence_ids"] = []
        record["customer_terms"]["input_use"] = "unknown"
        record["customer_terms"]["deliverable_ownership_promise"] = "unknown"
        record["customer_terms"]["provider_pass_through_reviewed"] = False
        record["customer_terms"]["evidence_ids"] = []
        record["output_rights"]["provider_claim"] = "unknown"
        record["output_rights"]["founder_claim"] = "unknown"
        record["output_rights"]["evidence_ids"] = []
        record["review"]["reviewed_at"] = None
        record["review"]["blockers"] = ["Resolve rights before commercial use."]
        validate(copy.deepcopy(record))


if __name__ == "__main__":
    unittest.main()
