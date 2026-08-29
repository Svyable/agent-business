import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("validate_complaint_redress",ROOT/"scripts"/"validate_complaint_redress.py")
MOD=importlib.util.module_from_spec(SPEC); assert SPEC.loader is not None; SPEC.loader.exec_module(MOD)
STARTER=json.loads((ROOT/"templates"/"COMPLAINT_REDRESS_RECORD.json").read_text())

def ev(eid,etype="case",status="current"):
    return {"id":eid,"type":etype,"status":status,"observed_at":"2026-08-28T23:55:00Z","reference":f"https://example.com/{eid}"}

def decided_record(status="resolved"):
    r=copy.deepcopy(STARTER); r["status"]=status
    r["triage"]={"categories":["service_quality"],"severity":"medium","owner":"support-human","human_review_required":False}
    r["facts"]=[{"statement":"The disputed action is correlated to the recorded release.","evidence_ids":["fact"]}]
    r["interpretation"]={"summary":"Evidence reviewed.","uncertainty_material":False}
    r["decision"]={"disposition":"no_remedy","rationale":"Evidence does not support remediation.","decision_maker":"reviewer-1","independent_from_execution_agent":True,"evidence_ids":["decision"]}
    r["communication"]={"acknowledged":True,"decision_delivered":status=="closed","evidence_ids":["ack"]}
    r["authority"]={"can_approve_consequential_remedy":False,"can_close":status=="closed","evidence_ids":["auth"] if status=="closed" else []}
    r["evidence"]=[ev("fact"),ev("decision"),ev("ack","communication")]+([ev("auth","authority")] if status=="closed" else [])
    return r

class ComplaintRedressValidationTests(unittest.TestCase):
    def assertFails(self,r,text):
        with self.assertRaises(SystemExit) as cm: MOD.validate(r)
        self.assertIn(text,str(cm.exception))
    def test_starter_safe(self): MOD.validate(copy.deepcopy(STARTER))
    def test_resolved_happy_path(self): MOD.validate(decided_record())
    def test_hidden_channel_rejected(self):
        r=copy.deepcopy(STARTER); r["complainant"]["channel_discoverable"]=False; self.assertFails(r,"discoverable")
    def test_missing_human_escalation_rejected(self):
        r=copy.deepcopy(STARTER); r["complainant"]["human_escalation_available"]=False; self.assertFails(r,"human escalation")
    def test_high_severity_requires_human_review(self):
        r=copy.deepcopy(STARTER); r["triage"]["severity"]="high"; self.assertFails(r,"requires human review")
    def test_privacy_category_requires_human_review(self):
        r=copy.deepcopy(STARTER); r["triage"]["categories"]=["privacy"]; self.assertFails(r,"requires human review")
    def test_fact_requires_evidence(self):
        r=copy.deepcopy(STARTER); r["facts"]=[{"statement":"Claimed fact","evidence_ids":[]}]; self.assertFails(r,"requires evidence")
    def test_stale_fact_evidence_rejected(self):
        r=copy.deepcopy(STARTER); r["facts"]=[{"statement":"Claimed fact","evidence_ids":["f"]}]; r["evidence"]=[ev("f",status="stale")]; self.assertFails(r,"requires current evidence")
    def test_resolved_requires_final_decision(self):
        r=decided_record(); r["decision"]["disposition"]="pending"; self.assertFails(r,"requires final decision")
    def test_executed_remediation_must_be_verified(self):
        r=decided_record(); r["remediation"]["executed"]=["credit-requested"]; r["remediation"]["verified"]=False; self.assertFails(r,"must be verified")
    def test_consequential_remedy_requires_idempotency(self):
        r=decided_record(); r["remediation"]["consequential"]=True; r["authority"]={"can_approve_consequential_remedy":True,"can_close":False,"evidence_ids":["auth"]}; r["evidence"].append(ev("auth","authority")); self.assertFails(r,"idempotency")
    def test_consequential_remedy_requires_independent_authority(self):
        r=decided_record(); r["remediation"]["consequential"]=True; r["remediation"]["idempotency_key"]="complaint-1-remedy-1"; r["decision"]["independent_from_execution_agent"]=False; self.assertFails(r,"independent decision authority")
    def test_consequential_remedy_requires_explicit_authority(self):
        r=decided_record(); r["remediation"]["consequential"]=True; r["remediation"]["idempotency_key"]="complaint-1-remedy-1"; self.assertFails(r,"explicit approval authority")
    def test_hold_blocks_unpreserved_evidence(self):
        r=copy.deepcopy(STARTER); r["preservation"]["hold_active"]=True; self.assertFails(r,"requires preserved evidence")
    def test_appeal_requires_independent_reviewer(self):
        r=decided_record("appealed"); r["appeal"]={"requested":True,"independent_review_required":True,"independent_reviewer":None,"resolved":False}; self.assertFails(r,"independent reviewer")
    def test_closed_requires_decision_delivery(self):
        r=decided_record("closed"); r["communication"]["decision_delivered"]=False; self.assertFails(r,"decision delivery")
    def test_closed_requires_authority(self):
        r=decided_record("closed"); r["authority"]["can_close"]=False; self.assertFails(r,"closure authority")
    def test_high_severity_uncertainty_blocks_closure(self):
        r=decided_record("closed"); r["triage"]={"categories":["safety_security"],"severity":"high","owner":"security-human","human_review_required":True}; r["interpretation"]["uncertainty_material"]=True; self.assertFails(r,"material uncertainty")
    def test_secret_like_field_rejected(self):
        r=copy.deepcopy(STARTER); r["api_key"]="redacted"; self.assertFails(r,"prohibited sensitive field")

if __name__=="__main__": unittest.main()
