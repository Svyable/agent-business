#!/usr/bin/env python3
"""Validate Agent Business marketplace listing records with only the standard library."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = {
    "schema_version", "listing_id", "listing_version", "updated_at", "status",
    "provider", "capability", "pricing", "payment_options", "buyer_qualification",
    "claims", "evidence", "marketplaces", "conversion", "privacy",
}
STATUSES = {"draft", "evidence_reviewed", "published", "suspended", "retired"}
CLAIM_CLASSES = {"self_asserted", "platform_verified", "customer_signal", "benchmark_evidence", "editorial_interpretation"}
EVIDENCE_STATES = {"current", "stale", "disputed", "superseded"}
PROHIBITED_KEYS = {
    "password", "secret", "client_secret", "api_key", "access_token", "refresh_token",
    "authorization", "raw_prompt", "prompt_content", "card_number", "cvv",
    "private_key", "seed_phrase", "bearer_token",
}
PLACEHOLDERS = (
    "replace before publication", "replace-before-publication", "replace with",
    "replace.capability", "replace-category", "replace-input", "replace-output",
    "example.invalid", "unknown-until-reviewed", "draft only",
)
REQUIRED_FUNNEL = {
    "listing_discovered", "capability_inspected", "buyer_qualified",
    "quote_or_checkout_started", "paid_transaction", "successful_delivery", "repeat_purchase",
}


def fail(message: str) -> None:
    raise SystemExit(f"marketplace-listing validation failed: {message}")


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot parse {path}: {exc}")
    if not isinstance(value, dict):
        fail("listing must be a JSON object")
    return value


def parse_time(value: object, label: str) -> datetime:
    if not isinstance(value, str):
        fail(f"{label} must be an ISO-8601 date-time")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        fail(f"{label} must be an ISO-8601 date-time")
    if parsed.tzinfo is None:
        fail(f"{label} must include a timezone")
    return parsed


def https_url(value: object, label: str, *, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if not isinstance(value, str):
        fail(f"{label} must be an https URL")
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        fail(f"{label} must use an absolute https URL")


def scan_prohibited(value: object, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in PROHIBITED_KEYS:
                fail(f"prohibited sensitive field: {path}.{key}")
            scan_prohibited(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_prohibited(child, f"{path}[{index}]")


def contains_placeholder(record: dict) -> str | None:
    text = json.dumps(record, sort_keys=True).lower()
    for marker in PLACEHOLDERS:
        if marker in text:
            return marker
    return None


def unique_by_id(items: object, label: str) -> dict[str, dict]:
    if not isinstance(items, list):
        fail(f"{label} must be a list")
    result: dict[str, dict] = {}
    for item in items:
        if not isinstance(item, dict):
            fail(f"{label} entries must be objects")
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            fail(f"{label} entries require non-empty id")
        if item_id in result:
            fail(f"duplicate {label} id: {item_id}")
        result[item_id] = item
    return result


def unique_marketplaces(items: object) -> dict[str, dict]:
    if not isinstance(items, list):
        fail("marketplaces must be a list")
    result: dict[str, dict] = {}
    for item in items:
        if not isinstance(item, dict):
            fail("marketplace entries must be objects")
        marketplace_id = item.get("marketplace_id")
        if not isinstance(marketplace_id, str) or not marketplace_id:
            fail("marketplace entries require marketplace_id")
        if marketplace_id in result:
            fail(f"duplicate marketplace_id: {marketplace_id}")
        result[marketplace_id] = item
    return result


def evidence_is_current(item: dict, as_of: datetime) -> bool:
    observed = parse_time(item.get("observed_at"), f"evidence {item.get('id')}.observed_at")
    if observed > as_of:
        fail(f"evidence {item.get('id')} is observed after listing updated_at")
    if item.get("status") != "current":
        return False
    expires_raw = item.get("expires_at")
    if expires_raw is not None and parse_time(expires_raw, f"evidence {item.get('id')}.expires_at") < as_of:
        return False
    return True


def check_refs(refs: object, evidence: dict[str, dict], label: str) -> list[str]:
    if not isinstance(refs, list) or any(not isinstance(ref, str) or not ref for ref in refs):
        fail(f"{label}.evidence_ids must be a list of non-empty ids")
    unknown = sorted(set(refs) - set(evidence))
    if unknown:
        fail(f"{label} references unknown evidence: {', '.join(unknown)}")
    return refs


def require_current(refs: list[str], current: set[str], label: str) -> None:
    stale = sorted(set(refs) - current)
    if stale:
        fail(f"{label} references non-current evidence: {', '.join(stale)}")


def validate(record: dict, *, allow_draft: bool = False) -> None:
    missing = sorted(REQUIRED - set(record))
    if missing:
        fail(f"missing required fields: {', '.join(missing)}")
    if record.get("schema_version") != "1.0.0":
        fail("schema_version must be 1.0.0")
    status = record.get("status")
    if status not in STATUSES:
        fail("status is invalid")
    if status == "draft" and not allow_draft:
        fail("draft listings require --allow-draft")

    as_of = parse_time(record.get("updated_at"), "updated_at")
    scan_prohibited(record)

    provider = record.get("provider")
    if not isinstance(provider, dict):
        fail("provider must be an object")
    for field in ("display_name", "identity_ref"):
        if not isinstance(provider.get(field), str) or not provider[field].strip():
            fail(f"provider.{field} is required")
    https_url(provider.get("canonical_url"), "provider.canonical_url")

    capability = record.get("capability")
    if not isinstance(capability, dict):
        fail("capability must be an object")
    for field in ("capability_id", "name", "summary"):
        if not isinstance(capability.get(field), str) or not capability[field].strip():
            fail(f"capability.{field} is required")
    for field in ("categories", "inputs", "outputs", "regions"):
        value = capability.get(field)
        if not isinstance(value, list) or not value:
            fail(f"capability.{field} must be a non-empty list")
    for field in ("synonyms", "dependencies", "compliance_constraints"):
        if not isinstance(capability.get(field), list):
            fail(f"capability.{field} must be a list")

    service_levels = capability.get("service_levels")
    if not isinstance(service_levels, dict):
        fail("capability.service_levels must be an object")
    service_fields = ("availability_target", "p95_latency_seconds", "completion_deadline_seconds", "support_window")
    for field in service_fields:
        if field not in service_levels:
            fail(f"capability.service_levels.{field} is required")
    if status == "published" and all(service_levels.get(field) is None for field in service_fields):
        fail("published listing requires at least one explicit service-level value")
    availability = service_levels.get("availability_target")
    if availability is not None and (isinstance(availability, bool) or not isinstance(availability, (int, float)) or not 0 <= availability <= 1):
        fail("capability.service_levels.availability_target must be between 0 and 1")
    for field in ("p95_latency_seconds", "completion_deadline_seconds"):
        value = service_levels.get(field)
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0):
            fail(f"capability.service_levels.{field} must be a non-negative number or null")
    support_window = service_levels.get("support_window")
    if support_window is not None and (not isinstance(support_window, str) or not support_window.strip()):
        fail("capability.service_levels.support_window must be a non-empty string or null")

    evidence = unique_by_id(record.get("evidence"), "evidence")
    current_evidence: set[str] = set()
    for evidence_id, item in evidence.items():
        if item.get("status") not in EVIDENCE_STATES:
            fail(f"evidence {evidence_id} has invalid status")
        https_url(item.get("public_url"), f"evidence {evidence_id}.public_url", nullable=True)
        if evidence_is_current(item, as_of):
            current_evidence.add(evidence_id)

    protocols = unique_by_id(capability.get("protocols"), "protocol")
    if not protocols:
        fail("capability.protocols must contain at least one protocol")
    for protocol_id, item in protocols.items():
        https_url(item.get("endpoint"), f"protocol {protocol_id}.endpoint")
        refs = check_refs(item.get("evidence_ids"), evidence, f"protocol {protocol_id}")
        if status == "published":
            if not refs:
                fail(f"published protocol {protocol_id} requires evidence")
            require_current(refs, current_evidence, f"published protocol {protocol_id}")

    pricing = record.get("pricing")
    if not isinstance(pricing, dict):
        fail("pricing must be an object")
    model = pricing.get("model")
    if model not in {"undecided", "free", "fixed", "usage", "subscription", "outcome", "quote", "hybrid"}:
        fail("pricing.model is invalid")
    if pricing.get("terms_url") is not None:
        https_url(pricing.get("terms_url"), "pricing.terms_url")
    if status == "published":
        if model == "undecided":
            fail("published listing cannot have undecided pricing")
        if not isinstance(pricing.get("headline"), str) or not pricing["headline"].strip():
            fail("published listing requires pricing.headline")
        if model != "free":
            currency = pricing.get("currency")
            if not isinstance(currency, str) or len(currency) != 3 or currency.upper() != currency:
                fail("published paid listing requires three-letter uppercase pricing.currency")
        if pricing.get("minimum_commitment_minor") is None:
            fail("published listing requires pricing.minimum_commitment_minor, including zero")

    payment_options = unique_by_id(record.get("payment_options"), "payment option")
    for option_id, item in payment_options.items():
        for field in ("rail", "asset_or_currency", "settlement_semantics"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                fail(f"payment option {option_id}.{field} is required")
        refs = check_refs(item.get("evidence_ids"), evidence, f"payment option {option_id}")
        if not refs:
            fail(f"payment option {option_id} requires evidence_ids")
        if not any(evidence[ref].get("type") == "payment_capability" for ref in refs):
            fail(f"payment option {option_id} requires payment_capability evidence")
        if status == "published":
            require_current(refs, current_evidence, f"published payment option {option_id}")

    buyer = record.get("buyer_qualification")
    if not isinstance(buyer, dict):
        fail("buyer_qualification must be an object")
    if buyer.get("automatic_purchase_allowed") is True:
        if buyer.get("requires_authority_proof") is not True:
            fail("automatic purchase requires buyer authority proof")
        if buyer.get("acceptance_criteria_required") is not True:
            fail("automatic purchase requires acceptance criteria")
        cap = buyer.get("max_autonomous_purchase_minor")
        if not isinstance(cap, int) or isinstance(cap, bool) or cap <= 0:
            fail("automatic purchase requires a positive max_autonomous_purchase_minor")
        if status == "published" and model != "free" and not payment_options:
            fail("published paid automatic purchase requires at least one evidenced payment option")
    if status == "published" and not isinstance(buyer.get("data_constraints"), list):
        fail("published listing requires explicit buyer data_constraints")

    marketplaces = unique_marketplaces(record.get("marketplaces"))
    for marketplace_id, item in marketplaces.items():
        listing_url = item.get("listing_url")
        if listing_url is not None:
            https_url(listing_url, f"marketplace {marketplace_id}.listing_url")
        synced_raw = item.get("synced_at")
        synced = parse_time(synced_raw, f"marketplace {marketplace_id}.synced_at") if synced_raw is not None else None
        if item.get("state") == "published":
            if listing_url is None or synced is None:
                fail(f"published marketplace {marketplace_id} requires listing_url and synced_at")
            if item.get("projected_listing_version") != record.get("listing_version"):
                fail(f"published marketplace {marketplace_id} has stale projected_listing_version")
            if synced < as_of:
                fail(f"published marketplace {marketplace_id} was synced before canonical updated_at")
        badges = item.get("badges")
        if not isinstance(badges, list):
            fail(f"marketplace {marketplace_id}.badges must be a list")
        for badge in badges:
            if not isinstance(badge, dict):
                fail(f"marketplace {marketplace_id} badge must be an object")
            scope = badge.get("scope")
            if not isinstance(scope, str) or not scope.strip():
                fail(f"marketplace {marketplace_id} badge requires a non-empty scope")
            refs = check_refs(badge.get("evidence_ids"), evidence, f"marketplace {marketplace_id} badge")
            if not refs:
                fail(f"marketplace {marketplace_id} badge requires evidence_ids")
            for ref in refs:
                evidence_item = evidence[ref]
                if evidence_item.get("type") != "platform_verification":
                    fail(f"marketplace {marketplace_id} badge must use platform_verification evidence")
                if evidence_item.get("marketplace_id") != marketplace_id:
                    fail(f"marketplace {marketplace_id} badge evidence is not scoped to that marketplace")
                if status == "published" and ref not in current_evidence:
                    fail(f"marketplace {marketplace_id} badge uses non-current evidence")

    claims = unique_by_id(record.get("claims"), "claim")
    if not claims:
        fail("claims must contain at least one claim")
    for claim_id, item in claims.items():
        classification = item.get("classification")
        if classification not in CLAIM_CLASSES:
            fail(f"claim {claim_id} has invalid classification")
        refs = check_refs(item.get("evidence_ids"), evidence, f"claim {claim_id}")
        expires_raw = item.get("expires_at")
        if expires_raw is not None and parse_time(expires_raw, f"claim {claim_id}.expires_at") < as_of and status == "published":
            fail(f"published claim {claim_id} is expired")
        marketplace_id = item.get("marketplace_id")
        if classification == "platform_verified":
            if not isinstance(marketplace_id, str) or marketplace_id not in marketplaces:
                fail(f"platform_verified claim {claim_id} requires a known marketplace_id")
            if not refs:
                fail(f"platform_verified claim {claim_id} requires evidence")
            for ref in refs:
                evidence_item = evidence[ref]
                if evidence_item.get("type") != "platform_verification" or evidence_item.get("marketplace_id") != marketplace_id:
                    fail(f"platform_verified claim {claim_id} evidence must be scoped to {marketplace_id}")
        elif marketplace_id is not None and marketplace_id not in marketplaces:
            fail(f"claim {claim_id} references unknown marketplace_id")
        if status == "published" and classification != "editorial_interpretation":
            if not refs:
                fail(f"published non-editorial claim {claim_id} requires evidence")
            require_current(refs, current_evidence, f"published claim {claim_id}")

    conversion = record.get("conversion")
    if not isinstance(conversion, dict) or not isinstance(conversion.get("events"), list):
        fail("conversion.events must be a list")
    if status == "published" and not REQUIRED_FUNNEL.issubset(set(conversion["events"])):
        missing_events = sorted(REQUIRED_FUNNEL - set(conversion["events"]))
        fail(f"published listing is missing conversion events: {', '.join(missing_events)}")

    privacy = record.get("privacy")
    if not isinstance(privacy, dict):
        fail("privacy must be an object")
    if privacy.get("public_disclosure_confirmed") is not True:
        fail("privacy.public_disclosure_confirmed must be true")
    for field in ("contains_secrets", "contains_private_customer_data", "contains_private_prompts", "contains_credentials"):
        if privacy.get(field) is not False:
            fail(f"privacy.{field} must be false")

    if status in {"evidence_reviewed", "published"}:
        marker = contains_placeholder(record)
        if marker:
            fail(f"listing still contains placeholder text: {marker!r}")
        if not current_evidence:
            fail(f"{status} listing requires current evidence")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", nargs="?", default="templates/AGENT_MARKETPLACE_LISTING.json")
    parser.add_argument("--allow-draft", action="store_true", help="allow the safe draft starter")
    args = parser.parse_args()
    path = (ROOT / args.record).resolve()
    if path != ROOT and ROOT not in path.parents:
        fail("record path must stay inside the repository")
    record = load_json(path)
    validate(record, allow_draft=args.allow_draft)
    print(
        "marketplace listing OK: "
        f"{record['listing_id']} version={record['listing_version']} status={record['status']} "
        f"protocols={len(record['capability']['protocols'])} payment_options={len(record['payment_options'])} "
        f"marketplaces={len(record['marketplaces'])} claims={len(record['claims'])} evidence={len(record['evidence'])}"
    )


if __name__ == "__main__":
    main()
