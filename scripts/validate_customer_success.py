#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROHIBITED = {"password","secret","api_key","access_token","refresh_token","authorization","raw_prompt","prompt_content","card_number","cvv","bank_account","payment_credential"}


def fail(msg: str) -> None:
    raise SystemExit(f"customer-success validation failed: {msg}")


def load(path: Path) -> dict:
    try: data=json.loads(path.read_text())
    except Exception as e: fail(f"cannot parse {path}: {e}")
    if not isinstance(data, dict): fail("record must be an object")
    return data


def ts(v, label):
    if v is None: return None
    if not isinstance(v,str): fail(f"{label} must be ISO-8601")
    try: d=datetime.fromisoformat(v.replace("Z","+00:00"))
    except ValueError: fail(f"{label} must be ISO-8601")
    if d.tzinfo is None: fail(f"{label} must include timezone")
    return d


def scan(v, path="$"):
    if isinstance(v,dict):
        for k,c in v.items():
            if str(k).lower().replace("-","_") in PROHIBITED: fail(f"prohibited sensitive field: {path}.{k}")
            scan(c,f"{path}.{k}")
    elif isinstance(v,list):
        for i,c in enumerate(v): scan(c,f"{path}[{i}]")


def validate(r: dict) -> None:
    required={"schema_version","record_id","updated_at","status","account","lifecycle","value","signals","health","renewal","incidents","communications","economics","authority","privacy"}
    missing=required-set(r)
    if missing: fail("missing fields: "+", ".join(sorted(missing)))
    if r["schema_version"]!="1.0.0": fail("schema_version must be 1.0.0")
    ts(r["updated_at"],"updated_at"); scan(r)
    signals={}
    for s in r["signals"]:
        sid=s.get("id")
        if not sid or sid in signals: fail("signal ids must be unique and non-empty")
        signals[sid]=s; ts(s.get("observed_at"),f"signal {sid}.observed_at")
        if s.get("classification")=="model_inference" and s.get("kind")=="sentiment" and "customer said" in s.get("description","").lower():
            fail("model-inferred sentiment must not be phrased as a customer statement")
    def refs(ids,label,current=False):
        unknown=set(ids)-set(signals)
        if unknown: fail(f"{label} references unknown signals: {', '.join(sorted(unknown))}")
        if current:
            bad=[i for i in ids if signals[i].get("status")!="current"]
            if bad: fail(f"{label} references non-current signals: {', '.join(bad)}")
    refs(r["value"].get("evidence_ids",[]),"value")
    health=r["health"]; refs(health.get("evidence_ids",[]),"health")
    if health.get("risk_level")!="unknown" and not health.get("evidence_ids"): fail("non-unknown health requires evidence")
    if health.get("score") is not None and not health.get("evidence_ids"): fail("health score requires evidence")
    ts(health.get("next_review_at"),"health.next_review_at")
    renewal=r["renewal"]; refs(renewal.get("evidence_ids",[]),"renewal")
    end=ts(renewal.get("contract_end_at"),"renewal.contract_end_at"); notice=ts(renewal.get("notice_deadline_at"),"renewal.notice_deadline_at")
    if notice and end and notice>end: fail("renewal notice deadline cannot be after contract end")
    if renewal.get("recommendation")!="none" and not renewal.get("evidence_ids"): fail("renewal recommendation requires evidence")
    if renewal.get("action_status") in {"approved","executed"}:
        if not renewal.get("approval"): fail("approved/executed renewal action requires explicit approval")
        if not renewal.get("evidence_ids"): fail("approved/executed renewal action requires evidence")
        refs(renewal["evidence_ids"],"renewal action",current=True)
        ts(renewal["approval"].get("approved_at"),"renewal.approval.approved_at")
    auth=r["authority"]
    if any(auth.get(k) for k in ["can_contact","can_offer_discount","can_renew_contract","can_issue_credit","can_expand_scope"]) and not auth.get("evidence_ref"):
        fail("granted authority requires authority.evidence_ref")
    if renewal.get("discount_bps",0)>0 and not auth.get("can_offer_discount"): fail("discount requires can_offer_discount authority")
    if renewal.get("action_status")=="executed" and renewal.get("recommendation") in {"renew","retain","renegotiate"} and not auth.get("can_renew_contract"):
        fail("executed renewal requires can_renew_contract authority")
    if (renewal.get("expansion_proposed") or renewal.get("recommendation")=="expand") and renewal.get("action_status")=="executed" and not auth.get("can_expand_scope"):
        fail("executed expansion requires can_expand_scope authority")
    comm=r["communications"]
    if comm.get("suppressed") and (comm.get("proactive_contact_allowed") or comm.get("next_contact_at") is not None): fail("suppressed account cannot have proactive contact or scheduled next contact")
    if comm.get("proactive_contact_allowed"):
        if not auth.get("can_contact"): fail("proactive contact requires can_contact authority")
        if not comm.get("basis_ref"): fail("proactive contact requires communications.basis_ref")
    for inc in r["incidents"]:
        ts(inc.get("opened_at"),f"incident {inc.get('id')}.opened_at")
        if inc.get("status")=="resolved" and not inc.get("resolved_at"): fail("resolved incident requires resolved_at")
    unresolved=[i for i in r["incidents"] if i.get("status")!="resolved" and i.get("severity") in {"high","critical"}]
    if unresolved and renewal.get("action_status")=="executed": fail("cannot execute renewal/expansion with unresolved high/critical incidents")
    privacy=r["privacy"]
    for k in ["contains_secrets","contains_private_prompts","contains_payment_credentials","contains_raw_customer_content"]:
        if privacy.get(k) is not False: fail(f"privacy.{k} must be false")
    if privacy.get("tenant_isolation_confirmed") is not True: fail("tenant isolation must be confirmed")


def main():
    p=argparse.ArgumentParser(); p.add_argument("record",nargs="?",default="templates/CUSTOMER_SUCCESS_RECORD.json"); a=p.parse_args()
    path=(ROOT/a.record).resolve()
    if path!=ROOT and ROOT not in path.parents: fail("record path must stay inside repository")
    r=load(path); validate(r); print(f"customer success OK: {r['record_id']} stage={r['lifecycle']['stage']} signals={len(r['signals'])} incidents={len(r['incidents'])}")

if __name__=="__main__": main()
