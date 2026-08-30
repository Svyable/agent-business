import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("bounty", ROOT / "scripts" / "validate_interoperability_bounty.py")
bounty = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(bounty)


def starter():
    return json.loads((ROOT / "templates" / "INTEROPERABILITY_BOUNTY.json").read_text())


def accepted_record():
    record = starter()
    criteria_hash = "sha256:criteria-v1"
    record["status"] = "accepted"
    record["target"].update({
        "population_hash": "sha256:population-v1",
        "selection_rule_hash": "sha256:selection-v1",
        "acceptance_criteria_hash": criteria_hash,
        "minimum_incremental_reachable_corridors": 2,
    })
    record["demand"] = {
        "evidence_class": "observed_commercial_demand",
        "snapshot_ref": "liquidity:snapshot:before",
        "corridor_count": 3,
        "qualified_value_minor_range": [10000, 20000],
        "currency": "USD",
        "evidence_refs": ["ev-demand"],
        "demand_backed_claim": True,
    }
    record["funding"] = {
        "repo_custodies_funds": False,
        "currency": "USD",
        "payout_cap_minor": 1000,
        "custody_state": "external_verified",
        "custody_provider_ref": "external-custodian-ref",
        "custody_evidence_ref": "ev-custody",
        "sponsors": [{
            "sponsor_ref": "sponsor-a",
            "commitment_minor": 1000,
            "currency": "USD",
            "state": "verified",
            "expires_at": "2026-12-31T00:00:00Z",
            "verification_evidence_ref": "ev-funding",
        }],
    }
    record["builder"] = {
        "state": "submitted",
        "builder_ref": "builder-a",
        "proposal_ref": "proposal-a",
        "implementation_cost_minor_range": [500, 800],
        "currency": "USD",
        "compatibility_profile_target_ref": "compatibility-profile:v1",
        "submission_evidence_refs": ["ev-submission"],
    }
    record["award"] = {
        "state": "awarded",
        "builder_ref": "builder-a",
        "acceptance_criteria_hash": criteria_hash,
        "awarded_at": "2026-08-30T18:00:00Z",
    }
    record["acceptance"] = {
        "state": "passed",
        "criteria_hash": criteria_hash,
        "criteria_locked_at": "2026-08-30T17:59:00Z",
        "test_evidence_refs": ["ev-tests"],
        "evaluated_at": "2026-08-30T18:10:00Z",
    }
    record["unlock_verification"] = {
        "state": "verified",
        "baseline_snapshot_ref": "liquidity:snapshot:before",
        "post_snapshot_ref": "liquidity:snapshot:after",
        "same_population_confirmed": True,
        "same_selection_rule_confirmed": True,
        "incremental_reachable_corridors": 2,
        "evidence_ref": "ev-unlock",
        "verified_at": "2026-08-30T18:11:00Z",
    }
    record["payout"] = {
        "state": "earned",
        "amount_minor": 1000,
        "currency": "USD",
        "payout_authority_ref": None,
        "payment_ref": None,
        "settlement_evidence_ref": None,
    }
    record["acceptance"]["criteria_hash"] = criteria_hash
    record["value_attribution"] = {
        "overlap_group_id": None,
        "overlap_policy": "independent_no_value_claim",
        "overlap_check_evidence_ref": None,
        "claims_exclusive_incremental_value": False,
    }
    record["conflicts"] = {
        "builder_related_to_sponsors": False,
        "disclosure": "No known related-party relationship between builder and sponsor.",
    }
    return record


