import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_agent_proposal", ROOT / "scripts" / "validate_agent_proposal.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


def starter():
    return json.loads((ROOT / "templates" / "AGENT_RFQ_PROPOSAL.json").read_text())


def submitted():
    record = starter()
    record.update({"status": "submitted", "updated_at": "2026-08-29T18:30:00Z", "proposal_version": "1.0.0"})
    record["request"].update({
        "request_id": "request.real-1",
        "request_version": "2.0.0",
        "request_digest": "sha256:request-real-1-v2",
        "bid_closes_at": "2026-08-30T18:00:00Z",
    })
    record["seller"].update({
        "listing_id": "listing.seller-1",
        "listing_version": "3.1.0",
        "listing_updated_at": "2026-08-29T17:00:00Z",
        "listing_evidence_state": "current",
        "listing_evidence_expires_at": "2026-09-05T00:00:00Z",
        "authority_state": "current",
        "authority_evidence_ref": "authority:seller-1:quote",
        "authority_effective_at": "2026-08-29T16:00:00Z",
        "authority_expires_at": "2026-09-05T00:00:00Z",
    })
    record["offer"].update({
        "currency": "USD",
        "total_price_minor": 25000,
        "pricing_basis": "fixed",
        "valid_until": "2026-08-31T00:00:00Z",
        "submitted_at": "2026-08-29T18:00:00Z",
        "delivery_due_at": "2026-09-03T00:00:00Z",
        "capacity_units": 100,
        "capacity_unit": "cases",
        "assumptions": ["Buyer provides complete structured case payloads."],
    })
    record["service_levels"].update({
        "availability_target": 0.99,
        "p95_latency_seconds": 15,
        "completion_deadline_seconds": 86400,
        "human_review": "exceptions_only",
    })
    record["compatibility"].update({"protocols": ["https_api"], "regions": ["US"]})
    record["eligibility"].update({
        "all_hard_requirements_satisfied": True,
        "eligible_for_award": True,
        "unresolved_hard_requirement_ids": [],
        "evaluated_against_request_version": "2.0.0",
    })
    record["payment"].update({
        "rail": "invoice_ach",
        "asset_or_currency": "USD",
        "settlement_semantics": "Settlement is final only after bank confirmation.",
        "payment_terms": "Net 15 after accepted delivery.",
    })
    record["acceptance"]["request_criteria_acknowledged"] = True
    record["normalization"].update({
        "comparison_currency": "USD",
        "comparable_total_minor": 25000,
        "quantity": 100,
        "quantity_unit": "cases",
        "normalization_method": "Direct fixed-price comparison; no FX or adjustments.",
    })
    return record


class ProposalTests(unittest.TestCase):
    def assert_invalid(self, record, needle, allow_draft=True):
        errors = MOD.validate_record(record, allow_draft=allow_draft)
        self.assertTrue(any(needle in error for error in errors), errors)

    def test_safe_starter_is_valid_draft(self):
        self.assertEqual(MOD.validate_record(starter(), allow_draft=True), [])

    def test_draft_requires_flag(self):
        self.assert_invalid(starter(), "--allow-draft", allow_draft=False)

    def test_valid_submitted_proposal(self):
        self.assertEqual(MOD.validate_record(submitted(), allow_draft=True), [])

    def test_stale_listing_cannot_support_submission(self):
        record = submitted()
        record["seller"]["listing_evidence_state"] = "stale"
        self.assert_invalid(record, "requires current seller listing evidence")

    def test_listing_evidence_expired_at_submission(self):
        record = submitted()
        record["seller"]["listing_evidence_expires_at"] = "2026-08-29T17:59:59Z"
        self.assert_invalid(record, "stale at submission")

    def test_expired_seller_authority_rejected(self):
        record = submitted()
        record["seller"]["authority_expires_at"] = "2026-08-29T17:00:00Z"
        self.assert_invalid(record, "submitted after seller authority expired")

    def test_submission_after_bid_close_rejected(self):
        record = submitted()
        record["request"]["bid_closes_at"] = "2026-08-29T17:00:00Z"
        self.assert_invalid(record, "after the RFQ bid window closed")

    def test_request_version_mismatch_rejected(self):
        record = submitted()
        record["eligibility"]["evaluated_against_request_version"] = "1.0.0"
        self.assert_invalid(record, "referenced request version")

    def test_hard_deviation_must_be_machine_visible_as_unresolved(self):
        record = submitted()
        record["deviations"] = [{
            "id": "sla-1", "dimension": "sla", "severity": "hard_requirement",
            "request_value": "completion within 4h", "proposed_value": "completion within 24h",
            "impact": "Misses buyer hard deadline.", "buyer_approval_required": True,
        }]
        self.assert_invalid(record, "unresolved_hard_requirement_ids")

    def test_hard_deviation_requires_buyer_approval(self):
        record = submitted()
        record["deviations"] = [{
            "id": "region-1", "dimension": "region", "severity": "hard_requirement",
            "request_value": "US only", "proposed_value": "US and EU",
            "impact": "Changes processing geography.", "buyer_approval_required": False,
        }]
        record["eligibility"].update({
            "all_hard_requirements_satisfied": False,
            "eligible_for_award": False,
            "unresolved_hard_requirement_ids": ["region-1"],
        })
        self.assert_invalid(record, "must require buyer approval")

    def test_bid_with_unresolved_hard_requirement_cannot_be_award_eligible(self):
        record = submitted()
        record["eligibility"].update({
            "all_hard_requirements_satisfied": False,
            "eligible_for_award": True,
            "unresolved_hard_requirement_ids": ["protocol-x"],
        })
        self.assert_invalid(record, "eligible_for_award requires all hard requirements satisfied")

    def test_payment_asset_difference_requires_explicit_deviation(self):
        record = submitted()
        record["payment"]["asset_or_currency"] = "USDC"
        self.assert_invalid(record, "requires an explicit payment deviation")

    def test_same_currency_normalization_cannot_silently_change_price(self):
        record = submitted()
        record["normalization"]["comparable_total_minor"] = 20000
        self.assert_invalid(record, "normalized total differs")

    def test_selected_requires_buyer_selection_evidence(self):
        record = submitted()
        record["status"] = "selected"
        self.assert_invalid(record, "buyer_selection_ref")

    def test_selection_after_quote_expiry_rejected(self):
        record = submitted()
        record["status"] = "selected"
        record["selection"].update({
            "buyer_selection_ref": "award:request.real-1:proposal.example-draft",
            "selected_at": "2026-09-01T00:00:00Z",
        })
        self.assert_invalid(record, "selected after quote validity expired")

    def test_nonselected_proposal_cannot_carry_selection_evidence(self):
        record = submitted()
        record["selection"]["buyer_selection_ref"] = "award:unexpected"
        self.assert_invalid(record, "must be null unless status is selected")

    def test_confidential_bid_data_rejected_from_public_record(self):
        record = starter()
        record["disclosure"]["contains_confidential_bid_data"] = True
        self.assert_invalid(record, "contains_confidential_bid_data must be false")


if __name__ == "__main__":
    unittest.main()
