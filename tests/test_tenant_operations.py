import copy
import json
import unittest
from pathlib import Path

from scripts.validate_tenant_operations import validate

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "TENANT_OPERATIONS_RECORD.json"


class TenantOperationsTests(unittest.TestCase):
    def starter(self):
        return json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def operational(self):
        r = self.starter()
        r["status"] = "operational"
        r["deployment"].update({"region": "us-central", "residency_status": "verified", "service_tier": "standard"})
        r["context_propagation"] = {
            "identity_source": "authenticated_claim",
            "prompt_text_authoritative": False,
            "layers": ["edge","orchestrator","model_session","retrieval","memory","cache","tools","queues","billing","observability","release_config"]
        }
        r["evidence"] = [{"id":"ev-current","type":"isolation_test","status":"current","observed_at":"2026-08-28T13:00:00Z"}]
        r["boundaries"] = [
            {"layer": layer, "isolation_method": "tenant scoped policy", "authorization_checked": True, "tenant_scoped": True, "evidence_ids": ["ev-current"]}
            for layer in ["runtime","retrieval","memory","cache","tools","data_store"]
        ]
        r["quotas"] = [
            {"layer":"edge","metric":"requests","limit":100,"window":"minute","enforced":True,"evidence_ids":["ev-current"]},
            {"layer":"inference","metric":"tokens","limit":10000,"window":"minute","enforced":True,"evidence_ids":["ev-current"]}
        ]
        r["entitlements"].update({"policy_version":"policy-1","release_config_scoped":True})
        r["cost_attribution"].update({"inference":True,"shared_overhead_method":"proportional direct cost"})
        r["observability"] = {"tenant_scoped":True,"metrics":["latency","errors","throttles","cost_per_success"],"missing_context_alert":True}
        tests = ["missing_context","cross_tenant_retrieval","memory_collision","cache_leakage","unauthorized_tool_routing","downstream_quota_bypass","noisy_neighbor","billing_attribution","release_leakage"]
        r["isolation_tests"] = [{"test":name,"status":"pass","observed_at":"2026-08-28T13:00:00Z","evidence_ids":["ev-current"]} for name in tests]
        r["authority"].update({"can_activate":True,"authority_evidence_ids":["ev-current"]})
        return r

    def assert_invalid(self, record, text):
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn(text, str(ctx.exception))

    def test_safe_starter_is_valid(self):
        validate(self.starter())

    def test_complete_operational_record_is_valid(self):
        validate(self.operational())

    def test_prompt_text_cannot_be_tenant_identity(self):
        r = self.starter()
        r["context_propagation"]["prompt_text_authoritative"] = True
        self.assert_invalid(r, "prompt text")

    def test_operational_requires_all_context_layers(self):
        r = self.operational()
        r["context_propagation"]["layers"].remove("billing")
        self.assert_invalid(r, "missing tenant context layers")

    def test_boundary_must_be_authorization_checked(self):
        r = self.operational()
        r["boundaries"][1]["authorization_checked"] = False
        self.assert_invalid(r, "not tenant-scoped")

    def test_boundary_needs_current_evidence(self):
        r = self.operational()
        r["evidence"][0]["status"] = "stale"
        self.assert_invalid(r, "must reference current evidence")

    def test_edge_only_quota_is_rejected(self):
        r = self.operational()
        r["quotas"] = [r["quotas"][0]]
        self.assert_invalid(r, "edge-only quotas")

    def test_release_config_must_be_tenant_scoped(self):
        r = self.operational()
        r["entitlements"]["release_config_scoped"] = False
        self.assert_invalid(r, "release/config")

    def test_operational_requires_tenant_observability(self):
        r = self.operational()
        r["observability"]["tenant_scoped"] = False
        self.assert_invalid(r, "tenant-scoped observability")

    def test_noisy_neighbor_test_is_required(self):
        r = self.operational()
        r["isolation_tests"] = [x for x in r["isolation_tests"] if x["test"] != "noisy_neighbor"]
        self.assert_invalid(r, "missing isolation tests")

    def test_failed_isolation_test_blocks_operational(self):
        r = self.operational()
        r["isolation_tests"][0]["status"] = "fail"
        self.assert_invalid(r, "must pass")

    def test_material_authority_requires_evidence(self):
        r = self.starter()
        r["authority"]["can_change_quotas"] = True
        self.assert_invalid(r, "material tenant authority")

    def test_sensitive_portable_field_is_rejected(self):
        r = self.starter()
        r["customer_name"] = "private tenant"
        self.assert_invalid(r, "prohibited sensitive field")

    def test_offboarded_requires_complete_cleanup(self):
        r = self.operational()
        r["status"] = "offboarded"
        self.assert_invalid(r, "incomplete controls")

    def test_offboarded_requires_cleanup_test(self):
        r = self.operational()
        r["status"] = "offboarded"
        for key in ("admission_disabled","credentials_revoked","jobs_disabled","data_disposition_complete","memory_cleanup_complete","billing_closed","audit_retention_resolved"):
            r["offboarding"][key] = True
        r["offboarding"]["evidence_ids"] = ["ev-current"]
        self.assert_invalid(r, "offboarding_cleanup")

    def test_offboarded_with_cleanup_evidence_is_valid(self):
        r = self.operational()
        r["status"] = "offboarded"
        for key in ("admission_disabled","credentials_revoked","jobs_disabled","data_disposition_complete","memory_cleanup_complete","billing_closed","audit_retention_resolved"):
            r["offboarding"][key] = True
        r["offboarding"]["evidence_ids"] = ["ev-current"]
        r["isolation_tests"].append({"test":"offboarding_cleanup","status":"pass","observed_at":"2026-08-28T13:00:00Z","evidence_ids":["ev-current"]})
        validate(r)


if __name__ == "__main__":
    unittest.main()
