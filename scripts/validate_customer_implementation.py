#!/usr/bin/env python3
"""Validate customer implementation, go-live, and adoption records without third-party packages."""
from __future__ import annotations
import argparse, json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "agent-index.json"
PROD_STATUSES = {"rollout_ready", "live", "hypercare", "handed_to_customer_success"}
PROHIBITED_KEYS = {"password","secret","api_key","access_token","refresh_token","authorization","credential","credentials","raw_customer_data","private_prompt","raw_prompt"}

def fail(message: str) -> None: raise SystemExit(f"customer-implementation validation failed: {message}")
def load(path: Path) -> dict:
    try: value=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc: fail(f"cannot parse {path}: {exc}")
    if not isinstance(value,dict): fail("record must be a JSON object")
    return value
def parse_time(value: object,label: str) -> datetime:
    if not isinstance(value,str): fail(f"{label} must be an ISO-8601 date-time")
    try: result=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError: fail(f"{label} must be an ISO-8601 date-time")
    if result.tzinfo is None: fail(f"{label} must include a timezone")
    return result
def scan(value: object,path: str="$") -> None:
    if isinstance(value,dict):
        for key,child in value.items():
            normalized=str(key).lower().replace("-","_")
            if normalized in PROHIBITED_KEYS: fail(f"prohibited sensitive field: {path}.{key}")
            scan(child,f"{path}.{key}")
    elif isinstance(value,list):
        for i,child in enumerate(value): scan(child,f"{path}[{i}]")
def evidence_map(items: object) -> dict[str,dict]:
    if not isinstance(items,list): fail("evidence must be a list")
    out={}
    for item in items:
        if not isinstance(item,dict): fail("evidence entries must be objects")
        eid=item.get("id")
        if not isinstance(eid,str) or not eid: fail("evidence entries need non-empty ids")
        if eid in out: fail(f"duplicate evidence id: {eid}")
        parse_time(item.get("observed_at"),f"evidence {eid}.observed_at")
        url=item.get("public_url")
        if url is not None:
            parsed=urlparse(url)
            if parsed.scheme!="https" or not parsed.netloc: fail(f"evidence {eid}.public_url must be absolute https")
        out[eid]=item
    return out
def current_refs(refs: object,evidence: dict[str,dict],label: str,required: bool=False) -> None:
    if not isinstance(refs,list): fail(f"{label} must be a list")
    if required and not refs: fail(f"{label} requires current evidence")
    for ref in refs:
        if ref not in evidence: fail(f"{label} references unknown evidence: {ref}")
        if evidence[ref].get("status") != "current": fail(f"{label} must reference only current evidence")