class InteroperabilityBountyTests(unittest.TestCase):
    def test_schema_parses(self):
        json.loads((ROOT / "schemas" / "interoperability-bounty.schema.json").read_text())

    def test_starter_passes_only_with_draft_flag(self):
        record = starter()
        self.assertEqual(bounty.validate(record, allow_draft=True), [])
        self.assertTrue(any("--allow-draft" in error for error in bounty.validate(record)))

    def test_valid_accepted_record(self):
        self.assertEqual(bounty.validate(accepted_record()), [])

    def test_synthetic_demand_cannot_carry_commercial_value(self):
        record = accepted_record()
        record["demand"]["evidence_class"] = "synthetic_test"
        errors = bounty.validate(record)
        self.assertTrue(any("commercial demand" in error for error in errors))

    def test_self_declared_demand_cannot_claim_demand_backing(self):
        record = accepted_record()
        record["demand"]["evidence_class"] = "self_declared_intent"
        record["demand"]["qualified_value_minor_range"] = None
        record["demand"]["currency"] = None
        errors = bounty.validate(record)
        self.assertTrue(any("demand_backed_claim" in error for error in errors))

    def test_verified_commitment_requires_evidence(self):
        record = accepted_record()
        record["funding"]["sponsors"][0]["verification_evidence_ref"] = None
        errors = bounty.validate(record)
        self.assertTrue(any("verified funding requires" in error for error in errors))

    def test_pledge_is_not_verified_funding_for_award(self):
        record = accepted_record()
        record["funding"]["sponsors"][0]["state"] = "pledged"
        record["funding"]["sponsors"][0]["verification_evidence_ref"] = None
        errors = bounty.validate(record)
        self.assertTrue(any("verified sponsor commitments" in error for error in errors))

    def test_repository_can_never_claim_custody(self):
        record = accepted_record()
        record["funding"]["repo_custodies_funds"] = True
        errors = bounty.validate(record)
        self.assertTrue(any("repo_custodies_funds must be false" in error for error in errors))

    def test_external_verified_custody_needs_evidence(self):
        record = accepted_record()
        record["funding"]["custody_evidence_ref"] = None
        errors = bounty.validate(record)
        self.assertTrue(any("external_verified custody" in error for error in errors))

    def test_award_cannot_mutate_acceptance_criteria(self):
        record = accepted_record()
        record["award"]["acceptance_criteria_hash"] = "sha256:changed-after-award"
        errors = bounty.validate(record)
        self.assertTrue(any("frozen target hash" in error for error in errors))

    def test_builder_sponsor_self_dealing_must_be_disclosed(self):
        record = accepted_record()
        record["builder"]["builder_ref"] = "sponsor-a"
        record["award"]["builder_ref"] = "sponsor-a"
        errors = bounty.validate(record)
        self.assertTrue(any("must be disclosed as related" in error for error in errors))

    def test_acceptance_requires_verified_marginal_unlock(self):
        record = accepted_record()
        record["unlock_verification"]["state"] = "not_started"
        record["unlock_verification"]["baseline_snapshot_ref"] = None
        record["unlock_verification"]["post_snapshot_ref"] = None
        record["unlock_verification"]["evidence_ref"] = None
        record["unlock_verification"]["verified_at"] = None
        record["unlock_verification"]["same_population_confirmed"] = False
        record["unlock_verification"]["same_selection_rule_confirmed"] = False
        errors = bounty.validate(record)
        self.assertTrue(any("verified unlock" in error for error in errors))

    def test_unlock_must_meet_published_threshold(self):
        record = accepted_record()
        record["unlock_verification"]["incremental_reachable_corridors"] = 1
        errors = bounty.validate(record)
        self.assertTrue(any("minimum incremental" in error for error in errors))

    def test_same_population_and_selection_rule_are_required(self):
        record = accepted_record()
        record["unlock_verification"]["same_population_confirmed"] = False
        record["unlock_verification"]["same_selection_rule_confirmed"] = False
        errors = bounty.validate(record)
        self.assertTrue(any("same_population_confirmed" in error for error in errors))
        self.assertTrue(any("same_selection_rule_confirmed" in error for error in errors))

    def test_acceptance_never_executes_payment_or_grants_authority(self):
        record = accepted_record()
        record["authority"]["acceptance_executes_payment"] = True
        record["authority"]["acceptance_grants_authority"] = True
        errors = bounty.validate(record)
        self.assertTrue(any("acceptance_executes_payment must be false" in error for error in errors))
        self.assertTrue(any("acceptance_grants_authority must be false" in error for error in errors))

    def test_settled_payout_requires_external_authority_payment_and_settlement_evidence(self):
        record = accepted_record()
        record["status"] = "closed"
        record["payout"]["state"] = "settled"
        errors = bounty.validate(record)
        self.assertTrue(any("payout_authority_ref" in error for error in errors))
        self.assertTrue(any("payment_ref" in error for error in errors))
        self.assertTrue(any("settlement_evidence_ref" in error for error in errors))

    def test_closed_record_with_independent_settlement_evidence_is_valid(self):
        record = accepted_record()
        record["status"] = "closed"
        record["payout"].update({
            "state": "settled",
            "payout_authority_ref": "authority:payout:001",
            "payment_ref": "machine-payment:001",
            "settlement_evidence_ref": "settlement:001",
        })
        self.assertEqual(bounty.validate(record), [])

    def test_exclusive_value_claim_needs_disjoint_overlap_evidence(self):
        record = accepted_record()
        record["value_attribution"]["claims_exclusive_incremental_value"] = True
        errors = bounty.validate(record)
        self.assertTrue(any("disjoint_population" in error for error in errors))
        self.assertTrue(any("overlap group and evidence" in error for error in errors))

    def test_cancelled_bounty_cannot_claim_settled_payout(self):
        record = accepted_record()
        record["status"] = "cancelled"
        record["payout"].update({
            "state": "settled",
            "payout_authority_ref": "authority:payout:001",
            "payment_ref": "machine-payment:001",
            "settlement_evidence_ref": "settlement:001",
        })
        errors = bounty.validate(record)
        self.assertTrue(any("cancelled bounty cannot claim settled payout" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
