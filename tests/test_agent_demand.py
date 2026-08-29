import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_agent_demand", ROOT / "scripts" / "validate_agent_demand.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


def starter():
    return json.loads((ROOT / "templates" / "AGENT_DEMAND_REQUEST.json").read_text())


def commercial():
    record = starter()
    record.update({"status": "published", "demand_quality": "verified_commercial", "updated_at": "2026-08-29T12:00:00Z"})
    record["buyer"].update({"identity_confidence": "platform_verified"})
    record["outcome"].update({"quantity_min": 100, "quantity_max": 200, "quantity_unit": "cases", "recurrence": "monthly"})
    record["requirements"].update({
        "inputs": ["structured case payload"],
        "outputs": ["validated completed case"],
        "hard_constraints": ["HTTPS API required", "US processing only"],
        "required_protocols": ["https_api"],
        "regions": ["US"],
        "human_review": "exceptions_only",
    })
    record["budget"].update({"currency": "USD", "public_min_minor": 10000, "public_max_minor": 50000, "budget_disclosed": True})
    record["timing"].update({"bid_opens_at": "2026-08-29T12:00:00Z", "bid_closes_at": "2026-08-30T12:00:00Z", "delivery_due_at": "2026-09-05T12:00:00Z"})
    record["authority"].update({
        "authority_state": "current", "authority_evidence_ref": "authority:example-1",
        "authorized_currency": "USD", "max_authorized_spend_minor": 60000,
        "effective_at": "2026-08-29T10:00:00Z", "expires_at": "2026-09-10T00:00:00Z",
    })
    record["bidding"].update({"mode": "public", "award_method": "weighted_score"})
    record["acceptance"].update({"criteria": ["200 or fewer cases completed with buyer-defined validation"]})
    return record


class AgentDemandTests(unittest.TestCase):
    def assert_invalid(self, record, needle):
        errors = MOD.validate_record(record, allow_draft=True)
        self.assertTrue(any(needle in error for error in errors), errors)

    def test_safe_starter_is_valid_draft(self):
        self.assertEqual(MOD.validate_record(starter(), allow_draft=True), [])

    def test_draft_requires_flag(self):
        errors = MOD.validate_record(starter(), allow_draft=False)
        self.assertTrue(any("--allow-draft" in error for error in errors), errors)

    def test_verified_demand_requires_authority(self):
        record = commercial()
        record["authority"]["authority_state"] = "none"
        self.assert_invalid(record, "verified_commercial demand requires current buyer authority")

    def test_synthetic_demand_cannot_auto_award(self):
        record = starter()
        record["bidding"].update({"automatic_award_allowed": True, "max_autonomous_award_minor": 100})
        self.assert_invalid(record, "exploratory/synthetic demand cannot enable automatic award")

    def test_auto_award_cannot_exceed_authority(self):
        record = commercial()
        record["bidding"].update({"automatic_award_allowed": True, "max_autonomous_award_minor": 70000})
        self.assert_invalid(record, "exceeds buyer authority")

    def test_auto_award_requires_acceptance(self):
        record = commercial()
        record["bidding"].update({"automatic_award_allowed": True, "max_autonomous_award_minor": 50000})
        record["acceptance"]["criteria"] = []
        self.assert_invalid(record, "automatic award requires acceptance criteria")

    def test_undisclosed_budget_cannot_publish_amounts(self):
        record = starter()
        record["budget"]["public_max_minor"] = 1000
        self.assert_invalid(record, "undisclosed budget")

    def test_bid_window_must_be_ordered(self):
        record = commercial()
        record["timing"]["bid_closes_at"] = "2026-08-29T11:00:00Z"
        self.assert_invalid(record, "after bid_opens_at")

    def test_confidential_request_cannot_be_public(self):
        record = commercial()
        record["disclosure"]["tier"] = "confidential"
        self.assert_invalid(record, "public bidding requires disclosure.tier=public")

    def test_private_customer_data_rejected(self):
        record = starter()
        record["disclosure"]["contains_private_customer_data"] = True
        self.assert_invalid(record, "contains_private_customer_data must be false")

    def test_awarded_state_requires_selection_evidence(self):
        record = commercial()
        record["status"] = "awarded"
        self.assert_invalid(record, "requires award.seller_listing_ref")

    def test_award_after_authority_expiry_rejected(self):
        record = commercial()
        record["status"] = "awarded"
        record["award"].update({
            "seller_listing_ref": "listing:seller-1", "seller_listing_version": "1.2.0",
            "proposal_ref": "proposal:1", "awarded_price_minor": 40000, "awarded_currency": "USD",
            "awarded_at": "2026-09-11T00:00:00Z",
        })
        self.assert_invalid(record, "award occurred after authority expired")

    def test_payment_is_not_acceptance(self):
        record = commercial()
        record["status"] = "paid"
        record["award"].update({
            "seller_listing_ref": "listing:seller-1", "seller_listing_version": "1.2.0",
            "proposal_ref": "proposal:1", "awarded_price_minor": 40000, "awarded_currency": "USD",
            "awarded_at": "2026-08-30T13:00:00Z",
        })
        record["acceptance"]["acceptance_state"] = "accepted"
        self.assert_invalid(record, "paid state cannot itself be treated as accepted")

    def test_accepted_state_requires_acceptance_evidence(self):
        record = commercial()
        record["status"] = "accepted"
        record["award"].update({
            "seller_listing_ref": "listing:seller-1", "seller_listing_version": "1.2.0",
            "proposal_ref": "proposal:1", "awarded_price_minor": 40000, "awarded_currency": "USD",
            "awarded_at": "2026-08-30T13:00:00Z",
        })
        self.assert_invalid(record, "accepted status requires acceptance_state=accepted")


if __name__ == "__main__":
    unittest.main()
