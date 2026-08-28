#!/usr/bin/env python3
"""Validate Agent Business pricing/package records without third-party packages."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OPERATIONAL = {"quote_ready", "active"}
OUTCOME_MODELS = {"outcome"}
PROHIBITED_KEYS = {
    "password", "secret", "api_key", "access_token", "refresh_token",
    "authorization", "card_number", "cvv", "payment_credential", "raw_prompt"
}
PLACEHOLDERS = ("replace with", "placeholder", "example segment", "draft pricing")


def fail(message: str) -> None:
    raise SystemExit(f"pricing-package validation failed: {message}")


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


def scan_sensitive(value: object, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in PROHIBITED_KEYS:
                fail(f"prohibited sensitive field: {path}.{key}")
            scan_sensitive(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_sensitive(child, f"{path}[{index}]")


def evidence_map(items: object) -> dict[str, dict]:
    if not isinstance(items, list):
        fail("evidence must be a list")
    result: dict[str, dict] = {}
    for item in items:
        if not isinstance(item, dict):
            fail("evidence entries must be objects")
        evidence_id = item.get("id")
        if not isinstance(evidence_id, str) or not evidence_id:
            fail("evidence entries require ids")
        if evidence_id in result:
            fail(f"duplicate evidence id: {evidence_id}")
        if item.get("status") not in {"current", "stale", "disputed", "draft"}:
            fail(f"evidence {evidence_id} has invalid status")
        parse_time(item.get("observed_at"), f"evidence {evidence_id}.observed_at")
        url = item.get("public_url")
        if url is not None:
            if not isinstance(url, str) or urlparse(url).scheme != "https" or not urlparse(url).netloc:
                fail(f"evidence {evidence_id}.public_url must be an absolute https URL")
        result[evidence_id] = item
    return result


def require_current_refs(refs: object, evidence: dict[str, dict], label: str) -> None:
    if not isinstance(refs, list) or not refs:
        fail(f"{label} requires at least one evidence reference")
    for ref in refs:
        if ref not in evidence:
            fail(f"{label} references unknown evidence: {ref!r}")
        if evidence[ref].get("status") != "current":
            fail(f"{label} references non-current evidence: {ref}")


def validate(record: dict) -> None:
    required = {
        "schema_version", "package_id", "updated_at", "status", "currency",
        "pricing_model", "customer_segment", "meter", "commercial_terms",
        "economics", "budget_controls", "authority", "evidence", "privacy"
    }
    missing = sorted(required - set(record))
    if missing:
        fail(f"missing required fields: {', '.join(missing)}")
    if record.get("schema_version") != "1.0.0":
        fail("schema_version must be 1.0.0")
    if record.get("status") not in {"draft", "needs_review", "quote_ready", "active", "retired"}:
        fail("status is invalid")
    scan_sensitive(record)
    updated = parse_time(record.get("updated_at"), "updated_at")
    evidence = evidence_map(record.get("evidence"))

    meter = record.get("meter")
    if not isinstance(meter, dict):
        fail("meter must be an object")
    definition = meter.get("definition")
    if not isinstance(definition, str) or len(definition.strip()) < 20:
        fail("meter.definition must unambiguously describe the billable event")
    if not isinstance(meter.get("deduplication_key"), str) or not meter["deduplication_key"].strip():
        fail("meter.deduplication_key is required to prevent retry double-billing")
    if record["status"] in OPERATIONAL and meter.get("customer_verifiable") is not True:
        fail("operational packages require a customer-verifiable meter")
    exclusions = meter.get("exclusions")
    if not isinstance(exclusions, list):
        fail("meter.exclusions must be a list")
    if record["status"] in OPERATIONAL:
        normalized = " ".join(str(item).lower() for item in exclusions)
        if "retr" not in normalized or "duplicate" not in normalized:
            fail("operational meter exclusions must address retries and duplicates")

    model = record.get("pricing_model")
    trigger = meter.get("trigger")
    outcome_policy = record.get("outcome_policy")
    if model in OUTCOME_MODELS or trigger == "verified_outcome":
        if not isinstance(outcome_policy, dict):
            fail("outcome pricing requires outcome_policy")
        for field in ("success_definition", "attribution_rule"):
            if not isinstance(outcome_policy.get(field), str) or len(outcome_policy[field].strip()) < 20:
                fail(f"outcome_policy.{field} must be explicit")
        if record["status"] in OPERATIONAL:
            require_current_refs(outcome_policy.get("evidence_ids"), evidence, "outcome_policy")

    terms = record.get("commercial_terms")
    if not isinstance(terms, dict):
        fail("commercial_terms must be an object")
    effective_from = parse_time(terms.get("effective_from"), "commercial_terms.effective_from")
    quote_expires = parse_time(terms.get("quote_expires_at"), "commercial_terms.quote_expires_at")
    effective_until = terms.get("effective_until")
    if effective_until is not None and parse_time(effective_until, "commercial_terms.effective_until") <= effective_from:
        fail("effective_until must be after effective_from")
    if record["status"] == "quote_ready" and quote_expires <= updated:
        fail("quote_ready package cannot have an expired quote")
    if record["status"] == "active" and effective_until is not None and parse_time(effective_until, "commercial_terms.effective_until") <= updated:
        fail("active package cannot be past effective_until")
    if terms.get("overage_price_minor") is not None and terms.get("hard_spend_cap_minor") is None:
        controls = record.get("budget_controls", {})
        if controls.get("overage_requires_approval") is not True:
            fail("uncapped overages require explicit approval controls")

    economics = record.get("economics")
    if not isinstance(economics, dict):
        fail("economics must be an object")
    cost = economics.get("expected_cost_per_billable_unit_minor")
    price = economics.get("expected_net_price_per_unit_minor")
    floor = economics.get("minimum_contribution_margin_bps")
    target = economics.get("target_contribution_margin_bps")
    if not all(isinstance(v, int) for v in (cost, price, floor, target)):
        fail("economics cost, net price, target margin, and floor must be integers")
    if target < floor:
        fail("target contribution margin cannot be below the minimum margin floor")
    if record["status"] in OPERATIONAL:
        if price <= 0:
            fail("operational packages require positive expected net price per billable unit")
        actual_margin_bps = round((price - cost) * 10000 / price)
        if actual_margin_bps < floor:
            fail(f"expected contribution margin {actual_margin_bps} bps is below floor {floor} bps")
        require_current_refs(economics.get("evidence_ids"), evidence, "economics")

    controls = record.get("budget_controls")
    if not isinstance(controls, dict):
        fail("budget_controls must be an object")
    if record["status"] in OPERATIONAL:
        if controls.get("no_surprise_billing") is not True:
            fail("operational packages require no_surprise_billing=true")
        cap = terms.get("hard_spend_cap_minor")
        alerts = controls.get("usage_alert_percentages")
        if cap is None and (not isinstance(alerts, list) or not alerts):
            fail("operational packages need a hard spend cap or usage alerts")
        if controls.get("hard_cap_behavior") == "not_configured" and cap is not None:
            fail("hard spend cap requires configured enforcement behavior")

    authority = record.get("authority")
    if not isinstance(authority, dict):
        fail("authority must be an object")
    discount = terms.get("discount_bps")
    service_credit = terms.get("service_credit_cap_minor")
    if not isinstance(discount, int) or not isinstance(service_credit, int):
        fail("discount and service-credit cap must be integers")
    if discount > authority.get("max_discount_bps", -1):
        fail("discount exceeds deal-desk authority")
    if service_credit > 0:
        if authority.get("can_grant_credits") is not True:
            fail("service credits require credit authority")
        if service_credit > authority.get("max_credit_minor", -1):
            fail("service credit cap exceeds authority")
    if record["status"] in OPERATIONAL:
        if authority.get("can_issue_quote") is not True:
            fail("operational package requires quote authority")
        if not isinstance(authority.get("source"), str) or not authority["source"].strip():
            fail("operational package requires authority provenance")
        reviewed = parse_time(authority.get("reviewed_at"), "authority.reviewed_at")
        if reviewed > updated:
            fail("authority.reviewed_at cannot be after record.updated_at")

    privacy = record.get("privacy")
    if not isinstance(privacy, dict):
        fail("privacy must be an object")
    for field in ("contains_secrets", "contains_payment_credentials", "contains_private_customer_data"):
        if privacy.get(field) is not False:
            fail(f"privacy.{field} must be false")

    if record["status"] in OPERATIONAL:
        text = json.dumps(record, sort_keys=True).lower()
        for marker in PLACEHOLDERS:
            if marker in text:
                fail(f"operational package contains placeholder text: {marker!r}")
        if not evidence:
            fail("operational packages require evidence")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", nargs="?", default="templates/PRICING_PACKAGE.json")
    args = parser.parse_args()
    path = (ROOT / args.record).resolve()
    if path != ROOT and ROOT not in path.parents:
        fail("record path must stay inside repository")
    record = load(path)
    validate(record)
    print(
        f"pricing package OK: {record['package_id']} status={record['status']} "
        f"model={record['pricing_model']} evidence={len(record['evidence'])}"
    )


if __name__ == "__main__":
    main()
