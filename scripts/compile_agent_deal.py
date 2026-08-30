#!/usr/bin/env python3
"""Compile buyer intent, seller proposal, and compatibility into a safe deal plan."""
from __future__ import annotations
import argparse, importlib.util, json, sys
from pathlib import Path

try:
    from agent_business_compatibility import negotiate, validate_profile
except ModuleNotFoundError:
    _compat_path = Path(__file__).with_name("agent_business_compatibility.py")
    _spec = importlib.util.spec_from_file_location("agent_business_compatibility", _compat_path)
    if _spec is None or _spec.loader is None:
        raise
    _compat = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_compat)
    negotiate = _compat.negotiate
    validate_profile = _compat.validate_profile

TRANSITIONS = [
    ("qualify", "machine-rfq", False), ("compare", "machine-proposal", False),
    ("select", "economic-state-separation", False), ("contract", "versioned-commercial-truth", True),
    ("authorize_payment", "bounded-authority", True), ("execute_payment", "machine-payment-reconciliation", True),
    ("settle", "machine-payment-reconciliation", False), ("deliver", "execution-evidence", False),
    ("accept", "evidence-provenance", True), ("close_or_dispute", "economic-state-separation", False),
]

def load(path: Path) -> dict:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise ValueError(f"{path} root must be an object")
    return value

def compile_plan(rfq: dict, proposal: dict, buyer: dict, seller: dict) -> dict:
    handshake=negotiate(buyer,seller); shared={x["convention_id"] for x in handshake["shared"]}; fallbacks={x["convention_id"]:x["fallback"] for x in handshake["fallbacks"]}
    transitions=[]; minimum_work=[]
    eligible=proposal.get("eligibility",{}).get("eligible_for_award") is True; selected=bool(proposal.get("selection",{}).get("selected_at"))
    buyer_authority=rfq.get("authority",{}).get("authority_state"); price=proposal.get("offer",{}).get("total_price_minor"); max_spend=rfq.get("authority",{}).get("max_authorized_spend_minor")
    authority_ok=buyer_authority not in (None,"none","unknown") and isinstance(price,int) and isinstance(max_spend,int) and price<=max_spend
    for name,convention,human_if_missing in TRANSITIONS:
        status,reasons,fallback="ready",[],None
        if handshake["transaction_mode"]=="stop": status,reasons="blocked",["compatibility handshake has required blockers"]
        elif convention not in shared:
            fallback=fallbacks.get(convention)
            if fallback: status,reasons="human_review",[f"{convention} not shared; use explicit fallback"]
            elif human_if_missing: status,reasons="human_review",[f"{convention} not shared and transition requires independent review"]
            else: status,reasons="unsupported",[f"{convention} not shared"]
        if name in {"select","contract","authorize_payment","execute_payment","settle","deliver","accept","close_or_dispute"} and not eligible: status,reasons="blocked",["proposal is not eligible for award"]
        if name in {"contract","authorize_payment","execute_payment","settle","deliver","accept","close_or_dispute"} and not selected: status,reasons="blocked",["proposal has not been selected"]
        if name in {"authorize_payment","execute_payment"} and selected and eligible and not authority_ok: status,reasons="blocked",["current buyer payment authority does not cover proposal price"]
        transitions.append({"transition":name,"convention":convention,"status":status,"reasons":reasons,"fallback":fallback,"grants_authority":False})
        if status!="ready": minimum_work.append({"transition":name,"status":status,"work":reasons[0]})
    friction={"blocked_transitions":sum(x["status"]=="blocked" for x in transitions),"human_reviews":sum(x["status"]=="human_review" for x in transitions),"unsupported_transitions":sum(x["status"]=="unsupported" for x in transitions),"fallbacks":sum(x["fallback"] is not None for x in transitions)}
    return {"schema_version":"1.0.0","plan_id":f"deal:{rfq.get('request_id')}:{proposal.get('proposal_id')}","request_ref":{"id":rfq.get("request_id"),"version":rfq.get("request_version")},"proposal_ref":{"id":proposal.get("proposal_id"),"version":proposal.get("proposal_version")},"compatibility":handshake,"plan_ready":friction["blocked_transitions"]==0,"action_authorized":False,"grants_authority":False,"transitions":transitions,"coordination_friction":friction,"minimum_work_to_transact":minimum_work,"invariants":["selection is not contract","payment authority is not payment execution","settlement is not delivery","payment is not acceptance","compiler output never grants authority"]}

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("rfq",type=Path); p.add_argument("proposal",type=Path); p.add_argument("buyer_profile",type=Path); p.add_argument("seller_profile",type=Path); p.add_argument("--output",type=Path); a=p.parse_args()
    try: rfq,proposal,buyer,seller=map(load,[a.rfq,a.proposal,a.buyer_profile,a.seller_profile])
    except (OSError,json.JSONDecodeError,ValueError) as e: print(f"ERROR: {e}",file=sys.stderr); return 2
    errors=validate_profile(buyer)+["seller: "+e for e in validate_profile(seller)]
    if errors:
        for e in errors: print("ERROR: "+e,file=sys.stderr)
        return 1
    plan=compile_plan(rfq,proposal,buyer,seller); text=json.dumps(plan,indent=2,sort_keys=True)+"\n"
    if a.output: a.output.write_text(text,encoding="utf-8")
    else: print(text,end="")
    return 0 if plan["plan_ready"] else 3
if __name__=="__main__": raise SystemExit(main())
