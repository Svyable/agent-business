#!/usr/bin/env python3
"""Validate Agent Business complaint/redress records without third-party packages."""
from __future__ import annotations
import argparse, json
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROHIBITED={"password","secret","api_key","access_token","refresh_token","authorization_header","private_key","raw_prompt","private_customer_data","payment_data","card_number","cvv","privileged_legal_advice"}
DECISIONAL={"resolved","rejected_with_reason","appealed","closed"}
HIGH_RISK={"safety_security","privacy","billing_financial","unauthorized_action","discrimination_fairness"}

def fail(msg:str)->None: raise SystemExit(f"complaint-redress validation failed: {msg}")
def load(path:Path)->dict:
    try: value=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc: fail(f"cannot parse {path}: {exc}")
    if not isinstance(value,dict): fail("record must be a JSON object")
    return value

def parse_time(value:object,label:str)->datetime:
    if not isinstance(value,str): fail(f"{label} must be ISO-8601")
    try: parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError: fail(f"{label} must be ISO-8601")
    if parsed.tzinfo is None: fail(f"{label} must include timezone")
    return parsed

def scan(value:object,path:str="$")->None:
    if isinstance(value,dict):
        for k,v in value.items():
            if str(k).lower().replace("-","_") in PROHIBITED: fail(f"prohibited sensitive field: {path}.{k}")
            scan(v,f"{path}.{k}")
    elif isinstance(value,list):
        for i,v in enumerate(value): scan(v,f"{path}[{i}]")

def evidence_map(items:object)->dict[str,dict]:
    if not isinstance(items,list): fail("evidence must be a list")
    out={}
    for item in items:
        if not isinstance(item,dict): fail("evidence entries must be objects")
        eid=item.get("id")
        if not isinstance(eid,str) or not eid: fail("evidence ids must be non-empty")
        if eid in out: fail(f"duplicate evidence id: {eid}")
        parse_time(item.get("observed_at"),f"evidence {eid}.observed_at")
        if not isinstance(item.get("reference"),str) or not item.get("reference"): fail(f"evidence {eid}.reference required")
        out[eid]=item
    return out

def current_refs(label:str,refs:object,ev:dict[str,dict],required:bool=False)->None:
    if not isinstance(refs,list): fail(f"{label} evidence_ids must be a list")
    if required and not refs: fail(f"{label} requires evidence")
    for ref in refs:
        if ref not in ev: fail(f"{label} references unknown evidence: {ref}")
        if ev[ref].get("status")!="current": fail(f"{label} requires current evidence: {ref}")

