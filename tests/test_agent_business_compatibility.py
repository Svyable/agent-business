import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "agent_business_compatibility.py"
SPEC = importlib.util.spec_from_file_location("agent_business_compatibility", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def load_template():
    return json.loads((ROOT / "templates" / "AGENT_BUSINESS_COMPATIBILITY.json").read_text())


def tested(convention):
    convention["support_state"] = "tested"
    convention["test_evidence_ref"] = "public:test:ref"
    convention["tested_at"] = "2026-08-29T00:00:00Z"
    convention["evidence_expires_at"] = "2026-09-29T00:00:00Z"
    return convention


class CompatibilityProfileTests(unittest.TestCase):
    def assert_invalid(self, record, needle):
        errors = MODULE.validate_profile(record)
        self.assertTrue(any(needle in error for error in errors), errors)

    def test_safe_template_validates(self):
        self.assertEqual(MODULE.validate_profile(load_template()), [])

    def test_authority_can_never_be_granted(self):
        record = load_template()
        record["compatibility_grants_authority"] = True
        self.assert_invalid(record, "must be false")

    def test_certification_claim_rejected(self):
        record = load_template()
        record["certification_claim"] = "Agent Business certified"
        self.assert_invalid(record, "must not claim")

    def test_duplicate_convention_rejected(self):
        record = load_template()
        record["conventions"].append(copy.deepcopy(record["conventions"][0]))
        self.assert_invalid(record, "duplicate convention")

    def test_unknown_convention_requires_namespace(self):
        record = load_template()
        record["conventions"][0]["id"] = "magic-trust"
        self.assert_invalid(record, "must use x- namespace")

    def test_custom_convention_namespace_allowed(self):
        record = load_template()
        record["conventions"][0]["id"] = "x-example-custom"
        self.assertEqual(MODULE.validate_profile(record), [])

    def test_tested_support_requires_test_evidence(self):
        record = load_template()
        record["conventions"][0]["support_state"] = "tested"
        record["conventions"][0]["tested_at"] = "2026-08-29T00:00:00Z"
        record["conventions"][0]["evidence_expires_at"] = "2026-09-29T00:00:00Z"
        self.assert_invalid(record, "test_evidence_ref")

    def test_production_support_requires_scope(self):
        record = load_template()
        item = record["conventions"][0]
        item["support_state"] = "observed_in_production"
        item["production_evidence_ref"] = "public:prod:ref"
        item["observed_at"] = "2026-08-29T00:00:00Z"
        item["evidence_expires_at"] = "2026-09-29T00:00:00Z"
        self.assert_invalid(record, "observation_scope")

    def test_independent_verification_requires_verifier(self):
        record = load_template()
        item = record["conventions"][0]
        item["support_state"] = "independently_verified"
        item["verification_evidence_ref"] = "public:verify:ref"
        item["verified_at"] = "2026-08-29T00:00:00Z"
        item["evidence_expires_at"] = "2026-09-29T00:00:00Z"
        self.assert_invalid(record, "verifier_ref")

    def test_non_declared_evidence_must_outlive_observation(self):
        record = load_template()
        item = tested(record["conventions"][0])
        item["evidence_expires_at"] = "2026-08-28T00:00:00Z"
        self.assert_invalid(record, "after tested_at")

    def test_profile_expiry_must_follow_update(self):
        record = load_template()
        record["expires_at"] = "2026-08-29T00:00:00Z"
        self.assert_invalid(record, "after updated_at")


class NegotiationTests(unittest.TestCase):
    def test_same_profiles_negotiate_structured(self):
        left = load_template()
        right = copy.deepcopy(left)
        right["profile_id"] = "right"
        result = MODULE.negotiate(left, right)
        self.assertEqual(result["transaction_mode"], "structured")
        self.assertFalse(result["authority_granted"])

    def test_required_missing_convention_stops(self):
        left = load_template()
        right = copy.deepcopy(left)
        right["profile_id"] = "right"
        right["conventions"] = [c for c in right["conventions"] if c["id"] != "bounded-authority"]
        result = MODULE.negotiate(left, right)
        self.assertEqual(result["transaction_mode"], "stop")
        self.assertTrue(any(b["reason"] == "required_convention_missing" for b in result["blockers"]))

    def test_required_major_version_mismatch_stops(self):
        left = load_template()
        right = copy.deepcopy(left)
        right["profile_id"] = "right"
        next(c for c in right["conventions"] if c["id"] == "bounded-authority")["spec_version"] = "2.0.0"
        result = MODULE.negotiate(left, right)
        self.assertEqual(result["transaction_mode"], "stop")
        self.assertTrue(any(b["reason"] == "required_major_version_mismatch" for b in result["blockers"]))

    def test_optional_missing_uses_declared_fallback(self):
        left = load_template()
        right = copy.deepcopy(left)
        right["profile_id"] = "right"
        right["conventions"] = [c for c in right["conventions"] if c["id"] != "machine-rfq"]
        result = MODULE.negotiate(left, right)
        self.assertEqual(result["transaction_mode"], "reduced")
        self.assertTrue(any(f["convention_id"] == "machine-rfq" for f in result["fallbacks"]))

    def test_effective_support_is_weaker_claim(self):
        left = load_template()
        right = copy.deepcopy(left)
        right["profile_id"] = "right"
        left_item = next(c for c in left["conventions"] if c["id"] == "evidence-provenance")
        right_item = next(c for c in right["conventions"] if c["id"] == "evidence-provenance")
        tested(left_item)
        right_item["support_state"] = "declared"
        result = MODULE.negotiate(left, right)
        shared = next(s for s in result["shared"] if s["convention_id"] == "evidence-provenance")
        self.assertEqual(shared["effective_support_state"], "declared")

    def test_negotiated_version_uses_lower_compatible_version(self):
        left = load_template()
        right = copy.deepcopy(left)
        right["profile_id"] = "right"
        next(c for c in left["conventions"] if c["id"] == "machine-proposal")["spec_version"] = "1.4.0"
        next(c for c in right["conventions"] if c["id"] == "machine-proposal")["spec_version"] = "1.2.3"
        result = MODULE.negotiate(left, right)
        shared = next(s for s in result["shared"] if s["convention_id"] == "machine-proposal")
        self.assertEqual(shared["negotiated_version"], "1.2.3")

    def test_custom_shared_semantics_not_labeled_standard(self):
        left = load_template()
        right = copy.deepcopy(left)
        custom = copy.deepcopy(left["conventions"][0])
        custom["id"] = "x-example-extension"
        custom["required_for_transaction"] = False
        left["conventions"].append(custom)
        right["conventions"].append(copy.deepcopy(custom))
        result = MODULE.negotiate(left, right)
        self.assertTrue(any(c["convention_id"] == "x-example-extension" for c in result["custom_shared"]))
        self.assertFalse(any(c["convention_id"] == "x-example-extension" for c in result["shared"]))

    def test_core_missing_but_not_required_is_reduced_not_structured(self):
        left = load_template()
        right = copy.deepcopy(left)
        for profile in (left, right):
            for item in profile["conventions"]:
                if item["id"] == "economic-state-separation":
                    item["required_for_transaction"] = False
            profile["conventions"] = [c for c in profile["conventions"] if c["id"] != "economic-state-separation"]
        result = MODULE.negotiate(left, right)
        self.assertEqual(result["transaction_mode"], "reduced")


if __name__ == "__main__":
    unittest.main()