def validate(record: dict) -> None:
    required={"schema_version","implementation_id","status","updated_at","commercial_handoff","environments","integrations","data_readiness","evals","rollout","adoption","go_live","hypercare","customer_success_handoff","economics","evidence","privacy"}
    missing=sorted(required-set(record))
    if missing: fail(f"missing required fields: {', '.join(missing)}")
    if record.get("schema_version")!="1.0.0": fail("schema_version must be 1.0.0")
    status=record.get("status")
    allowed={"sold","implementation_planning","configuring","validating","rollout_ready","live","hypercare","handed_to_customer_success","rolled_back"}
    if status not in allowed: fail("status is invalid")
    parse_time(record.get("updated_at"),"updated_at"); scan(record)
    if INDEX.exists():
        resources={x.get("id") for x in load(INDEX).get("resources",[]) if isinstance(x,dict)}
        for rid in record.get("repository_resources",[]):
            if rid not in resources: fail(f"unknown repository resource: {rid}")
    evidence=evidence_map(record.get("evidence"))
    privacy=record.get("privacy",{})
    for key in ("contains_credentials","contains_private_customer_data","contains_private_prompts"):
        if privacy.get(key) is not False: fail(f"privacy.{key} must be false")
    if privacy.get("public_disclosure_confirmed") is not True: fail("privacy.public_disclosure_confirmed must be true")
    handoff=record.get("commercial_handoff",{})
    if not isinstance(handoff,dict) or not handoff.get("accepted_scope") or not handoff.get("success_criteria"): fail("commercial handoff must preserve accepted scope and success criteria")
    current_refs(handoff.get("handoff_evidence_ids",[]),evidence,"commercial_handoff.handoff_evidence_ids",required=status!="implementation_planning")
    envs=record.get("environments")
    if not isinstance(envs,list) or not envs: fail("environments must be a non-empty list")
    prod=[e for e in envs if isinstance(e,dict) and e.get("production") is True]
    if len(prod)!=1: fail("exactly one production environment must be declared")
    for env in envs:
        if not isinstance(env,dict): fail("environment entries must be objects")
        current_refs(env.get("evidence_ids",[]),evidence,f"environment {env.get('name','?')} evidence")
    integrations=record.get("integrations")
    if not isinstance(integrations,list): fail("integrations must be a list")
    for integration in integrations:
        if not isinstance(integration,dict): fail("integration entries must be objects")
        if integration.get("status") in {"validated","production"}:
            if integration.get("failure_behavior_defined") is not True or integration.get("rate_limits_defined") is not True: fail("validated/production integrations require rate limits and failure behavior")
            current_refs(integration.get("evidence_ids",[]),evidence,f"integration {integration.get('id','?')} evidence",required=True)
    data=record.get("data_readiness",{}); evals=record.get("evals",{}); rollout=record.get("rollout",{}); adoption=record.get("adoption",{}); live=record.get("go_live",{}); hyper=record.get("hypercare",{}); cs=record.get("customer_success_handoff",{})
    for obj,label in ((data,"data_readiness"),(evals,"evals"),(rollout,"rollout"),(adoption,"adoption"),(live,"go_live"),(hyper,"hypercare"),(cs,"customer_success_handoff")):
        if not isinstance(obj,dict): fail(f"{label} must be an object")
    if status in PROD_STATUSES:
        for key in ("source_authority_resolved","minimum_necessary_defined","retention_defined","residency_resolved","deletion_path_defined","test_data_policy_defined"):
            if data.get(key) is not True: fail(f"production-capable status requires data_readiness.{key}=true")
        if data.get("customer_data_training_use")=="unknown": fail("production-capable status cannot have unknown customer-data training/use")
        for key in ("representative_set","regression_suite","safety_policy_cases","human_review_defined","acceptance_thresholds_defined","known_limitations_documented","production_monitoring_aligned","production_grade_passed"):
            if evals.get(key) is not True: fail(f"production-capable status requires evals.{key}=true")
        current_refs(evals.get("evidence_ids",[]),evidence,"evals.evidence_ids",required=True)
        if rollout.get("rollback_defined") is not True or rollout.get("kill_switch_defined") is not True or not rollout.get("rollback_triggers"): fail("production-capable status requires rollback, kill switch, and rollback triggers")
        if not isinstance(rollout.get("exposure_cap_percent"),int) or not 0 < rollout.get("exposure_cap_percent") <= 100: fail("production-capable status requires exposure cap between 1 and 100")
        for key in ("training_complete","communications_complete","sop_updates_complete","human_escalation_defined","adoption_metrics_defined"):
            if adoption.get(key) is not True: fail(f"production-capable status requires adoption.{key}=true")
    if live.get("approved") or status in {"live","hypercare","handed_to_customer_success"}:
        if live.get("requested") is not True or live.get("approved") is not True: fail("live status requires explicit requested and approved go-live state")
        if live.get("critical_blockers"): fail("go-live cannot proceed with unresolved critical blockers")
        for key in ("security_privacy_ready","reliability_ready","observability_ready","support_owner_defined"):
            if live.get(key) is not True: fail(f"go-live requires go_live.{key}=true")
        current_refs(live.get("customer_acceptance_evidence_ids",[]),evidence,"go_live.customer_acceptance_evidence_ids",required=True)
        current_refs(live.get("production_authority_evidence_ids",[]),evidence,"go_live.production_authority_evidence_ids",required=True)
        if prod[0].get("promotion_state")!="approved": fail("live status requires approved production promotion")
        current_refs(prod[0].get("evidence_ids",[]),evidence,"production environment evidence",required=True)
    if status=="hypercare":
        if hyper.get("active") is not True: fail("hypercare status requires hypercare.active=true")
        for key in ("incident_thresholds_defined","review_cadence_defined","customer_communications_defined","exit_criteria_defined"):
            if hyper.get(key) is not True: fail(f"hypercare requires hypercare.{key}=true")
    if status=="handed_to_customer_success" or cs.get("ready") is True:
        for key in ("ready","activation_baseline_defined","actual_permissions_recorded","support_escalation_map_defined","known_limitations_handed_off","first_value_milestone_defined"):
            if cs.get(key) is not True: fail(f"customer-success handoff requires {key}=true")
        current_refs(cs.get("evidence_ids",[]),evidence,"customer_success_handoff.evidence_ids",required=True)
        if status=="handed_to_customer_success" and hyper.get("active") is True: fail("cannot hand off while hypercare remains active")
    economics=record.get("economics",{})
    if not isinstance(economics,dict): fail("economics must be an object")
    for key in ("implementation_cost_minor","rework_cost_minor","delay_cost_minor","contracted_implementation_revenue_minor"):
        if not isinstance(economics.get(key),int) or economics.get(key)<0: fail(f"economics.{key} must be a non-negative integer")
    days=economics.get("time_to_live_days")
    if days is not None and (not isinstance(days,int) or days<0): fail("economics.time_to_live_days must be null or a non-negative integer")
def main() -> None:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("record",nargs="?",default="templates/CUSTOMER_IMPLEMENTATION_RECORD.json"); args=p.parse_args()
    path=(ROOT/args.record).resolve()
    if path!=ROOT and ROOT not in path.parents: fail("record path must stay inside repository")
    record=load(path); validate(record); print(f"customer implementation OK: {record['implementation_id']} status={record['status']} evidence={len(record['evidence'])}")
if __name__=="__main__": main()
