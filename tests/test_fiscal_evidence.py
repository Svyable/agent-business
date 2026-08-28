#!/usr/bin/env python3
from __future__ import annotations

import copy
import unittest

from scripts.validate_fiscal_evidence import validate


def base_evidence() -> list[dict]:
    return [
        {
            "id": "ev-jurisdiction",
            "type": "tax_authority",
            "description": "Current jurisdiction and place-of-supply evidence for the test fixture.",
            "source": "https://example.test/tax-authority/jurisdiction",
            "observed_at": "2026-08-20T00:00:00Z",
            "valid_until": "2027-01-01T00:00:00Z",
            "status": "current",
        },
        {
            "id": "ev-tax",
            "type": "tax_authority",
            "description": "Current tax treatment evidence for the test fixture.",
            "source": "https://example.test/tax-authority/treatment",
            "observed_at": "2026-08-20T00:00:00Z",
            "valid_until": "2027-01-01T00:00:00Z",
            "status": "current",
        },
        {
            "id": "ev-invoice",
            "type": "invoice_standard",
            "description": "Current invoice-format requirement evidence for the test fixture.",
            "source": "https://example.test/invoice-standard",
            "observed_at": "2026-08-20T00:00:00Z",
            "valid_until": "2027-01-01T00:00:00Z",
            "status": "current",
        },
    ]


def operational_record() -> dict:
    return {
        "schema_version": "1.0.0",
        "record_id": "fiscal-test-001",
        "updated_at": "2026-08-28T04:10:00Z",
        "status": "ready_to_invoice",
        "transaction": {
            "transaction_id": "txn-001",
            "occurred_at": "2026-08-28T04:00:00Z",
            "type": "service",
            "description": "Test fixture professional service",
            "amount_minor": 10000,
            "currency": "USD",
            "original_transaction_id": None,
        },
        "parties": {
            "seller": {
                "party_id": "seller-001",
                "country": "US",
                "tax_registration_status": "registered",
                "tax_id_reference": "internal-tax-profile-seller",
                "entity_type": "company",
            },
            "buyer": {
                "party_id": "buyer-001",
                "country": "US",
                "tax_registration_status": "registered",
                "tax_id_reference": "internal-tax-profile-buyer",
                "entity_type": "company",
            },
            "platform": None,
        },
        "jurisdiction": {
            "determination_status": "confirmed",
            "seller_country": "US",
            "buyer_country": "US",
            "supply_country": "US",
            "subdivision": "TEST",
            "ruleset": "test fiscal ruleset",
            "ruleset_version": "2026-08",
            "valid_from": "2026-01-01T00:00:00Z",
            "valid_until": "2027-01-01T00:00:00Z",
            "evidence_ids": ["ev-jurisdiction"],
        },
        "tax_determination": {
            "status": "confirmed",
            "tax_type": "sales_tax",
            "treatment": "standard",
            "rate_bps": 500,
            "tax_amount_minor": 500,
            "reason": "Fixture-only confirmed treatment.",
            "registration_required": "yes",
            "registration_reference": "internal-tax-profile-seller",
            "exemption_reference": None,
            "reverse_charge_reference": None,
            "evidence_ids": ["ev-tax"],
        },
        "invoice": {
            "required": "yes",
            "status": "validated",
            "document_type": "invoice",
            "invoice_id": "INV-001",
            "issue_date": "2026-08-28",
            "format": "test-machine-invoice",
            "profile": "test-profile-2026",
            "original_invoice_id": None,
            "evidence_ids": ["ev-invoice"],
        },
        "withholding": {
            "status": "not_applicable",
            "rate_bps": None,
            "amount_minor": None,
            "form_or_certificate": None,
            "evidence_ids": [],
        },
        "platform_reporting": {
            "status": "not_applicable",
            "regime": None,
            "seller_reportable": "no",
            "reporting_period": None,
            "evidence_ids": [],
        },
        "currency": {
            "transaction_currency": "USD",
            "accounting_currency": "USD",
            "fx_required": False,
            "rate": None,
            "rate_source": None,
            "rate_observed_at": None,
            "evidence_ids": [],
        },
        "evidence": base_evidence(),
        "approvals": {
            "human_review_required": False,
            "review_status": "not_required",
            "review_reason": "Fixture assumes deterministic policy is approved for this exact transaction class.",
            "reviewed_at": None,
            "reviewer_role": None,
        },
        "privacy": {
            "contains_payment_credentials": False,
            "contains_secrets": False,
            "contains_private_prompts": False,
            "contains_unnecessary_personal_data": False,
        },
    }


