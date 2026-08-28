#!/usr/bin/env python3
"""Validate Agent Business data-residency records without third-party packages."""
from __future__ import annotations
import argparse, json
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROHIBITED={"password","secret","api_key","access_token","refresh_token","authorization","private_key","raw_prompt","private_customer_data","encryption_key","unpublished_legal_advice"}
ACTIVEISH={"configured","tested","active"}

def fail(msg:str)->None: raise SystemExit(f"data-residency validation failed: {msg}")
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

def current_refs(label:str,refs:object,ev:dict[str,dict],required:bool=True)->None:
    if not isinstance(refs,list): fail(f"{label} evidence_ids must be a list")
    if required and not refs: fail(f"{label} requires evidence")
    for ref in refs:
        if ref not in ev: fail(f"{label} references unknown evidence: {ref}")
        if ev[ref].get("status")!="current": fail(f"{label} requires current evidence: {ref}")

def validate(r:dict)->None:
    required={"schema_version","record_id","status","updated_at","tenant_scope","requirements","data_paths","failover","change_control","authority","evidence","privacy"}
    miss=sorted(required-set(r))
    if miss: fail("missing required fields: "+", ".join(miss))
    if r.get("schema_version")!="1.0.0": fail("schema_version must be 1.0.0")
    status=r.get("status")
    if status not in {"inventory","requirements_mapped","architecture_selected","configured","tested","active","changed","suspended","retired"}: fail("status is invalid")
    parse_time(r.get("updated_at"),"updated_at"); scan(r)
    tenant,failover,change,auth,privacy=(r.get(k) for k in ("tenant_scope","failover","change_control","authority","privacy"))
    if not all(isinstance(x,dict) for x in (tenant,failover,change,auth,privacy)): fail("core sections must be objects")
    for f in ("contains_credentials","contains_private_customer_data","contains_raw_private_prompts","contains_keys","contains_unpublished_legal_advice"):
        if privacy.get(f) is not False: fail(f"privacy.{f} must be false")
    if privacy.get("public_disclosure_confirmed") is not True: fail("privacy.public_disclosure_confirmed must be true")
    ev=evidence_map(r.get("evidence"))
    reqs=r.get("requirements")
    if not isinstance(reqs,list): fail("requirements must be a list")
    reqmap={}
    for req in reqs:
        if not isinstance(req,dict) or not req.get("id"): fail("requirements entries need ids")
        if req["id"] in reqmap: fail(f"duplicate requirement id: {req['id']}")
        allowed=req.get("allowed_geographies")
        if not isinstance(allowed,list): fail("allowed_geographies must be a list")
        reqmap[req["id"]]=req
        if status in ACTIVEISH: current_refs(f"requirement {req['id']}",req.get("evidence_ids"),ev)
    paths=r.get("data_paths")
    if not isinstance(paths,list): fail("data_paths must be a list")
    seen=set()
    for path in paths:
        if not isinstance(path,dict) or not path.get("id"): fail("data paths need ids")
        if path["id"] in seen: fail(f"duplicate data path id: {path['id']}")
        seen.add(path["id"])
        rid=path.get("requirement_id")
        if rid and rid not in reqmap: fail(f"data path {path['id']} references unknown requirement")
        if status in ACTIVEISH and path.get("material"):
            for field in ("storage_region","processing_region","telemetry_region","control_plane_region","provider","subprocessor_location","support_admin_geography"):
                if path.get(field) in (None,"","unknown"): fail(f"active material path {path['id']} has unknown {field}")
            if path.get("routing_mode")=="unknown": fail(f"active material path {path['id']} has unknown routing mode")
            if tenant.get("constrained") and path.get("routing_mode")=="global": fail("constrained tenant cannot use global endpoint")
            allowed=set(reqmap.get(rid,{}).get("allowed_geographies",[]))
            if allowed:
                observed=[path.get("storage_region"),path.get("processing_region"),path.get("telemetry_region"),path.get("control_plane_region")]+list(path.get("backup_regions",[]))+list(path.get("failover_regions",[]))
                bad=[x for x in observed if x and x not in allowed]
                if bad: fail(f"data path {path['id']} uses disallowed geography: {', '.join(sorted(set(bad)))}")
            current_refs(f"data path {path['id']}",path.get("evidence_ids"),ev)
    if status in {"tested","active"}:
        if failover.get("compliant") is not True or failover.get("tested") is not True: fail(f"{status} requires compliant tested failover")
        current_refs("failover",failover.get("evidence_ids"),ev)
    if change.get("material_change_detected") is True:
        if change.get("re_review_required") is not True: fail("material change must trigger re-review")
        if status=="active": fail("active status invalid after material change")
    if status=="active":
        if auth.get("can_activate") is not True: fail("active status requires activation authority")
        current_refs("activation authority",auth.get("evidence_ids"),ev)
        if any(path.get("material") for path in paths) and not reqs: fail("active material processing requires mapped requirements")
    if status=="retired" and auth.get("can_activate"): fail("retired record cannot retain activation authority")

def main()->None:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("record",nargs="?",default="templates/DATA_RESIDENCY_RECORD.json"); a=p.parse_args()
    path=(ROOT/a.record).resolve()
    if path!=ROOT and ROOT not in path.parents: fail("record path must stay inside repository")
    rec=load(path); validate(rec); print(f"data residency OK: {rec['record_id']} status={rec['status']} paths={len(rec['data_paths'])}")
if __name__=="__main__": main()
