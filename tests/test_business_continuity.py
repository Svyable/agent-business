import json
import unittest
from pathlib import Path

from scripts.validate_business_continuity import validate

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "BUSINESS_CONTINUITY_RECORD.json"


class BusinessContinuityTests(unittest.TestCase):
    def starter(self):
        return json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def ready(self):
        r = self.starter()
        r["status"] = "recovery_ready"
        r["service"].update({"criticality":"critical","rto_minutes":60,"rpo_minutes":15,"maximum_tolerable_downtime_minutes":120})
        r["evidence"] = [
            {"id":"ev-restore","type":"restore_test","status":"current","observed_at":"2026-08-28T14:00:00Z"},
            {"id":"ev-authority","type":"authority_record","status":"current","observed_at":"2026-08-28T14:00:00Z"}
        ]
        r["state_inventory"] = [
            {"component":"agent_definition","recovery_class":"reconstructable","contains_customer_state":False,"recovery_owner":"platform","procedure_defined":True,"evidence_ids":["ev-restore"]},
            {"component":"retrieval_index","recovery_class":"reconstructable","contains_customer_state":True,"recovery_owner":"platform","procedure_defined":True,"evidence_ids":["ev-restore"]},
            {"component":"memory_threads","recovery_class":"backed_up","contains_customer_state":True,"recovery_owner":"platform","procedure_defined":True,"evidence_ids":["ev-restore"]},
            {"component":"queues_jobs","recovery_class":"replicated","contains_customer_state":True,"recovery_owner":"platform","procedure_defined":True,"evidence_ids":["ev-restore"]},
            {"component":"billing_metering","recovery_class":"externally_owned","contains_customer_state":True,"recovery_owner":"finance-system","procedure_defined":True,"evidence_ids":[]}
        ]
        r["recovery_strategy"].update({"mode":"warm_standby","secondary_failure_domain":"secondary-region"})
        r["degraded_mode"] = {"defined":True,"mode":"manual queue and read-only status","customer_impact_recorded":False,"authority_bounded":True}
        r["authority"].update({"can_failover":True,"can_restore":True,"authority_evidence_ids":["ev-authority"]})
        scenarios = [
            "restore_failure","stale_config","dependency_unavailable","retrieval_corruption","partial_memory",
            "control_plane_outage","duplicate_replay","economic_action_replay","premature_traffic","premature_failback"
        ]
        r["drills"] = [
            {"scenario":name,"status":"pass","observed_at":"2026-08-28T14:00:00Z","recovery_time_minutes":30,"recovered_rpo_minutes":10,"integrity_ok":True,"reconciliation_ok":True,"evidence_ids":["ev-restore"]}
            for name in scenarios
        ]
        return r

    def assert_invalid(self, record, text):
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn(text, str(ctx.exception))

    def test_safe_starter_is_valid(self):
        validate(self.starter())

    def test_complete_recovery_ready_record_is_valid(self):
        validate(self.ready())

    def test_rto_cannot_exceed_maximum_tolerable_downtime(self):
        r = self.starter()
        r["service"]["rto_minutes"] = 4000
        self.assert_invalid(r, "RTO cannot exceed")

    def test_customer_state_cannot_be_silently_ephemeral(self):
        r = self.ready()
        r["state_inventory"][1]["recovery_class"] = "ephemeral"
        self.assert_invalid(r, "cannot be silently classified as ephemeral")

    def test_recoverable_state_requires_procedure(self):
        r = self.ready()
        r["state_inventory"][0]["procedure_defined"] = False
        self.assert_invalid(r, "defined recovery procedure")

    def test_backup_claim_requires_current_evidence(self):
        r = self.ready()
        r["evidence"][0]["status"] = "stale"
        self.assert_invalid(r, "must reference current evidence")

    def test_dependency_order_blocks_traffic_first(self):
        r = self.starter()
        r["recovery_strategy"]["dependency_order"] = list(reversed(r["recovery_strategy"]["dependency_order"]))
        self.assert_invalid(r, "restore identity/policy/data controls before traffic")

    def test_queue_replay_must_require_idempotency(self):
        r = self.starter()
        r["recovery_strategy"]["queue_replay_requires_idempotency"] = False
        self.assert_invalid(r, "queue_replay_requires_idempotency")

    def test_economic_action_replay_requires_reconciliation(self):
        r = self.starter()
        r["recovery_strategy"]["economic_actions_require_reconciliation"] = False
        self.assert_invalid(r, "economic_actions_require_reconciliation")

    def test_material_recovery_authority_requires_evidence(self):
        r = self.starter()
        r["authority"]["can_restore"] = True
        self.assert_invalid(r, "material recovery authority")

    def test_warm_standby_requires_failover_authority(self):
        r = self.ready()
        r["authority"]["can_failover"] = False
        self.assert_invalid(r, "requires failover authority")

    def test_recovery_ready_requires_restore_drill_suite(self):
        r = self.ready()
        r["drills"] = [x for x in r["drills"] if x["scenario"] != "duplicate_replay"]
        self.assert_invalid(r, "missing recovery drills")

    def test_failed_drill_blocks_recovery_ready(self):
        r = self.ready()
        r["drills"][0]["status"] = "fail"
        self.assert_invalid(r, "must pass integrity")

    def test_drill_must_meet_rto(self):
        r = self.ready()
        r["drills"][0]["recovery_time_minutes"] = 61
        self.assert_invalid(r, "exceeds declared RTO")

    def test_drill_must_meet_rpo(self):
        r = self.ready()
        r["drills"][0]["recovered_rpo_minutes"] = 16
        self.assert_invalid(r, "exceeds declared RPO")

    def test_resume_traffic_requires_all_recovery_gates(self):
        r = self.ready()
        r["authority"]["can_resume_normal_traffic"] = True
        self.assert_invalid(r, "normal traffic blocked by recovery gate")

    def test_recovered_with_gates_and_authority_is_valid(self):
        r = self.ready()
        r["status"] = "recovered"
        r["degraded_mode"]["customer_impact_recorded"] = True
        r["authority"]["can_resume_normal_traffic"] = True
        for key in r["recovery_gate"]:
            r["recovery_gate"][key] = True
        validate(r)

    def test_sensitive_recovery_key_is_rejected(self):
        r = self.starter()
        r["recovery_key"] = "do-not-store-this"
        self.assert_invalid(r, "prohibited sensitive field")


if __name__ == "__main__":
    unittest.main()
