import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validator", ROOT / "scripts/validate_customer_implementation.py")
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
BASE = json.loads((ROOT / "templates/CUSTOMER_IMPLEMENTATION_RECORD.json").read_text())


def ev(eid, typ="public_artifact", status="current"):
    return {"id": eid, "type": typ, "status": status, "observed_at": "2026-08-28T12:00:00Z"}


def live_record():
    r = copy.deepcopy(BASE)
    r["status"] = "live"
    r["evidence"] = [ev("sale", "commercial_record"), ev("eval", "eval_result"), ev("prod", "environment_promotion"), ev("accept", "buyer_acceptance"), ev("auth", "authority_grant")]
    r["commercial_handoff"]["handoff_evidence_ids"] = ["sale"]
    r["environments"][1].update({"promotion_state": "approved", "evidence_ids": ["prod"]})
    r["data_readiness"].update({"source_authority_resolved": True, "minimum_necessary_defined": True, "retention_defined": True, "residency_resolved": True, "customer_data_training_use": "prohibited", "deletion_path_defined": True, "test_data_policy_defined": True})
    for k in ("representative_set", "regression_suite", "safety_policy_cases", "human_review_defined", "acceptance_thresholds_defined", "known_limitations_documented", "production_monitoring_aligned", "production_grade_passed"):
        r["evals"][k] = True
    r["evals"]["evidence_ids"] = ["eval"]
    r["rollout"].update({"strategy": "canary", "exposure_cap_percent": 10, "rollback_defined": True, "kill_switch_defined": True, "rollback_triggers": ["critical incident"]})
    r["adoption"].update({"training_complete": True, "communications_complete": True, "sop_updates_complete": True, "human_escalation_defined": True, "adoption_metrics_defined": True})
    r["go_live"].update({"requested": True, "approved": True, "customer_acceptance_evidence_ids": ["accept"], "production_authority_evidence_ids": ["auth"], "security_privacy_ready": True, "reliability_ready": True, "observability_ready": True, "support_owner_defined": True})
    return r


class TestImplementation(unittest.TestCase):
    def test_safe_template(self):
        v.validate(copy.deepcopy(BASE))

    def test_live_record(self):
        v.validate(live_record())

    def assertFails(self, r, text):
        with self.assertRaises(SystemExit) as cm:
            v.validate(r)
        self.assertIn(text, str(cm.exception))

    def test_scope_handoff_required_after_planning(self):
        r = copy.deepcopy(BASE)
        r["status"] = "configuring"
        self.assertFails(r, "handoff_evidence_ids")

    def test_credentials_fail(self):
        r = copy.deepcopy(BASE)
        r["integrations"] = [{"id": "x", "status": "planned", "rate_limits_defined": False, "failure_behavior_defined": False, "evidence_ids": [], "api_key": "nope"}]
        self.assertFails(r, "prohibited sensitive field")

    def test_sandbox_evidence_cannot_go_live(self):
        r = live_record()
        r["environments"][1]["promotion_state"] = "configured"
        self.assertFails(r, "approved production promotion")

    def test_unknown_customer_data_use_fails(self):
        r = live_record()
        r["data_readiness"]["customer_data_training_use"] = "unknown"
        self.assertFails(r, "unknown customer-data")

    def test_missing_rollback_fails(self):
        r = live_record()
        r["rollout"]["kill_switch_defined"] = False
        self.assertFails(r, "rollback, kill switch")

    def test_stale_customer_acceptance_fails(self):
        r = live_record()
        next(x for x in r["evidence"] if x["id"] == "accept")["status"] = "stale"
        self.assertFails(r, "only current evidence")

    def test_critical_blocker_fails(self):
        r = live_record()
        r["go_live"]["critical_blockers"] = ["privacy approval missing"]
        self.assertFails(r, "critical blockers")

    def test_unvalidated_integration_fails(self):
        r = copy.deepcopy(BASE)
        r["integrations"] = [{"id": "crm", "status": "validated", "rate_limits_defined": False, "failure_behavior_defined": True, "evidence_ids": []}]
        self.assertFails(r, "rate limits and failure behavior")

    def test_premature_handoff_fails(self):
        r = live_record()
        r["status"] = "handed_to_customer_success"
        self.assertFails(r, "customer-success handoff")

    def test_hypercare_must_be_active(self):
        r = live_record()
        r["status"] = "hypercare"
        self.assertFails(r, "hypercare.active")


if __name__ == "__main__":
    unittest.main()
