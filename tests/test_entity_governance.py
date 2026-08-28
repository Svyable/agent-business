#!/usr/bin/env python3
from __future__ import annotations

import copy
import unittest

from scripts.validate_entity_governance import validate


def current_evidence(eid: str, etype: str, sensitivity: str = "public") -> dict:
    return {
        "id": eid,
        "type": etype,
        "description": f"Current evidence for {eid}",
        "public_url": f"https://example.com/evidence/{eid}" if sensitivity == "public" else None,
        "private_reference": f"secure-record:{eid}" if sensitivity == "private_reference_only" else None,
        "observed_at": "2026-08-20T00:00:00Z",
        "effective_from": "2026-01-01T00:00:00Z",
        "expires_at": "2027-12-31T00:00:00Z",
        "status": "current",
        "sensitivity": sensitivity,
    }


def operational_record() -> dict:
    evidence = [
        current_evidence("formation", "formation_document"),
        current_evidence("governing", "governing_document", "private_reference_only"),
        current_evidence("cap", "cap_table", "private_reference_only"),
        current_evidence("bo", "professional_review", "private_reference_only"),
        current_evidence("bank", "bank_authority", "private_reference_only"),
        current_evidence("filing", "filing_receipt"),
        current_evidence("approval", "consent_or_resolution", "private_reference_only"),
    ]
    return {
        "schema_version": "1.0.0",
        "record_id": "entity-valid-001",
        "updated_at": "2026-08-28T04:00:00Z",
        "status": "operational",
        "entity": {
            "legal_name": "Public Example LLC",
            "entity_type": "limited liability company",
            "formation_jurisdiction": "US-DE",
            "formation_effective_at": "2026-01-01T00:00:00Z",
            "formation_evidence_ids": ["formation"],
            "registry_identifier_reference": "public-registry-record",
            "governing_document_evidence_ids": ["governing"],
            "good_standing": "current",
        },
        "ownership": {
            "cap_table_status": "current",
            "cap_table_evidence_ids": ["cap"],
            "beneficial_ownership_status": "current",
            "beneficial_ownership_evidence_ids": ["bo"],
            "equity_instrument_count": 1,
            "last_reconciled_at": "2026-08-20T00:00:00Z",
        },
        "authority": {
            "governance_body": "members",
            "material_actions_require_approval": True,
            "banking_authority_status": "current",
            "signatory_evidence_ids": ["bank"],
            "delegation_evidence_ids": [],
        },
        "obligations": [
            {
                "id": "annual-2026",
                "type": "annual_report",
                "jurisdiction": "US-DE",
                "status": "filed",
                "due_at": "2026-03-01T00:00:00Z",
                "evidence_ids": ["filing"],
            }
        ],
        "corporate_actions": [
            {
                "id": "banking-001",
                "action_type": "banking_change",
                "effective_at": "2026-08-21T00:00:00Z",
                "approval_evidence_ids": ["approval"],
                "status": "effective",
            }
        ],
        "evidence": evidence,
        "privacy": {
            "contains_raw_government_id": False,
            "contains_signature": False,
            "contains_bank_credentials": False,
            "contains_private_beneficial_owner_documents": False,
            "contains_secrets": False,
        },
        "review": {
            "human_review_required": True,
            "reviewed_at": "2026-08-22T00:00:00Z",
            "review_notes": "Operational evidence reviewed; jurisdiction-specific advice remains external.",
        },
    }


class EntityGovernanceTests(unittest.TestCase):
    def test_valid_operational_record(self):
        validate(operational_record())

    def test_unknown_formation_jurisdiction_fails_operational(self):
        record = operational_record()
        record["entity"]["formation_jurisdiction"] = "unknown"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("formation jurisdiction", str(ctx.exception))

    def test_stale_formation_evidence_fails(self):
        record = operational_record()
        record["evidence"][0]["status"] = "stale"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("non-current evidence", str(ctx.exception))

    def test_unresolved_beneficial_ownership_fails(self):
        record = operational_record()
        record["ownership"]["beneficial_ownership_status"] = "needs_review"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("beneficial-ownership", str(ctx.exception))

    def test_unknown_banking_authority_fails(self):
        record = operational_record()
        record["authority"]["banking_authority_status"] = "unknown"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("banking-authority", str(ctx.exception))

    def test_due_obligation_blocks_operational(self):
        record = operational_record()
        record["obligations"][0]["status"] = "due"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("unresolved obligations", str(ctx.exception))

    def test_filed_obligation_requires_evidence(self):
        record = operational_record()
        record["obligations"][0]["evidence_ids"] = []
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("requires evidence", str(ctx.exception))

    def test_effective_material_action_requires_approval(self):
        record = operational_record()
        record["corporate_actions"][0]["approval_evidence_ids"] = []
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("requires approval evidence", str(ctx.exception))

    def test_sensitive_field_is_rejected(self):
        record = operational_record()
        record["entity"]["ssn"] = "do-not-store"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("prohibited sensitive field", str(ctx.exception))

    def test_private_evidence_cannot_have_public_url(self):
        record = operational_record()
        record["evidence"][1]["public_url"] = "https://example.com/private"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("must not expose public_url", str(ctx.exception))

    def test_expired_current_evidence_fails(self):
        record = operational_record()
        record["evidence"][0]["expires_at"] = "2026-01-02T00:00:00Z"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("expired but marked current", str(ctx.exception))

    def test_material_actions_must_require_approval(self):
        record = operational_record()
        record["authority"]["material_actions_require_approval"] = False
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("material_actions_require_approval", str(ctx.exception))

    def test_safe_needs_review_template_shape_can_validate(self):
        record = operational_record()
        record["status"] = "needs_review"
        record["entity"]["formation_jurisdiction"] = "unknown"
        record["entity"]["formation_effective_at"] = None
        record["entity"]["formation_evidence_ids"] = []
        record["entity"]["governing_document_evidence_ids"] = []
        record["ownership"]["cap_table_status"] = "unknown"
        record["ownership"]["cap_table_evidence_ids"] = []
        record["ownership"]["beneficial_ownership_status"] = "unknown"
        record["ownership"]["beneficial_ownership_evidence_ids"] = []
        record["authority"]["banking_authority_status"] = "unknown"
        record["authority"]["signatory_evidence_ids"] = []
        record["obligations"] = []
        record["corporate_actions"] = []
        record["evidence"] = []
        record["review"]["reviewed_at"] = None
        validate(copy.deepcopy(record))


if __name__ == "__main__":
    unittest.main()
