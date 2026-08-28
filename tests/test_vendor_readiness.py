#!/usr/bin/env python3
from __future__ import annotations

import copy
import unittest

from scripts.validate_vendor_readiness import validate


def ready_record() -> dict:
    categories = [
        "security","privacy","data","identity_authority","observability",
        "incident_response","reliability","bcp_dr","ai_governance"
    ]
    evidence = [
        {
            "id": "evidence-control",
            "type": "public_artifact",
            "description": "Public control evidence for test fixture.",
            "public_url": "https://github.com/Svyable/agent-business",
            "observed_at": "2026-08-01T00:00:00Z",
            "expires_at": "2027-08-01T00:00:00Z",
            "status": "current",
            "scope": "Test fixture only."
        },
        {
            "id": "evidence-cert",
            "type": "third_party_audit",
            "description": "Synthetic third-party evidence fixture; not a real certification.",
            "public_url": "https://example.com/audit-fixture",
            "observed_at": "2026-08-01T00:00:00Z",
            "expires_at": "2027-08-01T00:00:00Z",
            "status": "current",
            "scope": "Unit test fixture only."
        }
    ]
    controls = [
        {
            "id": f"control-{category}",
            "category": category,
            "assertion": f"Test assertion for {category}.",
            "status": "self_attested",
            "evidence_ids": ["evidence-control"],
            "owner": "security-owner",
            "notes": None
        }
        for category in categories
    ]
    return {
        "schema_version": "1.0.0",
        "record_id": "vendor-ready-test-001",
        "updated_at": "2026-08-28T07:00:00Z",
        "readiness_status": "buyer_ready",
        "organization": {"public_name": "Test Vendor", "entity_evidence_ref": "entity-governance-test"},
        "offering": {
            "name": "Test Agent",
            "description": "Unit-test enterprise agent offering.",
            "deployment_model": "vendor_saas",
            "production_authority_granted": False
        },
        "controls": controls,
        "evidence": evidence,
        "certifications": [
            {"name": "Synthetic Certification", "status": "held", "scope": "Unit test only", "evidence_ids": ["evidence-cert"]}
        ],
        "subprocessors": [
            {
                "name": "Test Processor", "purpose": "Unit test", "data_categories": ["test data"],
                "processing_regions": ["US"], "status": "current", "evidence_ids": ["evidence-control"]
            }
        ],
        "data_handling": {
            "customer_data_used_for_training": "no",
            "input_retention": "30 days",
            "output_retention": "30 days",
            "residency_claim": "US processing for this test fixture.",
            "evidence_ids": ["evidence-control"]
        },
        "agent_governance": {
            "identity_model": "Unique workload identity.",
            "tool_authority_model": "Least privilege policy.",
            "human_oversight": "Approval for consequential action.",
            "change_control": "Reviewed versioned changes.",
            "rollback": "Version rollback and kill switch.",
            "evidence_ids": ["evidence-control"]
        },
        "questionnaire_answers": [
            {
                "id": "answer-001", "question": "Is access least privilege?", "answer": "Yes, within test fixture.",
                "answer_type": "reusable", "evidence_ids": ["evidence-control"], "owner_reviewed": True
            }
        ],
        "pilot_to_production": {
            "pilot_data_scope": "Synthetic data only.",
            "pilot_authority_scope": "No external actions.",
            "production_data_approved": False,
            "production_authority_approved": False,
            "security_review_complete": True,
            "legal_commercial_review_complete": True
        },
        "privacy": {
            "public_safe": True,
            "contains_secrets": False,
            "contains_credentials": False,
            "contains_private_customer_questionnaire": False,
            "contains_restricted_security_report": False,
            "contains_private_architecture": False
        }
    }


class VendorReadinessTests(unittest.TestCase):
    def test_valid_buyer_ready_record(self):
        validate(ready_record())

    def test_vendor_readiness_never_grants_production_authority(self):
        record = ready_record()
        record["offering"]["production_authority_granted"] = True
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("never grants production authority", str(ctx.exception))

    def test_fabricated_certification_without_evidence_rejected(self):
        record = ready_record()
        record["certifications"][0]["evidence_ids"] = []
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("requires evidence", str(ctx.exception))

    def test_verified_control_cannot_use_only_self_attestation(self):
        record = ready_record()
        record["evidence"][0]["type"] = "self_attestation"
        record["controls"][0]["status"] = "verified"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("stronger than self-attestation", str(ctx.exception))

    def test_expired_evidence_cannot_be_current(self):
        record = ready_record()
        record["evidence"][0]["expires_at"] = "2026-08-02T00:00:00Z"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("expired but marked current", str(ctx.exception))

    def test_unknown_data_training_state_blocks_buyer_ready(self):
        record = ready_record()
        record["data_handling"]["customer_data_used_for_training"] = "unknown"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("training use unknown", str(ctx.exception))

    def test_unknown_residency_blocks_buyer_ready(self):
        record = ready_record()
        record["data_handling"]["residency_claim"] = "Unknown pending vendor review"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("unknown residency", str(ctx.exception))

    def test_current_subprocessor_needs_region(self):
        record = ready_record()
        record["subprocessors"][0]["processing_regions"] = []
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("processing_regions", str(ctx.exception))

    def test_customer_specific_answer_requires_review(self):
        record = ready_record()
        record["questionnaire_answers"][0]["answer_type"] = "customer_specific"
        record["questionnaire_answers"][0]["owner_reviewed"] = False
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("requires owner review", str(ctx.exception))

    def test_production_authority_gate_requires_reviews(self):
        record = ready_record()
        record["pilot_to_production"]["production_authority_approved"] = True
        record["pilot_to_production"]["security_review_complete"] = False
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("requires security and legal", str(ctx.exception))

    def test_missing_required_control_blocks_buyer_ready(self):
        record = ready_record()
        record["controls"][0]["status"] = "missing"
        record["controls"][0]["evidence_ids"] = []
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("unresolved required controls", str(ctx.exception))

    def test_sensitive_raw_security_report_key_rejected(self):
        record = ready_record()
        record["security_report_raw"] = "do not store this"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("prohibited sensitive field", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
