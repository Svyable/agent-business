import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validator", ROOT / "scripts/validate_agent_release.py")
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
BASE = json.loads((ROOT / "templates/AGENT_RELEASE_RECORD.json").read_text())


def ev(eid, typ="public_artifact", status="current"):
    return {"id": eid, "type": typ, "status": status, "observed_at": "2026-08-28T12:00:00Z"}


def stable_record():
    r = copy.deepcopy(BASE)
    r["status"] = "stable"
    r["revision_id"] = "rev-2"
    r["parent_revision_id"] = "rev-1"
    r["change"]["classifications"] = ["behavioral"]
    r["change"]["affected_components"]["models"] = ["provider:model-v2"]
    r["baseline"].update({"production_revision_id": "rev-1", "evidence_ids": ["baseline"]})
    r["dependencies"] = [{
        "id": "model", "kind": "model", "previous_version": "v1", "new_version": "v2",
        "compatibility_checked": True, "evidence_ids": ["dep"]
    }]
    for key in ("baseline_compared", "regression_suite_passed", "safety_policy_passed", "tool_use_checked", "latency_delta_checked", "cost_delta_checked", "human_review_delta_checked"):
        r["evaluation"][key] = True
    r["evaluation"]["evidence_ids"] = ["eval"]
    r["compatibility"].update({
        "machine_contracts_checked": True, "stored_state_checked": True, "integrations_checked": True,
        "downstream_consumers_checked": True, "evidence_ids": ["compat"]
    })
    r["rollback"].update({"defined": True, "tested": True, "owner_defined": True, "evidence_ids": ["rollback"]})
    r["rollout"].update({
        "canary_percent": 10, "current_percent": 100, "hold_period_minutes": 60,
        "promotion_criteria": ["quality >= baseline"], "stop_conditions": ["critical regression"],
        "rollback_revision_id": "rev-1", "production_metrics_evidence_ids": ["metrics"]
    })
    for key in ("error_rate", "quality_safety", "latency", "cost_per_success", "escalation_rate", "customer_incidents"):
        r["observability"][key] = True
    r["evidence"] = [
        ev("baseline", "production_baseline"), ev("dep", "dependency_provenance"), ev("eval", "eval_result"),
        ev("compat", "compatibility_test"), ev("rollback", "rollback_test"), ev("metrics", "production_metrics")
    ]
    return r


class TestAgentRelease(unittest.TestCase):
    def assertFails(self, record, text):
        with self.assertRaises(SystemExit) as cm:
            v.validate(record)
        self.assertIn(text, str(cm.exception))

    def test_safe_template(self):
        v.validate(copy.deepcopy(BASE))

    def test_stable_record(self):
        v.validate(stable_record())

    def test_model_change_requires_behavioral_classification(self):
        r = stable_record()
        r["change"]["classifications"] = ["patch"]
        self.assertFails(r, "must be classified behavioral")

    def test_dependency_change_requires_behavioral_classification(self):
        r = stable_record()
        r["change"]["affected_components"]["models"] = []
        r["change"]["classifications"] = ["patch"]
        self.assertFails(r, "dependency version changes")

    def test_advanced_release_requires_baseline(self):
        r = stable_record()
        r["baseline"]["production_revision_id"] = None
        self.assertFails(r, "production baseline revision")

    def test_stale_eval_evidence_fails(self):
        r = stable_record()
        next(x for x in r["evidence"] if x["id"] == "eval")["status"] = "stale"
        self.assertFails(r, "only current evidence")

    def test_critical_regression_fails(self):
        r = stable_record()
        r["evaluation"]["critical_regressions"] = ["unsafe tool action"]
        self.assertFails(r, "critical regressions")

    def test_canary_bypass_fails(self):
        r = stable_record()
        r["status"] = "canary"
        r["rollout"]["current_percent"] = 25
        self.assertFails(r, "cannot exceed configured canary percentage")

    def test_production_metrics_required(self):
        r = stable_record()
        r["rollout"]["production_metrics_evidence_ids"] = []
        self.assertFails(r, "production_metrics_evidence_ids")

    def test_authority_widening_requires_reapproval(self):
        r = stable_record()
        r["authority"]["widened"] = True
        r["change"]["classifications"].append("authority")
        self.assertFails(r, "explicit reapproval")

    def test_irreversible_migration_cannot_claim_reversible(self):
        r = stable_record()
        r["rollback"]["irreversible_changes"] = ["state rewrite"]
        self.assertFails(r, "cannot be marked state-migration reversible")

    def test_breaking_change_requires_migration_path(self):
        r = stable_record()
        r["change"]["classifications"].append("breaking")
        r["compatibility"]["breaking_change"] = True
        self.assertFails(r, "migration path")

    def test_material_customer_impact_requires_communication(self):
        r = stable_record()
        r["change"]["classifications"].append("commercial")
        r["customer_impact"].update({"material": True, "dimensions": ["pricing"], "communication_required": False})
        self.assertFails(r, "requires customer communication")

    def test_customer_communication_must_be_complete_before_exposure(self):
        r = stable_record()
        r["customer_impact"].update({"material": True, "dimensions": ["behavior"], "communication_required": True, "communication_complete": False})
        self.assertFails(r, "requires completed communication")

    def test_rollback_must_be_tested(self):
        r = stable_record()
        r["rollback"]["tested"] = False
        self.assertFails(r, "defined, tested rollback")

    def test_stable_requires_full_traffic(self):
        r = stable_record()
        r["rollout"]["current_percent"] = 80
        self.assertFails(r, "100 percent production traffic")

    def test_retirement_requires_complete_migration(self):
        r = stable_record()
        r["status"] = "retired"
        r["deprecation"].update({
            "notice_required": True, "notice_complete": True, "support_window_defined": True,
            "migration_path_defined": True, "sunset_criteria_defined": True, "migration_complete": False,
            "evidence_ids": ["notice"]
        })
        r["evidence"].append(ev("notice", "migration_evidence"))
        self.assertFails(r, "migration_complete")

    def test_credentials_fail(self):
        r = copy.deepcopy(BASE)
        r["dependencies"] = [{"id": "x", "kind": "tool", "previous_version": None, "new_version": "v1", "compatibility_checked": False, "evidence_ids": [], "api_key": "nope"}]
        self.assertFails(r, "prohibited sensitive field")


if __name__ == "__main__":
    unittest.main()
