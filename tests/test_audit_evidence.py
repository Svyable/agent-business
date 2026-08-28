from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from scripts.verify_audit_evidence import canonical_event_hash, validate

ROOT = Path(__file__).resolve().parents[1]
STARTER = json.loads((ROOT / "templates" / "AUDIT_EVIDENCE_RECORD.json").read_text(encoding="utf-8"))


def base_active() -> dict:
    record = copy.deepcopy(STARTER)
    record["status"] = "active"
    record["scope"]["tenant_scope"] = "tenant-a"
    record["roles"]["runtime_writer"] = "runtime-agent"
    record["roles"]["evidence_custodian"] = "evidence-service"
    record["roles"]["verifier"] = "audit-verifier"
    record["integrity"].update({
        "level": "internally_checked",
        "mode": "hash_chain",
        "algorithm": "sha256",
        "trust_boundary": "Evidence service and verifier are isolated from the acting runtime.",
        "integrity_proven": True,
        "verification_evidence_ids": ["integrity-1"],
    })
    record["evidence"] = [
        {"id":"integrity-1","type":"integrity_verification","status":"current","observed_at":"2026-08-28T17:40:00Z","reference":"private://audit/integrity/1"},
        {"id":"coverage-1","type":"coverage_report","status":"current","observed_at":"2026-08-28T17:41:00Z","reference":"private://audit/coverage/1"},
    ]
    payload = hashlib.sha256(b"redacted tool input").hexdigest()
    event = {
        "event_id":"evt-1","sequence":1,"occurred_at":"2026-08-28T17:39:00Z","event_type":"tool_call",
        "run_id":"run-1","tenant_ref":"tenant-a","agent_id":"agent-1","principal_ref":"principal-1",
        "release_id":"release-1","policy_version":"policy-1","authority_ref":"authority-1","trace_id":"trace-1",
        "side_effect_receipt_ref":"","payload_digest":payload,"prev_hash":"GENESIS","event_hash":"","integrity_status":"verified"
    }
    event["event_hash"] = canonical_event_hash(event)
    record["events"] = [event]
    record["completeness"].update({
        "claim":"partial","scope_start":"2026-08-28T17:39:00Z","scope_end":"2026-08-28T17:42:00Z",
        "expected_event_count":2,"captured_event_count":1,"orphan_tool_calls":0,"missing_authority_links":0
    })
    return record


class AuditEvidenceTests(unittest.TestCase):
    def assert_invalid(self, record: dict, message: str) -> None:
        with self.assertRaises(SystemExit) as caught:
            validate(record)
        self.assertIn(message, str(caught.exception))

    def test_starter_is_safe_and_valid(self) -> None:
        validate(copy.deepcopy(STARTER))

    def test_valid_active_hash_chain(self) -> None:
        validate(base_active())

    def test_sequence_gap_fails(self) -> None:
        record = base_active()
        record["events"][0]["sequence"] = 2
        self.assert_invalid(record, "event sequence must be contiguous")

    def test_reordered_timestamp_fails(self) -> None:
        record = base_active()
        second = copy.deepcopy(record["events"][0])
        second.update({"event_id":"evt-2","sequence":2,"occurred_at":"2026-08-28T17:38:00Z","prev_hash":record["events"][0]["event_hash"]})
        second["event_hash"] = canonical_event_hash(second)
        record["events"].append(second)
        record["completeness"]["captured_event_count"] = 2
        self.assert_invalid(record, "events must be chronological")

    def test_broken_hash_chain_fails(self) -> None:
        record = base_active()
        record["events"][0]["prev_hash"] = "not-genesis"
        self.assert_invalid(record, "broken hash chain")

    def test_overwritten_event_fails_hash_check(self) -> None:
        record = base_active()
        record["events"][0]["release_id"] = "release-tampered"
        self.assert_invalid(record, "event hash mismatch")

    def test_unverifiable_integrity_claim_fails(self) -> None:
        record = base_active()
        record["integrity"]["verification_evidence_ids"] = []
        self.assert_invalid(record, "integrity_proven requires")

    def test_cross_tenant_event_fails(self) -> None:
        record = base_active()
        record["events"][0]["tenant_ref"] = "tenant-b"
        self.assert_invalid(record, "cannot mix tenant scope")

    def test_cross_tenant_export_fails(self) -> None:
        record = copy.deepcopy(STARTER)
        record["export"]["cross_tenant_allowed"] = True
        self.assert_invalid(record, "export.cross_tenant_allowed must be false")

    def test_hold_blocks_deletion(self) -> None:
        record = copy.deepcopy(STARTER)
        record["retention"].update({"active_hold":True,"hold_reference":"case-123","deletion_requested":True})
        self.assert_invalid(record, "fail closed while an evidence hold is active")

    def test_raw_secret_field_fails(self) -> None:
        record = copy.deepcopy(STARTER)
        record["secret"] = "do-not-store"
        self.assert_invalid(record, "prohibited sensitive field")

    def test_tool_event_without_authority_is_counted(self) -> None:
        record = base_active()
        record["events"][0]["authority_ref"] = ""
        record["events"][0]["event_hash"] = canonical_event_hash(record["events"][0])
        record["completeness"]["missing_authority_links"] = 0
        self.assert_invalid(record, "missing_authority_links does not match")

    def test_side_effect_without_receipt_fails(self) -> None:
        record = base_active()
        event = record["events"][0]
        event["event_type"] = "side_effect"
        event["event_hash"] = canonical_event_hash(event)
        self.assert_invalid(record, "side-effect events require a receipt")

    def test_complete_claim_requires_expected_equals_captured(self) -> None:
        record = base_active()
        record["completeness"]["claim"] = "complete_for_declared_scope"
        self.assert_invalid(record, "expected_event_count == captured_event_count")

    def test_complete_claim_requires_coverage_evidence(self) -> None:
        record = base_active()
        record["completeness"].update({"claim":"complete_for_declared_scope","expected_event_count":1})
        record["evidence"] = [item for item in record["evidence"] if item["type"] != "coverage_report"]
        self.assert_invalid(record, "coverage-report evidence")

    def test_active_writer_and_custodian_must_be_separate(self) -> None:
        record = base_active()
        record["roles"]["evidence_custodian"] = "runtime-agent"
        self.assert_invalid(record, "separate runtime writer from evidence custodian")

    def test_signed_mode_needs_signature_verification(self) -> None:
        record = base_active()
        record["integrity"].update({"level":"independently_verifiable","mode":"signed_hash_chain"})
        self.assert_invalid(record, "signature_verification evidence")

    def test_privileged_retention_authority_needs_evidence(self) -> None:
        record = copy.deepcopy(STARTER)
        record["roles"]["can_delete"] = True
        self.assert_invalid(record, "retention/deletion authority requires current authority evidence")


if __name__ == "__main__":
    unittest.main()