class FiscalEvidenceValidationTests(unittest.TestCase):
    def test_safe_starter_shape_can_remain_needs_review(self):
        record = operational_record()
        record["status"] = "needs_review"
        record["jurisdiction"]["determination_status"] = "unknown"
        record["jurisdiction"]["supply_country"] = None
        record["jurisdiction"]["ruleset"] = None
        record["jurisdiction"]["evidence_ids"] = []
        record["tax_determination"]["status"] = "unknown"
        record["tax_determination"]["treatment"] = "unknown"
        record["tax_determination"]["rate_bps"] = None
        record["tax_determination"]["tax_amount_minor"] = None
        record["tax_determination"]["registration_required"] = "unknown"
        record["tax_determination"]["evidence_ids"] = []
        record["invoice"]["required"] = "unknown"
        record["invoice"]["status"] = "not_started"
        record["invoice"]["invoice_id"] = None
        record["invoice"]["issue_date"] = None
        record["invoice"]["format"] = None
        record["invoice"]["evidence_ids"] = []
        record["withholding"]["status"] = "unknown"
        record["platform_reporting"]["status"] = "unknown"
        record["platform_reporting"]["seller_reportable"] = "unknown"
        record["approvals"] = {
            "human_review_required": True,
            "review_status": "pending",
            "review_reason": "Fiscal determinations remain unresolved.",
            "reviewed_at": None,
            "reviewer_role": None,
        }
        validate(record)

    def test_operational_record_validates(self):
        validate(operational_record())

    def test_unknown_jurisdiction_cannot_be_operational(self):
        record = operational_record()
        record["jurisdiction"]["determination_status"] = "unknown"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("confirmed jurisdiction", str(ctx.exception))

    def test_unknown_registration_blocks_operational_state(self):
        record = operational_record()
        record["tax_determination"]["registration_required"] = "unknown"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("registration determination", str(ctx.exception))

    def test_non_current_tax_evidence_blocks_operational_state(self):
        record = operational_record()
        record["evidence"][1]["status"] = "stale"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("non-current evidence", str(ctx.exception))

    def test_required_invoice_needs_validated_machine_format(self):
        record = operational_record()
        record["invoice"]["format"] = None
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("declared format", str(ctx.exception))

    def test_refund_requires_original_transaction_link(self):
        record = operational_record()
        record["transaction"]["type"] = "refund"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("original_transaction_id", str(ctx.exception))

    def test_correction_requires_original_invoice(self):
        record = operational_record()
        record["status"] = "corrected"
        record["invoice"]["status"] = "corrected"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("original_invoice_id", str(ctx.exception))

    def test_cross_currency_requires_fx_provenance(self):
        record = operational_record()
        record["currency"]["accounting_currency"] = "EUR"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("fx_required", str(ctx.exception))

    def test_fx_operational_record_needs_source_evidence(self):
        record = operational_record()
        record["currency"].update({
            "accounting_currency": "EUR",
            "fx_required": True,
            "rate": 0.85,
            "rate_source": "approved closing-rate source",
            "rate_observed_at": "2026-08-28T00:00:00Z",
            "evidence_ids": [],
        })
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("FX conversion requires source evidence", str(ctx.exception))

    def test_sensitive_fields_are_rejected(self):
        record = operational_record()
        record["authorization"] = "Bearer should-never-be-here"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("prohibited sensitive field", str(ctx.exception))

    def test_human_review_must_be_approved_before_operational_state(self):
        record = operational_record()
        record["approvals"] = {
            "human_review_required": True,
            "review_status": "pending",
            "review_reason": "Qualified review required by policy.",
            "reviewed_at": None,
            "reviewer_role": None,
        }
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("must be approved", str(ctx.exception))

    def test_confirmed_tax_needs_amount(self):
        record = operational_record()
        record["tax_determination"]["tax_amount_minor"] = None
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("tax_amount_minor", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
