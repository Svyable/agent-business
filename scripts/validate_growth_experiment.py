#!/usr/bin/env python3
"""Validate Agent Business growth experiment records without third-party packages."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "agent-index.json"

ADVANCED = {"planned", "running", "analyzed", "scaled", "stopped", "retired"}
PAID_CHANNELS = {"paid_search", "paid_social", "display"}
OUTBOUND_CHANNELS = {"email", "sms", "dm"}
PROHIBITED_KEYS = {
    "password", "secret", "api_key", "access_token", "refresh_token", "authorization",
    "raw_contacts", "contact_list", "customer_list", "ad_account_credential", "raw_prompt"
}


def fail(message: str) -> None:
    raise SystemExit(f"growth-experiment validation failed: {message}")


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot parse {path}: {exc}")
    if not isinstance(value, dict):
        fail("record must be a JSON object")
    return value


def parse_time(value: object, label: str) -> datetime:
    if not isinstance(value, str):
        fail(f"{label} must be an ISO-8601 date-time")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        fail(f"{label} must be an ISO-8601 date-time")
    if result.tzinfo is None:
        fail(f"{label} must include a timezone")
    return result


def scan(value: object, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in PROHIBITED_KEYS:
                fail(f"prohibited sensitive field: {path}.{key}")
            scan(child, f"{path}.{key}")
    elif isinstance(value, list):
        for i, child in enumerate(value):
            scan(child, f"{path}[{i}]")


def unique_evidence(items: object) -> dict[str, dict]:
    if not isinstance(items, list):
        fail("evidence must be a list")
    result: dict[str, dict] = {}
    for item in items:
        if not isinstance(item, dict):
            fail("evidence entries must be objects")
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            fail("evidence entries need non-empty ids")
        if item_id in result:
            fail(f"duplicate evidence id: {item_id}")
        parse_time(item.get("observed_at"), f"evidence {item_id}.observed_at")
        url = item.get("public_url")
        if url is not None:
            parsed = urlparse(url)
            if parsed.scheme != "https" or not parsed.netloc:
                fail(f"evidence {item_id}.public_url must be absolute https")
        result[item_id] = item
    return result


def validate(record: dict) -> None:
    required = {"schema_version","experiment_id","status","updated_at","hypothesis","audience","channel","metrics","budget","attribution","authority","evidence","decision","privacy"}
    missing = sorted(required - set(record))
    if missing:
        fail(f"missing required fields: {', '.join(missing)}")
    if record.get("schema_version") != "1.0.0":
        fail("schema_version must be 1.0.0")
    status = record.get("status")
    if status not in {"draft","planned","running","analyzed","scaled","stopped","retired"}:
        fail("status is invalid")
    parse_time(record.get("updated_at"), "updated_at")
    scan(record)

    resources = {item.get("id") for item in load(INDEX).get("resources", []) if isinstance(item, dict)}
    for resource_id in record.get("repository_resources", []):
        if resource_id not in resources:
            fail(f"unknown repository resource: {resource_id}")

    evidence = unique_evidence(record.get("evidence"))
    current = {key for key, item in evidence.items() if item.get("status") == "current"}

    audience = record.get("audience")
    channel = record.get("channel")
    metrics = record.get("metrics")
    budget = record.get("budget")
    attribution = record.get("attribution")
    authority = record.get("authority")
    decision = record.get("decision")
    privacy = record.get("privacy")
    if not all(isinstance(x, dict) for x in (audience, channel, metrics, budget, attribution, authority, decision, privacy)):
        fail("audience/channel/metrics/budget/attribution/authority/decision/privacy must be objects")

    for field in ("contains_raw_contacts", "contains_credentials", "contains_private_customer_data"):
        if privacy.get(field) is not False:
            fail(f"privacy.{field} must be false")
    if privacy.get("public_disclosure_confirmed") is not True:
        fail("privacy.public_disclosure_confirmed must be true")

    spend = metrics.get("spend_minor")
    daily_cap = budget.get("daily_cap_minor")
    lifetime_cap = budget.get("lifetime_cap_minor")
    stop_loss = budget.get("stop_loss_minor")
    max_spend = authority.get("max_spend_minor")
    for label, value in (("metrics.spend_minor", spend), ("budget.daily_cap_minor", daily_cap), ("budget.lifetime_cap_minor", lifetime_cap), ("budget.stop_loss_minor", stop_loss), ("authority.max_spend_minor", max_spend)):
        if not isinstance(value, int) or value < 0:
            fail(f"{label} must be a non-negative integer")
    if daily_cap > lifetime_cap and lifetime_cap > 0:
        fail("daily budget cap cannot exceed lifetime cap")
    if stop_loss > lifetime_cap and lifetime_cap > 0:
        fail("stop-loss cannot exceed lifetime cap")
    if spend > lifetime_cap:
        fail("recorded spend exceeds lifetime cap")
    if authority.get("can_spend") and max_spend < lifetime_cap:
        fail("spend authority must cover the configured lifetime cap")
    if not authority.get("can_spend") and spend > 0:
        fail("nonzero spend requires spend authority")

    refs = authority.get("authority_evidence_ids", [])
    if any(ref not in current for ref in refs):
        fail("authority must reference only current evidence")
    material_authority = any(authority.get(key) for key in ("can_publish","can_spend","can_reallocate_budget","can_change_audience","can_change_claims"))
    if material_authority and not refs:
        fail("material marketing authority requires current authority evidence")

    if status in ADVANCED:
        if audience.get("customer_data_use") == "unknown":
            fail(f"{status} records cannot have unknown customer-data use")
        if channel.get("claims_reviewed") is not True or channel.get("brand_assets_authorized") is not True:
            fail(f"{status} records require reviewed claims and authorized brand assets")
        if not evidence:
            fail(f"{status} records require evidence")

    if channel.get("type") in OUTBOUND_CHANNELS:
        if audience.get("consent_basis") == "unknown" or audience.get("suppression_enforced") is not True:
            fail("outbound channels require resolved consent basis and suppression enforcement")

    if channel.get("type") in PAID_CHANNELS and status in {"planned","running","scaled"}:
        if lifetime_cap <= 0 or not authority.get("can_spend"):
            fail("active paid media requires a positive lifetime cap and spend authority")

    observed = metrics.get("observed_revenue_minor")
    attributed = metrics.get("platform_attributed_revenue_minor")
    if not isinstance(observed, int) or observed < 0 or not isinstance(attributed, int) or attributed < 0:
        fail("revenue metrics must be non-negative integers")
    if observed > 0 and not any(item.get("type") in {"crm_event","buyer_event","public_artifact"} and item.get("status") == "current" for item in evidence.values()):
        fail("observed revenue requires current CRM/buyer/public evidence")
    if attributed > 0 and not any(item.get("type") == "platform_report" and item.get("status") == "current" for item in evidence.values()):
        fail("platform-attributed revenue requires a current platform report")

    causal = attribution.get("causal_claim")
    method = attribution.get("incrementality_method")
    if causal and method not in {"randomized_holdout","geo_holdout","matched_control"}:
        fail("causal claims require a holdout/control incrementality method")
    if causal and not any(item.get("type") == "experiment_output" and item.get("status") == "current" for item in evidence.values()):
        fail("causal claims require current experiment-output evidence")

    action = decision.get("action")
    decision_refs = decision.get("evidence_ids", [])
    unknown = [ref for ref in decision_refs if ref not in evidence]
    if unknown:
        fail(f"decision references unknown evidence: {', '.join(unknown)}")
    if action in {"launch","continue","scale","stop","retire"} and not decision_refs:
        fail(f"decision action {action} requires evidence")
    if action == "scale":
        if status not in {"analyzed","scaled"}:
            fail("scale decision requires analyzed or scaled status")
        if any(ref not in current for ref in decision_refs):
            fail("scale decision must use current evidence")
        if spend >= stop_loss and stop_loss > 0 and metrics.get("qualified_opportunities", 0) == 0:
            fail("cannot scale after reaching stop-loss with zero qualified opportunities")
        if channel.get("type") in PAID_CHANNELS and not authority.get("can_reallocate_budget"):
            fail("paid-media scale decision requires budget-reallocation authority")

    opportunities = metrics.get("qualified_opportunities")
    ids = metrics.get("revenue_opportunity_ids", [])
    if isinstance(opportunities, int) and opportunities > 0 and len(ids) > opportunities:
        fail("revenue_opportunity_ids cannot exceed qualified opportunity count")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", nargs="?", default="templates/GROWTH_EXPERIMENT_RECORD.json")
    args = parser.parse_args()
    path = (ROOT / args.record).resolve()
    if path != ROOT and ROOT not in path.parents:
        fail("record path must stay inside repository")
    record = load(path)
    validate(record)
    print(f"growth experiment OK: {record['experiment_id']} status={record['status']} evidence={len(record['evidence'])}")


if __name__ == "__main__":
    main()
