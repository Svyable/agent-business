import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_agent_world_model", ROOT / "scripts" / "validate_agent_world_model.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


def model():
    return json.loads((ROOT / "agent-world-model.json").read_text(encoding="utf-8"))


class AgentWorldModelTests(unittest.TestCase):
    def assert_invalid(self, candidate, needle):
        errors = MOD.validate_model(candidate, ROOT)
        self.assertTrue(any(needle in error for error in errors), errors)

    def test_canonical_world_model_is_valid(self):
        self.assertEqual(MOD.validate_model(model(), ROOT), [])

    def test_empirical_thesis_requires_falsifier(self):
        candidate = model()
        candidate["empirical_theses"][0]["falsifier"] = ""
        self.assert_invalid(candidate, "requires substantive falsifier")

    def test_empirical_thesis_requires_prediction(self):
        candidate = model()
        candidate["empirical_theses"][0]["prediction"] = ""
        self.assert_invalid(candidate, "requires substantive prediction")

    def test_confidence_is_bounded(self):
        candidate = model()
        candidate["empirical_theses"][0]["confidence"] = "certain"
        self.assert_invalid(candidate, "confidence must be")

    def test_missing_resource_is_rejected(self):
        candidate = model()
        candidate["empirical_theses"][0]["related_resources"] = ["docs/DOES_NOT_EXIST.md"]
        self.assert_invalid(candidate, "references missing resource")

    def test_duplicate_thesis_ids_are_rejected(self):
        candidate = model()
        candidate["empirical_theses"][1]["id"] = candidate["empirical_theses"][0]["id"]
        self.assert_invalid(candidate, "duplicate thesis/constraint id")

    def test_normative_constraint_cannot_claim_empirical_confidence(self):
        candidate = model()
        candidate["normative_constraints"][0]["confidence"] = "high"
        self.assert_invalid(candidate, "must not masquerade as an empirical thesis")

    def test_adoption_rule_must_allow_rejection_and_revision(self):
        candidate = model()
        candidate["adoption_rule"] = "Always adopt the canonical model."
        self.assert_invalid(candidate, "evidence-based revision and rejection")

    def test_model_requires_meaningful_thesis_set(self):
        candidate = model()
        candidate["empirical_theses"] = candidate["empirical_theses"][:3]
        self.assert_invalid(candidate, "at least eight empirical theses")


if __name__ == "__main__":
    unittest.main()
