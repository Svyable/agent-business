import copy, importlib.util, json, pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("deal",ROOT/"scripts"/"compile_agent_deal.py"); deal=importlib.util.module_from_spec(spec); spec.loader.exec_module(deal)

def profile(pid, conventions):
    return {"profile_id":pid,"conventions":[{"id":c,"spec_version":"1.0.0","support_state":"declared","required_for_transaction":c in {"evidence-provenance","bounded-authority","economic-state-separation"}} for c in conventions]}
ALL={"evidence-provenance","bounded-authority","versioned-commercial-truth","economic-state-separation","machine-rfq","machine-proposal","machine-payment-reconciliation","execution-evidence"}
class DealCompilerTests(unittest.TestCase):
    def setUp(self):
        self.rfq={"request_id":"r1","request_version":"1.0.0","authority":{"authority_state":"active","max_authorized_spend_minor":10000}}
        self.proposal={"proposal_id":"p1","proposal_version":"1.0.0","offer":{"total_price_minor":5000},"eligibility":{"eligible_for_award":True},"selection":{"selected_at":"2026-08-30T00:00:00Z"}}
        self.buyer=profile("buyer",ALL); self.seller=profile("seller",ALL)
    def test_fully_structured_corridor_is_ready_but_not_authorized(self):
        p=deal.compile_plan(self.rfq,self.proposal,self.buyer,self.seller)
        self.assertTrue(p["plan_ready"]); self.assertFalse(p["action_authorized"]); self.assertFalse(p["grants_authority"])
    def test_ineligible_proposal_blocks_downstream(self):
        q=copy.deepcopy(self.proposal); q["eligibility"]["eligible_for_award"]=False
        p=deal.compile_plan(self.rfq,q,self.buyer,self.seller)
        self.assertFalse(p["plan_ready"]); self.assertGreater(p["coordination_friction"]["blocked_transitions"],0)
    def test_unselected_proposal_cannot_reach_payment(self):
        q=copy.deepcopy(self.proposal); q["selection"]["selected_at"]=None
        p=deal.compile_plan(self.rfq,q,self.buyer,self.seller)
        execute=next(x for x in p["transitions"] if x["transition"]=="execute_payment")
        self.assertEqual(execute["status"],"blocked")
    def test_price_above_authority_blocks_payment(self):
        q=copy.deepcopy(self.proposal); q["offer"]["total_price_minor"]=20000
        p=deal.compile_plan(self.rfq,q,self.buyer,self.seller)
        execute=next(x for x in p["transitions"] if x["transition"]=="execute_payment")
        self.assertEqual(execute["status"],"blocked"); self.assertIn("authority",execute["reasons"][0])
    def test_missing_optional_convention_does_not_become_authority(self):
        seller=profile("seller",ALL-{"execution-evidence"})
        p=deal.compile_plan(self.rfq,self.proposal,self.buyer,seller)
        deliver=next(x for x in p["transitions"] if x["transition"]=="deliver")
        self.assertEqual(deliver["status"],"unsupported"); self.assertFalse(deliver["grants_authority"])
    def test_required_compatibility_blocker_stops_corridor(self):
        seller=profile("seller",ALL-{"bounded-authority"})
        p=deal.compile_plan(self.rfq,self.proposal,self.buyer,seller)
        self.assertFalse(p["plan_ready"]); self.assertTrue(all(x["status"]=="blocked" for x in p["transitions"]))
    def test_template_is_fail_closed(self):
        p=json.loads((ROOT/"templates"/"AGENT_DEAL_PLAN.json").read_text())
        self.assertFalse(p["plan_ready"]); self.assertFalse(p["action_authorized"]); self.assertEqual(p["coordination_friction"]["blocked_transitions"],10)
if __name__=="__main__": unittest.main()
