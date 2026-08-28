import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_ai_transparency", ROOT / "scripts" / "validate_ai_transparency.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)
STARTER = json.loads((ROOT / "templates" / "AI_TRANSPARENCY_RECORD.json").read_text())


def evidence(eid, etype="ruleset", status="current"):
    return {"id": eid, "type": etype, "status": status, "observed_at": "2026-08-28T20:00:00Z", "reference": f"https://example.com/{eid}"}


def active_record():
    r = copy.deepcopy(STARTER)
    r["status"] = "active"
    r["role"] = {"classification": "deployer", "evidence_ids": ["role"]}
    r["decision"] = {"result": "required", "rationale": "Current ruleset requires disclosure for this scoped direct interaction.", "evidence_ids": ["rule"]}
    r["rulesets"] = [{"id": "eu-example", "jurisdiction": "EU", "reference": "https://example.com/rule", "retrieved_at": "2026-08-28T19:00:00Z", "review_due_at": "2026-09-28T19:00:00Z", "status": "current"}]
    r["disclosure"] = {"configured": True, "surface": "chat header", "timing": "before_first_material_interaction", "accessible": True, "customer_can_disable": False, "render_test_evidence_ids": ["render"]}
    r["change_control"] = {"material_change_detected": False, "re_review_required": False}
    r["authority"] = {"can_activate_transparency_configuration": True, "can_publish": False, "evidence_ids": ["authority"]}
    r["evidence"] = [evidence("role", "role_classification"), evidence("rule"), evidence("render", "render_test"), evidence("authority", "authority")]
    return r


class TransparencyValidationTests(unittest.TestCase):
    def assertFails(self, record, text):
        with self.assertRaises(SystemExit) as cm:
            MOD.validate(record)
        self.assertIn(text, str(cm.exception))

    def test_starter_is_safe(self):
        MOD.validate(copy.deepcopy(STARTER))

    def test_active_happy_path(self):
        MOD.validate(active_record())

    def test_active_requires_resolved_role(self):
        r = active_record(); r["role"] = {"classification": "unknown", "evidence_ids": []}
        self.assertFails(r, "resolved provider/deployer role")

    def test_required_disclosure_cannot_be_late(self):
        r = active_record(); r["disclosure"]["timing"] = "after_material_interaction"
        self.assertFails(r, "before or at first material interaction")

    def test_required_disclosure_must_be_accessible(self):
        r = active_record(); r["disclosure"]["accessible"] = False
        self.assertFails(r, "accessible path")

    def test_customer_cannot_disable_required_disclosure(self):
        r = active_record(); r["disclosure"]["customer_can_disable"] = True
        self.assertFails(r, "cannot disable required disclosure")

    def test_render_evidence_must_be_current(self):
        r = active_record(); next(x for x in r["evidence"] if x["id"] == "render")["status"] = "stale"
        self.assertFails(r, "render testing requires current evidence")

    def test_stale_ruleset_fails(self):
        r = active_record(); r["rulesets"][0]["review_due_at"] = "2026-08-28T20:30:00Z"; r["updated_at"] = "2026-08-28T20:55:00Z"
        self.assertFails(r, "current ruleset is stale")

    def test_required_provenance_needs_export_survival_test(self):
        r = active_record(); r["provenance"] = {"required": True, "method": "machine-readable-mark", "configured": True, "export_survival_tested": False, "evidence_ids": ["prov"]}; r["evidence"].append(evidence("prov", "provenance_test"))
        self.assertFails(r, "export paths")

    def test_human_review_exception_requires_evidence(self):
        r = active_record(); r["content"]["public_interest_text"] = True; r["decision"]["result"] = "not_required"; r["human_review"] = {"required": True, "basis_for_exception": True, "review_evidence_ids": []}
        self.assertFails(r, "human review requires evidence")

    def test_material_change_invalidates_active(self):
        r = active_record(); r["change_control"] = {"material_change_detected": True, "re_review_required": True}
        self.assertFails(r, "active status is invalid after material change")

    def test_active_requires_activation_authority(self):
        r = active_record(); r["authority"] = {"can_activate_transparency_configuration": False, "can_publish": False, "evidence_ids": []}
        self.assertFails(r, "activation authority")

    def test_secret_like_field_rejected(self):
        r = copy.deepcopy(STARTER); r["api_key"] = "redacted"
        self.assertFails(r, "prohibited sensitive field")

    def test_retired_cannot_keep_authority(self):
        r = copy.deepcopy(STARTER); r["status"] = "retired"; r["authority"]["can_publish"] = True
        self.assertFails(r, "retired records cannot retain operational authority")


if __name__ == "__main__":
    unittest.main()
