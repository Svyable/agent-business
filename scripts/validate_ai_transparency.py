#!/usr/bin/env python3
"""Validate Agent Business AI transparency records without third-party packages."""
from __future__ import annotations
import argparse, json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "agent-index.json"
PROHIBITED = {"password","secret","api_key","access_token","refresh_token","authorization","private_key","raw_prompt","private_customer_data","unpublished_legal_advice"}
ACTIVEISH = {"configured","tested","active"}

def fail(msg: str) -> None: raise SystemExit(f"ai-transparency validation failed: {msg}")
def load(path: Path) -> dict:
    try: value=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc: fail(f"cannot parse {path}: {exc}")
    if not isinstance(value,dict): fail("record must be a JSON object")
    return value

def parse_time(value: object,label: str)->datetime:
    if not isinstance(value,str): fail(f"{label} must be ISO-8601")
    try: parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError: fail(f"{label} must be ISO-8601")
    if parsed.tzinfo is None: fail(f"{label} must include timezone")
    return parsed

def scan(value: object,path: str="$")->None:
    if isinstance(value,dict):
        for k,v in value.items():
            if str(k).lower().replace("-","_") in PROHIBITED: fail(f"prohibited sensitive field: {path}.{k}")
            scan(v,f"{path}.{k}")
    elif isinstance(value,list):
        for i,v in enumerate(value): scan(v,f"{path}[{i}]")

def evidence_map(items: object)->dict[str,dict]:
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

def current_refs(label: str,refs: object,evidence: dict[str,dict],required: bool=True)->None:
    if not isinstance(refs,list): fail(f"{label} evidence_ids must be a list")
    if required and not refs: fail(f"{label} requires evidence")
    for ref in refs:
        if ref not in evidence: fail(f"{label} references unknown evidence: {ref}")
        if evidence[ref].get("status")!="current": fail(f"{label} requires current evidence: {ref}")

def validate(r: dict)->None:
    req={"schema_version","record_id","status","updated_at","use_case","audience","jurisdictions","role","interaction","content","decision","rulesets","disclosure","provenance","human_review","change_control","authority","evidence","privacy"}
    miss=sorted(req-set(r))
    if miss: fail("missing required fields: "+", ".join(miss))
    if r.get("schema_version")!="1.0.0": fail("schema_version must be 1.0.0")
    statuses={"assessed","disclosure_required","disclosure_not_required","configured","tested","active","changed","suspended","retired"}
    status=r.get("status")
    if status not in statuses: fail("status is invalid")
    updated=parse_time(r.get("updated_at"),"updated_at"); scan(r)
    resources={x.get("id") for x in load(INDEX).get("resources",[]) if isinstance(x,dict)}
    for rid in r.get("repository_resources",[]):
        if rid not in resources: fail(f"unknown repository resource: {rid}")
    ev=evidence_map(r.get("evidence"))
    objs=[r.get(k) for k in ("audience","role","interaction","content","decision","disclosure","provenance","human_review","change_control","authority","privacy")]
    if not all(isinstance(x,dict) for x in objs): fail("core transparency sections must be objects")
    role,decision,disclosure,prov,review,change,auth,privacy=r["role"],r["decision"],r["disclosure"],r["provenance"],r["human_review"],r["change_control"],r["authority"],r["privacy"]
    for f in ("contains_credentials","contains_private_customer_data","contains_raw_private_prompts","contains_unpublished_legal_advice"):
        if privacy.get(f) is not False: fail(f"privacy.{f} must be false")
    if privacy.get("public_disclosure_confirmed") is not True: fail("privacy.public_disclosure_confirmed must be true")
    rules=r.get("rulesets")
    if not isinstance(rules,list): fail("rulesets must be a list")
    for rule in rules:
        if not isinstance(rule,dict): fail("rulesets entries must be objects")
        retrieved=parse_time(rule.get("retrieved_at"),"ruleset.retrieved_at"); due=parse_time(rule.get("review_due_at"),"ruleset.review_due_at")
        if due<=retrieved: fail("ruleset review_due_at must be after retrieved_at")
        if rule.get("status")=="current" and updated>due: fail("current ruleset is stale at record update time")
    if status in {"disclosure_required","disclosure_not_required"}|ACTIVEISH:
        if role.get("classification")=="unknown": fail(f"{status} requires resolved provider/deployer role")
        current_refs("role classification",role.get("evidence_ids"),ev)
        if not any(rule.get("status")=="current" for rule in rules): fail(f"{status} requires a current ruleset")
        current_refs("disclosure decision",decision.get("evidence_ids"),ev)
    required = decision.get("result")=="required" or r["interaction"].get("first_material_interaction_disclosure_required") is True
    if status in ACTIVEISH and required:
        if disclosure.get("configured") is not True: fail(f"{status} requires configured disclosure")
        if disclosure.get("timing") not in {"before_first_material_interaction","at_first_material_interaction"}: fail("required disclosure must occur before or at first material interaction")
        if disclosure.get("accessible") is not True: fail("required disclosure must have an accessible path")
        if disclosure.get("customer_can_disable") is not False: fail("customer configuration cannot disable required disclosure")
    if status in {"tested","active"} and required: current_refs("render testing",disclosure.get("render_test_evidence_ids"),ev)
    if prov.get("required") is True and status in ACTIVEISH:
        if prov.get("configured") is not True or not prov.get("method"): fail("required provenance must be configured with a method")
        current_refs("provenance",prov.get("evidence_ids"),ev)
    if prov.get("required") is True and status in {"tested","active"} and prov.get("export_survival_tested") is not True: fail("required provenance must be tested through supported export paths")
    if review.get("basis_for_exception") is True:
        if review.get("required") is not True: fail("human-review exception must require human review")
        current_refs("human review",review.get("review_evidence_ids"),ev)
    if r["content"].get("public_interest_text") is True and decision.get("result")=="not_required" and review.get("basis_for_exception") is True and not review.get("review_evidence_ids"): fail("public-interest review exception requires review evidence")
    if change.get("material_change_detected") is True and status=="active": fail("active status is invalid after material change until re-review")
    if change.get("material_change_detected") is True and change.get("re_review_required") is not True: fail("material change must trigger re-review")
    if status=="active":
        if decision.get("result")=="review_required": fail("active status cannot retain unresolved disclosure decision")
        if change.get("re_review_required") is True: fail("active status cannot have pending re-review")
        if auth.get("can_activate_transparency_configuration") is not True: fail("active status requires activation authority")
        current_refs("activation authority",auth.get("evidence_ids"),ev)
    if status=="retired" and any(auth.get(k) for k in ("can_activate_transparency_configuration","can_publish")): fail("retired records cannot retain operational authority")

def main()->None:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("record",nargs="?",default="templates/AI_TRANSPARENCY_RECORD.json"); a=p.parse_args()
    path=(ROOT/a.record).resolve()
    if path!=ROOT and ROOT not in path.parents: fail("record path must stay inside repository")
    record=load(path); validate(record); print(f"ai transparency OK: {record['record_id']} status={record['status']} evidence={len(record['evidence'])}")
if __name__=="__main__": main()
