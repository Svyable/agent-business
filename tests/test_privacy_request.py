import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_privacy_request", ROOT / "scripts" / "validate_privacy_request.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(mod)


def starter():
    return json.loads((ROOT / "templates" / "PRIVACY_REQUEST_RECORD.json").read_text())


def current_evidence(eid, etype="verification"):
    return {"id": eid, "type": etype, "status": "current", "observed_at": "2026-08-28T18:00:00Z", "public_url": None}


def fulfilled_erasure():
    r = starter()
    r["status"] = "fulfilled"
    r["scope"]["identity_scope_verified"] = True
    r["authority"] = {"can_access_subject_data": True, "can_execute_privacy_action": True, "authority_evidence_ids": ["auth"]}
    r["evidence"] = [current_evidence("auth", "authority"), current_evidence("raw", "system_action"), current_evidence("derived", "verification"), current_evidence("backup", "verification"), current_evidence("final", "final_response")]
    r["systems"] = [
        {"id": "raw", "surface": "raw_conversation", "action": "delete", "status": "verified_not_present", "restore_protection": "not_applicable", "evidence_ids": ["raw"]},
        {"id": "derived", "surface": "derived_summary", "action": "redact", "status": "verified_not_present", "restore_protection": "not_applicable", "evidence_ids": ["derived"]},
        {"id": "backup", "surface": "backup_recovery", "action": "tombstone", "status": "verified_not_present", "restore_protection": "verified", "evidence_ids": ["backup"]}
    ]
    r["verification"] = {"state": "passed", "mapped_surface_count": 3, "verified_surface_count": 3, "retrieval_residue_count": 0, "derived_memory_tested": True, "restore_resurrection_tested": True, "known_unverifiable_surfaces": [], "evidence_ids": ["derived", "backup"]}
    r["response"] = {"finalized": True, "final_evidence_ids": ["final"], "export_tenant_isolated": False, "export_redaction_reviewed": False}
    return r


class PrivacyRequestTests(unittest.TestCase):
    def assert_invalid(self, record, text):
        with self.assertRaises(SystemExit) as ctx:
            mod.validate(record)
        self.assertIn(text, str(ctx.exception))

    def test_starter_is_safe(self):
        mod.validate(starter())

    def test_fulfilled_erasure_is_valid(self):
        mod.validate(fulfilled_erasure())

    def test_raw_only_delete_with_derived_residue_fails(self):
        r = fulfilled_erasure(); r["verification"]["retrieval_residue_count"] = 1
        self.assert_invalid(r, "zero retrieval residue")

    def test_api_execution_without_verification_fails(self):
        r = fulfilled_erasure(); r["systems"][0]["status"] = "executed"
        self.assert_invalid(r, "every mapped surface")

    def test_derived_memory_must_be_tested(self):
        r = fulfilled_erasure(); r["verification"]["derived_memory_tested"] = False
        self.assert_invalid(r, "derived-memory resurfacing")

    def test_restore_must_not_resurrect_erased_data(self):
        r = fulfilled_erasure(); r["verification"]["restore_resurrection_tested"] = False
        self.assert_invalid(r, "restore-resurrection")

    def test_unresolved_downstream_blocks_completion(self):
        r = fulfilled_erasure(); r["downstream"] = [{"processor_ref": "processor-x", "required": True, "status": "sent", "evidence_ids": []}]
        self.assert_invalid(r, "unresolved required downstream")

    def test_unresolved_hold_blocks_completion(self):
        r = fulfilled_erasure(); r["exceptions"] = [{"id": "hold", "type": "legal_hold", "resolved": False, "decision_ref": None, "evidence_ids": []}]
        self.assert_invalid(r, "unresolved exceptions")

    def test_execution_requires_authority(self):
        r = fulfilled_erasure(); r["authority"]["can_execute_privacy_action"] = False
        self.assert_invalid(r, "explicit data-access and privacy-action authority")

    def test_stale_authority_evidence_fails(self):
        r = fulfilled_erasure(); r["evidence"][0]["status"] = "stale"
        self.assert_invalid(r, "must reference current evidence")

    def test_deadline_requires_source(self):
        r = starter(); r["policy_basis"]["deadline_at"] = "2026-09-01T00:00:00Z"
        self.assert_invalid(r, "deadline_source_ref")

    def test_fabricated_statutory_days_field_fails(self):
        r = starter(); r["policy_basis"]["gdpr_days"] = 30
        self.assert_invalid(r, "is not allowed")

    def test_consent_withdrawal_requires_propagation_and_basis_review(self):
        r = starter(); r["request_type"] = "consent_withdrawal"; r["status"] = "escalated"; r["scope"]["identity_scope_verified"] = True
        self.assert_invalid(r, "propagation completion")

    def test_access_export_requires_tenant_isolation(self):
        r = fulfilled_erasure(); r["request_type"] = "access"; r["systems"] = []; r["verification"]["mapped_surface_count"] = 0; r["verification"]["verified_surface_count"] = 0
        self.assert_invalid(r, "tenant isolation")

    def test_known_unverifiable_surface_blocks_erasure_fulfilled(self):
        r = fulfilled_erasure(); r["verification"]["known_unverifiable_surfaces"] = ["legacy-index"]
        self.assert_invalid(r, "known unverifiable surfaces")

    def test_prohibited_raw_identifier_field_fails(self):
        r = starter(); r["raw_subject_identifier"] = "person@example.com"
        self.assert_invalid(r, "prohibited sensitive field")

    def test_system_action_result_requires_evidence(self):
        r = starter(); r["status"] = "mapped"; r["scope"]["identity_scope_verified"] = True; r["systems"] = [{"id":"v","surface":"vector_index","action":"delete","status":"executed","restore_protection":"planned","evidence_ids":[]}]; r["verification"]["mapped_surface_count"] = 1
        self.assert_invalid(r, "asserted action/result requires evidence")


if __name__ == "__main__":
    unittest.main()
