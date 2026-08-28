import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_platform_access", ROOT / "scripts/validate_platform_access.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


def starter():
    return json.loads((ROOT / "templates/PLATFORM_ACCESS_RECORD.json").read_text(encoding="utf-8"))


def active_record():
    record = starter()
    record["status"] = "active"
    record["updated_at"] = "2026-08-28T19:55:00Z"
    record["principal_delegation"] = {"basis":"customer OAuth delegation","evidence_ids":["principal"],"status":"current"}
    record["platform_authorization"] = {"basis":"official API and OAuth grant","evidence_ids":["api","oauth"],"status":"current"}
    record["access_method"]["tested"] = True
    record["terms_policy"] = {
        "reference":"https://example.invalid/platform-policy",
        "retrieved_at":"2026-08-28T18:00:00Z",
        "review_due_at":"2026-09-28T18:00:00Z",
        "automation_reviewed":True,
        "robots_signal":"not_applicable"
    }
    record["identity"] = {"mode":"registered_app","automation_disclosed":True,"spoofs_human_identity":False}
    record["credentials"]["reference"] = "private-secret-store:platform/example"
    record["actions"]["read_search"] = "allowed"
    record["signals"] = {"explicit_objection":False,"blocked":False,"challenge_present":False,"authorization_uncertain":False,"policy_changed":False}
    record["authority"] = {"can_activate":True,"can_resume":True,"can_write":False,"can_transact":False,"can_delete":False,"evidence_ids":["authority"]}
    record["evidence"] = [
        {"id":"principal","type":"principal_delegation","status":"current","observed_at":"2026-08-28T18:05:00Z","reference":"private:customer-delegation"},
        {"id":"api","type":"api_docs","status":"current","observed_at":"2026-08-28T18:10:00Z","reference":"https://example.invalid/api-policy"},
        {"id":"oauth","type":"oauth_grant","status":"current","observed_at":"2026-08-28T18:15:00Z","reference":"private:oauth-grant"},
        {"id":"authority","type":"authority","status":"current","observed_at":"2026-08-28T18:20:00Z","reference":"private:activation-approval"},
        {"id":"test","type":"test_result","status":"current","observed_at":"2026-08-28T18:30:00Z","reference":"private:integration-test"}
    ]
    return record


class PlatformAccessTests(unittest.TestCase):
    def assert_fails(self, record, contains):
        with self.assertRaises(SystemExit) as ctx:
            MOD.validate(record)
        self.assertIn(contains, str(ctx.exception))

    def test_safe_starter_validates(self):
        MOD.validate(starter())

    def test_active_example_validates(self):
        MOD.validate(active_record())

    def test_user_delegation_does_not_substitute_for_platform_permission(self):
        record = active_record()
        record["platform_authorization"] = {"basis":"user asked us to do it","evidence_ids":[],"status":"unknown"}
        self.assert_fails(record, "current platform authorization independent")

    def test_public_or_robot_signal_does_not_substitute_for_permission(self):
        record = active_record()
        record["access_method"]["type"] = "scraping_or_crawling"
        record["terms_policy"]["robots_signal"] = "allows_relevant_crawl"
        record["platform_authorization"] = {"basis":"robots only","evidence_ids":[],"status":"unknown"}
        self.assert_fails(record, "current platform authorization independent")

    def test_crawl_disallow_fails_closed(self):
        record = active_record()
        record["access_method"]["type"] = "scraping_or_crawling"
        record["terms_policy"]["robots_signal"] = "disallows_relevant_crawl"
        self.assert_fails(record, "recorded disallow signal")

    def test_stale_terms_block_active(self):
        record = active_record()
        record["terms_policy"]["review_due_at"] = "2026-08-28T19:00:00Z"
        self.assert_fails(record, "stale")

    def test_explicit_objection_requires_suspension(self):
        record = active_record()
        record["signals"]["explicit_objection"] = True
        self.assert_fails(record, "active status is incompatible")

    def test_block_signal_prevents_active(self):
        record = active_record()
        record["signals"]["blocked"] = True
        self.assert_fails(record, "active status is incompatible")

    def test_challenge_prevents_active(self):
        record = active_record()
        record["signals"]["challenge_present"] = True
        self.assert_fails(record, "active status is incompatible")

    def test_policy_change_prevents_active(self):
        record = active_record()
        record["signals"]["policy_changed"] = True
        self.assert_fails(record, "active status is incompatible")

    def test_human_identity_spoofing_rejected(self):
        record = active_record()
        record["identity"]["spoofs_human_identity"] = True
        self.assert_fails(record, "must not spoof human identity")

    def test_secret_fields_are_rejected(self):
        record = starter()
        record["credentials"]["access_token"] = "definitely-not-real"
        self.assert_fails(record, "prohibited sensitive field")

    def test_embedded_secret_material_rejected(self):
        record = starter()
        record["credentials"]["embedded_secret_material"] = True
        self.assert_fails(record, "embedded_secret_material")

    def test_write_action_requires_write_authority(self):
        record = active_record()
        record["actions"]["write_update"] = "allowed"
        self.assert_fails(record, "write authority")

    def test_purchase_requires_transaction_authority(self):
        record = active_record()
        record["actions"]["purchase_order"] = "allowed"
        self.assert_fails(record, "transaction authority")

    def test_delete_requires_delete_authority(self):
        record = active_record()
        record["actions"]["delete_destroy"] = "allowed"
        self.assert_fails(record, "delete authority")

    def test_active_requires_current_test_evidence(self):
        record = active_record()
        record["evidence"] = [item for item in record["evidence"] if item["id"] != "test"]
        self.assert_fails(record, "current test-result evidence")

    def test_material_authority_requires_evidence(self):
        record = starter()
        record["authority"]["can_activate"] = True
        self.assert_fails(record, "material authority requires evidence")

    def test_suspended_cannot_leave_consequential_actions_allowed(self):
        record = active_record()
        record["status"] = "suspended"
        record["signals"]["explicit_objection"] = True
        record["actions"]["message"] = "allowed"
        record["authority"]["can_write"] = True
        self.assert_fails(record, "suspended records cannot leave consequential actions allowed")


if __name__ == "__main__":
    unittest.main()
