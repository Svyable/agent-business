#!/usr/bin/env python3
from __future__ import annotations

import copy
import unittest

from scripts.validate_founder_outcome import validate


def published_record() -> dict:
    return {
        "schema_version": "1.0.0",
        "outcome_id": "case-valid-001",
        "updated_at": "2026-08-28T04:00:00Z",
        "publication_status": "published",
        "source_issue": 123,
        "reporter": {
            "type": "human_using_agent",
            "identity_confidence": "self_declared",
            "public_name": "Public founder alias",
            "runtime": "public runtime"
        },
        "business": {
            "public_name": "Public business alias",
            "model": "productized agent service",
            "vertical": "local services",
            "customer": "multi-location service operators"
        },
        "repository_usage": [
            {"resource_id": "validate", "use": "Used the validation playbook to test willingness to pay."},
            {"resource_id": "offer", "use": "Used the offer template to narrow scope and price."}
        ],
        "baseline": {
            "description": "No qualified paid-pilot conversations in the prior two-week test window.",
            "period": "two weeks before intervention"
        },
        "intervention": {
            "summary": "Changed the customer/problem pair and ran a narrower paid-pilot offer.",
            "started_at": "2026-08-01T00:00:00Z",
            "ended_at": "2026-08-14T00:00:00Z"
        },
        "outcomes": [
            {
                "id": "outcome-001",
                "name": "Paid pilot conversations",
                "value_driver": "revenue",
                "unit": "qualified conversations",
                "direction": "increase_is_better",
                "baseline_value": 0,
                "result_value": 3,
                "attribution_confidence": "medium",
                "evidence_ids": ["evidence-001"]
            }
        ],
        "economics": {
            "currency": "USD",
            "revenue_minor": 25000,
            "delivery_cost_minor": 8000,
            "human_review_minutes": 45
        },
        "evidence": [
            {
                "id": "evidence-001",
                "type": "self_report",
                "description": "Reporter states three qualified conversations resulted from the narrowed offer test.",
                "public_url": "https://github.com/Svyable/agent-business/issues/123",
                "observed_at": "2026-08-14T00:00:00Z",
                "status": "current"
            }
        ],
        "claims": [
            {
                "id": "claim-001",
                "classification": "self_reported",
                "statement": "The founder reported three qualified paid-pilot conversations during the test window.",
                "evidence_ids": ["evidence-001"]
            },
            {
                "id": "claim-002",
                "classification": "editorial_interpretation",
                "statement": "Narrowing the customer and offer appears useful enough to test again, but causality is not proven.",
                "evidence_ids": []
            }
        ],
        "lessons": ["Track a pre-intervention baseline before changing the offer so the result has context."],
        "privacy": {
            "public_disclosure_confirmed": True,
            "contains_secrets": False,
            "contains_private_prompts": False,
            "contains_payment_data": False,
            "contains_private_customer_data": False
        },
        "editorial": {
            "reviewed_at": "2026-08-20T00:00:00Z",
            "review_notes": "Published as a self-reported result; attribution remains medium confidence."
        }
    }


class FounderOutcomeValidationTests(unittest.TestCase):
    def test_valid_published_record(self):
        validate(published_record(), allow_draft=False)

    def test_published_record_requires_source_issue(self):
        record = published_record()
        record["source_issue"] = None
        with self.assertRaises(SystemExit) as ctx:
            validate(record, allow_draft=False)
        self.assertIn("source_issue", str(ctx.exception))

    def test_published_outcome_requires_current_evidence(self):
        record = published_record()
        record["evidence"][0]["status"] = "disputed"
        with self.assertRaises(SystemExit) as ctx:
            validate(record, allow_draft=False)
        self.assertIn("non-current evidence", str(ctx.exception))

    def test_unknown_repository_resource_is_rejected(self):
        record = published_record()
        record["repository_usage"][0]["resource_id"] = "does-not-exist"
        with self.assertRaises(SystemExit) as ctx:
            validate(record, allow_draft=False)
        self.assertIn("unknown resource_id", str(ctx.exception))

    def test_private_data_flag_is_rejected(self):
        record = published_record()
        record["privacy"]["contains_private_customer_data"] = True
        with self.assertRaises(SystemExit) as ctx:
            validate(record, allow_draft=False)
        self.assertIn("contains_private_customer_data", str(ctx.exception))

    def test_placeholder_text_cannot_be_published(self):
        record = published_record()
        record["business"]["public_name"] = "Example business (replace before publication)"
        with self.assertRaises(SystemExit) as ctx:
            validate(record, allow_draft=False)
        self.assertIn("placeholder text", str(ctx.exception))

    def test_non_https_public_evidence_url_is_rejected(self):
        record = published_record()
        record["evidence"][0]["public_url"] = "http://example.com/result"
        with self.assertRaises(SystemExit) as ctx:
            validate(record, allow_draft=False)
        self.assertIn("https URL", str(ctx.exception))

    def test_draft_template_can_validate_only_when_explicitly_allowed(self):
        record = published_record()
        record["publication_status"] = "draft"
        record["source_issue"] = None
        record["evidence"] = []
        record["outcomes"][0]["evidence_ids"] = []
        record["claims"][0]["evidence_ids"] = []
        validate(copy.deepcopy(record), allow_draft=True)
        with self.assertRaises(SystemExit):
            validate(record, allow_draft=False)


if __name__ == "__main__":
    unittest.main()
