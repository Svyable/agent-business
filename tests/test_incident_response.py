import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_incident_response", ROOT / "scripts" / "validate_incident_response.py")
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(validator)


def starter():
    return json.loads((ROOT / "templates" / "INCIDENT_RESPONSE_RECORD.json").read_text(encoding="utf-8"))


def operational(status="monitoring"):
    record = starter()
    record["status"] = status
    record["severity"] = "SEV2"
    record["updated_at"] = "2026-08-28T18:00:00Z"
    record["evidence"] = [
        {"id":"sev","type":"alert","observed_at":"2026-08-28T17:11:00Z","status":"current","reference":"internal://alert/1"},
        {"id":"auth","type":"authorization_event","observed_at":"2026-08-28T17:12:00Z","status":"current","reference":"internal://authority/1"},
        {"id":"contain","type":"audit_event","observed_at":"2026-08-28T17:13:00Z","status":"current","reference":"internal://contain/1"},
        {"id":"recover","type":"recovery_test","observed_at":"2026-08-28T17:50:00Z","status":"current","reference":"internal://recovery/1"},
        {"id":"customer","type":"customer_impact","observed_at":"2026-08-28T17:20:00Z","status":"current","reference":"internal://customer/1"}
    ]
    record["impact"]["severity_evidence_ids"] = ["sev"]
    record["timeline"].append({"at":"2026-08-28T17:13:00Z","event":"Intake paused","classification":"action","evidence_ids":["contain"]})
    record["authority"]["can_pause_intake"] = True
    record["authority"]["evidence_ids"] = ["auth"]
    record["containment"] = {"actions":[{"type":"pause_intake","executed":True,"authority_required":True,"evidence_ids":["contain"]}],"contained_at":"2026-08-28T17:13:00Z"}
    record["customer_impact"] = {"assessed":True,"affected_count":0,"notification_decision":"not_required","owner":"incident-commander","evidence_ids":["customer"],"communication_evidence_ids":[]}
    record["recovery"] = {
        "trigger_removed": True,
        "identity_authority_healthy": True,
        "security_policy_healthy": True,
        "data_integrity_healthy": True,
        "side_effects_reconciled": True,
        "observability_healthy": True,
        "production_authority_valid": True,
        "verification_evidence_ids": ["recover"],
        "verified_at": "2026-08-28T17:50:00Z"
    }
    return record


class IncidentResponseTests(unittest.TestCase):
    def assert_invalid(self, record, message=None):
        with self.assertRaises(SystemExit) as caught:
            validator.validate(record)
        if message:
            self.assertIn(message, str(caught.exception))

    def test_safe_starter_is_valid(self):
        validator.validate(starter())

    def test_monitoring_fixture_is_valid(self):
        validator.validate(operational())

    def test_rejects_sensitive_field(self):
        record = starter()
        record["credential"] = "do-not-store"
        self.assert_invalid(record, "prohibited sensitive field")

    def test_advanced_status_requires_classified_severity(self):
        record = operational("triaged")
        record["severity"] = "unclassified"
        self.assert_invalid(record, "classified severity")

    def test_advanced_status_requires_current_severity_evidence(self):
        record = operational("triaged")
        record["evidence"][0]["status"] = "superseded"
        self.assert_invalid(record, "current evidence")

    def test_executed_containment_requires_authority(self):
        record = operational()
        record["authority"]["can_pause_intake"] = False
        self.assert_invalid(record, "lacks declared authority")

    def test_material_authority_requires_current_evidence(self):
        record = operational()
        record["authority"]["evidence_ids"] = []
        self.assert_invalid(record, "material incident authority")

    def test_fact_requires_evidence(self):
        record = operational()
        record["investigation"]["facts"] = [{"statement":"Provider returned malformed data","evidence_ids":[]}]
        self.assert_invalid(record, "observed facts require current evidence")

    def test_confirmed_root_cause_requires_evidence(self):
        record = operational()
        record["investigation"]["root_cause_status"] = "confirmed"
        record["investigation"]["root_cause"] = "Bad release"
        self.assert_invalid(record, "confirmed root cause")

    def test_unresolved_material_side_effect_blocks_monitoring(self):
        record = operational()
        record["side_effects"] = [{"operation_id":"payment-1","kind":"payment","state":"uncertain","material":True,"amount_minor":1000,"evidence_ids":[]}]
        self.assert_invalid(record, "unresolved material side effects")

    def test_recovery_requires_all_gates(self):
        record = operational()
        record["recovery"]["observability_healthy"] = False
        self.assert_invalid(record, "failed recovery gates")

    def test_closed_incident_requires_customer_assessment(self):
        record = operational("closed")
        record["customer_impact"]["assessed"] = False
        self.assert_invalid(record, "customer-impact assessment")

    def test_required_customer_notification_needs_evidence_at_closure(self):
        record = operational("closed")
        record["customer_impact"]["notification_decision"] = "required"
        self.assert_invalid(record, "communication evidence")

    def test_closed_incident_rejects_pending_notification_review(self):
        record = operational("closed")
        record["customer_impact"]["notification_decision"] = "pending_policy_or_legal_review"
        self.assert_invalid(record, "resolved customer notification")

    def test_verified_corrective_action_requires_verification(self):
        record = operational()
        record["corrective_actions"] = [{"id":"ca-1","class":"detect","owner":"sre","due_at":"2026-09-01T00:00:00Z","status":"verified","verification_evidence_ids":[],"waiver_reason":None}]
        self.assert_invalid(record, "verified corrective actions")

    def test_closed_incident_requires_corrective_actions_resolved(self):
        record = operational("closed")
        record["corrective_actions"] = [{"id":"ca-1","class":"prevent","owner":"security","due_at":"2026-09-01T00:00:00Z","status":"open","verification_evidence_ids":[],"waiver_reason":None}]
        self.assert_invalid(record, "unresolved corrective actions")

    def test_timeline_must_be_chronological(self):
        record = operational()
        record["timeline"].append({"at":"2026-08-28T17:12:00Z","event":"Out of order","classification":"observed","evidence_ids":[]})
        self.assert_invalid(record, "timeline must be chronological")


if __name__ == "__main__":
    unittest.main()
