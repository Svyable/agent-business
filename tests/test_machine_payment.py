import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_machine_payment.py"
TEMPLATE = ROOT / "templates" / "MACHINE_PAYMENT_RECORD.json"


class MachinePaymentValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def run_record(self, record):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "record.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(VALIDATOR), str(path)],
                text=True,
                capture_output=True,
                check=False,
            )

    def assert_invalid(self, mutate, message):
        record = copy.deepcopy(self.base)
        mutate(record)
        result = self.run_record(record)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(message, result.stderr + result.stdout)

    def settled_record(self):
        record = copy.deepcopy(self.base)
        record["status"] = "settled"
        record["authorization"]["amount_limit"] = 5
        record["authorization"]["valid_until"] = "2026-08-30T00:00:00Z"
        record["execution"].update({
            "amount": 5,
            "transaction_ref": "txn_public_ref",
            "submitted_at": "2026-08-29T01:00:00Z",
        })
        record["economics"].update({"principal_amount": 5, "total_cash_cost": 5})
        record["authority"].update({"can_execute_payment": True, "can_declare_settled": True})
        record["settlement"].update({
            "state": "settled",
            "finality_basis": "provider settlement record",
            "confirmation_ref": "settlement_public_ref",
            "settled_at": "2026-08-29T01:05:00Z",
            "evidence_ids": ["ev_settlement"],
        })
        record["evidence"].append({
            "id": "ev_settlement",
            "type": "settlement_confirmation",
            "status": "current",
            "observed_at": "2026-08-29T01:05:00Z",
            "reference": "settlement-evidence-pointer",
        })
        return record

    def test_conservative_template_is_valid(self):
        result = self.run_record(self.base)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_settled_record_is_valid(self):
        result = self.run_record(self.settled_record())
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_tool_capability_does_not_replace_execution_authority(self):
        record = self.settled_record()
        record["authority"]["can_execute_payment"] = False
        result = self.run_record(record)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("execution authority", result.stderr + result.stdout)

    def test_counterparty_mismatch_fails(self):
        self.assert_invalid(lambda r: r["authorization"].__setitem__("approved_payee_ref", "different"), "counterparty")

    def test_amount_above_limit_fails(self):
        self.assert_invalid(lambda r: r["execution"].__setitem__("amount", 1), "exceeds authorized limit")

    def test_currency_mismatch_fails(self):
        self.assert_invalid(lambda r: r["execution"].__setitem__("currency_or_asset", "EUR"), "currency/asset")

    def test_stale_authority_evidence_fails(self):
        self.assert_invalid(lambda r: r["evidence"][0].__setitem__("status", "stale"), "requires current evidence")

    def test_sensitive_secret_field_fails(self):
        self.assert_invalid(lambda r: r.__setitem__("private_key", "never-publish"), "prohibited sensitive field")

    def test_submitted_without_transaction_ref_fails(self):
        record = self.settled_record()
        record["execution"]["transaction_ref"] = None
        result = self.run_record(record)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("transaction_ref", result.stderr + result.stdout)

    def test_submission_outside_authorization_window_fails(self):
        record = self.settled_record()
        record["execution"]["submitted_at"] = "2026-08-31T00:00:00Z"
        result = self.run_record(record)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside authorization", result.stderr + result.stdout)

    def test_accepted_cannot_be_claimed_as_settled(self):
        record = self.settled_record()
        record["settlement"]["state"] = "accepted"
        result = self.run_record(record)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("settled or reversed", result.stderr + result.stdout)

    def test_settlement_requires_independent_authority(self):
        record = self.settled_record()
        record["authority"]["can_declare_settled"] = False
        result = self.run_record(record)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("settlement authority", result.stderr + result.stdout)

    def test_settlement_requires_current_evidence(self):
        record = self.settled_record()
        record["evidence"][1]["status"] = "stale"
        result = self.run_record(record)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("settlement requires current evidence", result.stderr + result.stdout)

    def test_economics_must_reconcile(self):
        record = self.settled_record()
        record["economics"]["fees"] = 1
        result = self.run_record(record)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("total_cash_cost", result.stderr + result.stdout)

    def test_principal_must_match_execution_amount(self):
        record = self.settled_record()
        record["economics"]["principal_amount"] = 4
        record["economics"]["total_cash_cost"] = 4
        result = self.run_record(record)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("principal_amount", result.stderr + result.stdout)

    def test_executed_reversal_requires_independent_authority(self):
        record = self.settled_record()
        record["reversal"].update({
            "requested": True,
            "executed": True,
            "amount": 5,
            "idempotency_key": "reverse_1",
            "evidence_ids": ["ev_settlement"],
        })
        result = self.run_record(record)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("reversal/refund authority", result.stderr + result.stdout)

    def test_executed_reversal_requires_own_idempotency_key(self):
        record = self.settled_record()
        record["authority"]["can_reverse_or_refund"] = True
        record["reversal"].update({"requested": True, "executed": True, "amount": 5, "evidence_ids": ["ev_settlement"]})
        result = self.run_record(record)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("idempotency key", result.stderr + result.stdout)

    def test_active_dispute_requires_allegation_and_evidence(self):
        record = self.settled_record()
        record["dispute"]["active"] = True
        result = self.run_record(record)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("allegation", result.stderr + result.stdout)

    def test_closed_requires_reconciliation(self):
        record = self.settled_record()
        record["status"] = "closed"
        record["authority"]["can_close"] = True
        result = self.run_record(record)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("resolved reconciliation", result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