def validate(r:dict)->None:
    required={"schema_version","record_id","status","updated_at","complainant","scope","triage","allegation","facts","interpretation","decision","remediation","appeal","preservation","communication","authority","evidence","privacy"}
    miss=sorted(required-set(r))
    if miss: fail("missing required fields: "+", ".join(miss))
    if r.get("schema_version")!="1.0.0": fail("schema_version must be 1.0.0")
    status=r.get("status")
    if status not in {"received","acknowledged","triaged","investigating","remediation_proposed","awaiting_approval","resolved","rejected_with_reason","appealed","closed"}: fail("status is invalid")
    parse_time(r.get("updated_at"),"updated_at"); scan(r)
    complainant,scope,triage,allegation,interpretation,decision,remediation,appeal,preservation,communication,authority,privacy=(r.get(k) for k in ("complainant","scope","triage","allegation","interpretation","decision","remediation","appeal","preservation","communication","authority","privacy"))
    if not all(isinstance(x,dict) for x in (complainant,scope,triage,allegation,interpretation,decision,remediation,appeal,preservation,communication,authority,privacy)): fail("core sections must be objects")
    for f in ("contains_credentials","contains_private_customer_data","contains_raw_private_prompts","contains_payment_data","contains_privileged_legal_advice"):
        if privacy.get(f) is not False: fail(f"privacy.{f} must be false")
    if privacy.get("public_disclosure_confirmed") is not True: fail("privacy.public_disclosure_confirmed must be true")
    if complainant.get("channel_discoverable") is not True: fail("complaint channel must be discoverable")
    if complainant.get("human_escalation_available") is not True: fail("human escalation path must be available")
    ev=evidence_map(r.get("evidence"))
    categories=triage.get("categories")
    if not isinstance(categories,list) or not categories: fail("triage.categories must be a non-empty list")
    allowed={"safety_security","privacy","billing_financial","unauthorized_action","transparency_deception","service_quality","discrimination_fairness","contractual_scope","other"}
    if any(c not in allowed for c in categories): fail("triage category is invalid")
    severity=triage.get("severity")
    if severity not in {"low","medium","high","critical"}: fail("triage severity is invalid")
    if severity in {"high","critical"} or HIGH_RISK.intersection(categories):
        if triage.get("human_review_required") is not True: fail("high-risk complaint requires human review")
    if status not in {"received","acknowledged"} and not triage.get("owner"): fail(f"{status} requires investigation owner")
    facts=r.get("facts")
    if not isinstance(facts,list): fail("facts must be a list")
    for i,fact in enumerate(facts):
        if not isinstance(fact,dict) or not isinstance(fact.get("statement"),str) or not fact.get("statement"): fail(f"fact {i} must contain statement")
        current_refs(f"fact {i}",fact.get("evidence_ids"),ev,required=True)
    if not isinstance(allegation.get("summary"),str) or not allegation.get("summary"): fail("allegation summary required")
    if not isinstance(interpretation.get("summary"),str): fail("interpretation summary required")
    current_refs("decision",decision.get("evidence_ids"),ev,required=status in DECISIONAL)
    if status in DECISIONAL:
        if decision.get("disposition") in {None,"pending"}: fail(f"{status} requires final decision")
        if not decision.get("decision_maker"): fail(f"{status} requires decision maker")
    if remediation.get("executed"):
        if remediation.get("verified") is not True: fail("executed remediation must be verified")
        current_refs("remediation",remediation.get("evidence_ids"),ev,required=True)
    if remediation.get("consequential"):
        if not remediation.get("idempotency_key"): fail("consequential remediation requires idempotency key")
        if decision.get("independent_from_execution_agent") is not True: fail("consequential remedy requires independent decision authority")
        if authority.get("can_approve_consequential_remedy") is not True: fail("consequential remedy requires explicit approval authority")
        current_refs("consequential remedy authority",authority.get("evidence_ids"),ev,required=True)
    if preservation.get("hold_active"):
        if preservation.get("evidence_preserved") is not True: fail("active hold requires preserved evidence")
        if preservation.get("deletion_blocked_while_held") is not True: fail("active hold must block deletion")
    if appeal.get("requested"):
        if appeal.get("independent_review_required") is not True: fail("appeal requires independent review")
        if not appeal.get("independent_reviewer"): fail("appeal requires independent reviewer")
    if status in {"acknowledged","triaged","investigating","remediation_proposed","awaiting_approval","resolved","rejected_with_reason","appealed","closed"} and communication.get("acknowledged") is not True: fail(f"{status} requires acknowledgement")
    if communication.get("acknowledged"): current_refs("acknowledgement",communication.get("evidence_ids"),ev,required=True)
    if status=="closed":
        if interpretation.get("uncertainty_material") is True and severity in {"high","critical"}: fail("cannot close high-severity complaint with material uncertainty")
        if remediation.get("executed") and remediation.get("verified") is not True: fail("cannot close with unverified remediation")
        if communication.get("decision_delivered") is not True: fail("closed complaint requires decision delivery")
        if appeal.get("requested") and appeal.get("resolved") is not True: fail("cannot close unresolved appeal")
        if authority.get("can_close") is not True: fail("closed complaint requires closure authority")
        current_refs("closure authority",authority.get("evidence_ids"),ev,required=True)
    if status=="appealed" and appeal.get("requested") is not True: fail("appealed status requires appeal.requested")

def main()->None:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("record",nargs="?",default="templates/COMPLAINT_REDRESS_RECORD.json"); a=p.parse_args()
    path=(ROOT/a.record).resolve()
    if path!=ROOT and ROOT not in path.parents: fail("record path must stay inside repository")
    rec=load(path); validate(rec); print(f"complaint redress OK: {rec['record_id']} status={rec['status']} evidence={len(rec['evidence'])}")
if __name__=="__main__": main()
