from __future__ import annotations
import unittest
from scripts.validate_customer_success import validate


def base():
    return {
      "schema_version":"1.0.0","record_id":"customer-test-001","updated_at":"2026-08-28T07:00:00Z","status":"active",
      "account":{"public_alias":"A","tenant_key":"tenant-a","product_or_service":"Outcome service"},
      "lifecycle":{"stage":"healthy","stage_started_at":"2026-08-01T00:00:00Z","activation_definition":"First verified outcome delivered","activated_at":"2026-08-02T00:00:00Z","value_realized_at":"2026-08-03T00:00:00Z"},
      "value":{"promised_outcome":"Reduce cycle time","evidence_ids":["s1"]},
      "signals":[{"id":"s1","classification":"observed","kind":"outcome","description":"Public-safe aggregate outcome observed","source_ref":"metric:cycle-time","observed_at":"2026-08-20T00:00:00Z","status":"current"}],
      "health":{"risk_level":"low","score":20,"score_method":"Documented deterministic rubric","evidence_ids":["s1"],"next_review_at":"2026-09-01T00:00:00Z"},
      "renewal":{"contract_end_at":"2026-12-31T00:00:00Z","notice_deadline_at":"2026-11-30T00:00:00Z","recommendation":"renew","confidence":"medium","evidence_ids":["s1"],"action_status":"needs_review","expansion_proposed":False,"discount_bps":0,"approval":None},
      "incidents":[],
      "communications":{"proactive_contact_allowed":False,"suppressed":False,"last_contact_at":None,"next_contact_at":None,"basis_ref":None},
      "economics":{"currency":"USD","period":"2026-Q3","starting_recurring_revenue_minor":100000,"retained_recurring_revenue_minor":100000,"expansion_revenue_minor":0,"contraction_revenue_minor":0,"churned_revenue_minor":0,"cost_to_serve_minor":20000,"human_review_minutes":30},
      "authority":{"can_contact":False,"can_offer_discount":False,"can_renew_contract":False,"can_issue_credit":False,"can_expand_scope":False,"evidence_ref":None},
      "privacy":{"contains_secrets":False,"contains_private_prompts":False,"contains_payment_credentials":False,"contains_raw_customer_content":False,"tenant_isolation_confirmed":True}
    }

class Tests(unittest.TestCase):
    def test_valid(self): validate(base())
    def test_rejects_health_without_evidence(self):
        r=base(); r["health"]["evidence_ids"]=[]
        with self.assertRaises(SystemExit): validate(r)
    def test_rejects_unknown_signal_ref(self):
        r=base(); r["renewal"]["evidence_ids"]=["missing"]
        with self.assertRaises(SystemExit): validate(r)
    def test_rejects_approval_without_evidence(self):
        r=base(); r["renewal"].update(action_status="approved",evidence_ids=[],approval={"approved_by":"principal","approved_at":"2026-08-28T00:00:00Z","scope":"renew"})
        with self.assertRaises(SystemExit): validate(r)
    def test_rejects_discount_without_authority(self):
        r=base(); r["renewal"]["discount_bps"]=500
        with self.assertRaises(SystemExit): validate(r)
    def test_rejects_executed_renewal_without_authority(self):
        r=base(); r["renewal"].update(action_status="executed",approval={"approved_by":"principal","approved_at":"2026-08-28T00:00:00Z","scope":"renew"})
        with self.assertRaises(SystemExit): validate(r)
    def test_rejects_suppressed_contact(self):
        r=base(); r["communications"].update(suppressed=True,next_contact_at="2026-09-01T00:00:00Z")
        with self.assertRaises(SystemExit): validate(r)
    def test_rejects_contact_without_authority(self):
        r=base(); r["communications"].update(proactive_contact_allowed=True,basis_ref="consent:1")
        with self.assertRaises(SystemExit): validate(r)
    def test_rejects_granted_authority_without_evidence(self):
        r=base(); r["authority"]["can_contact"]=True
        with self.assertRaises(SystemExit): validate(r)
    def test_rejects_execution_with_open_severe_incident(self):
        r=base(); r["authority"].update(can_renew_contract=True,evidence_ref="authority:1"); r["renewal"].update(action_status="executed",approval={"approved_by":"principal","approved_at":"2026-08-28T00:00:00Z","scope":"renew"}); r["incidents"]=[{"id":"i1","severity":"high","status":"open","summary":"Material failure","opened_at":"2026-08-27T00:00:00Z","resolved_at":None}]
        with self.assertRaises(SystemExit): validate(r)
    def test_rejects_raw_customer_content_flag(self):
        r=base(); r["privacy"]["contains_raw_customer_content"]=True
        with self.assertRaises(SystemExit): validate(r)
    def test_rejects_notice_after_contract_end(self):
        r=base(); r["renewal"]["notice_deadline_at"]="2027-01-01T00:00:00Z"
        with self.assertRaises(SystemExit): validate(r)

if __name__=="__main__": unittest.main()
