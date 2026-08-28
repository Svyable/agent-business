#!/usr/bin/env python3
"""Validate Agent Business IP/model/data-rights records without third-party packages."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]

PROHIBITED_KEYS = {
    "password",
    "secret",
    "api_key",
    "access_token",
    "refresh_token",
    "authorization",
    "private_key",
    "raw_prompt",
    "prompt_content",
    "contract_text",
    "customer_content",
    "dataset_content",
    "license_text",
}


def fail(message: str) -> None:
    raise SystemExit(f"ip-rights validation failed: {message}")


def load_json(path: Path) -> dict:
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
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        fail(f"{label} must be an ISO-8601 date-time")
    if parsed.tzinfo is None:
        fail(f"{label} must include a timezone")
    return parsed


def scan_sensitive(value: object, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in PROHIBITED_KEYS:
                fail(f"prohibited sensitive/content field: {path}.{key}")
            scan_sensitive(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_sensitive(child, f"{path}[{index}]")


def unique_ids(items: object, label: str) -> dict[str, dict]:
    if not isinstance(items, list):
        fail(f"{label} must be a list")
    result: dict[str, dict] = {}
    for item in items:
        if not isinstance(item, dict):
            fail(f"{label} entries must be objects")
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            fail(f"{label} entries need non-empty ids")
        if item_id in result:
            fail(f"duplicate {label} id: {item_id}")
        result[item_id] = item
    return result


def validate_public_url(value: object, label: str) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        fail(f"{label} must be a string or null")
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        fail(f"{label} must use an absolute https URL")


def require_refs(refs: object, evidence: dict[str, dict], label: str, *, current: bool = False) -> None:
    if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
        fail(f"{label}.evidence_ids must be a list of ids")
    unknown = sorted(set(refs) - set(evidence))
    if unknown:
        fail(f"{label} references unknown evidence: {', '.join(unknown)}")
    if current:
        if not refs:
            fail(f"{label} requires evidence")
        stale = [ref for ref in refs if evidence[ref].get("status") != "current"]
        if stale:
            fail(f"{label} references non-current evidence: {', '.join(stale)}")


def validate(record: dict) -> None:
    if record.get("schema_version") != "1.0.0":
        fail("schema_version must be 1.0.0")
    status = record.get("status")
    if status not in {"draft", "needs_review", "commercial_ready", "blocked", "retired"}:
        fail("status is invalid")
    parse_time(record.get("updated_at"), "updated_at")
    scan_sensitive(record)

    intended = record.get("intended_use")
    if not isinstance(intended, dict):
        fail("intended_use must be an object")
    for field in ("commercial", "redistribution", "training_or_finetuning", "customer_deliverable"):
        if not isinstance(intended.get(field), bool):
            fail(f"intended_use.{field} must be boolean")

    privacy = record.get("privacy")
    if not isinstance(privacy, dict) or privacy.get("public_safe") is not True:
        fail("privacy.public_safe must be true")
    for field in (
        "contains_secret",
        "contains_private_contract_text",
        "contains_private_customer_content",
        "contains_restricted_dataset_content",
        "contains_private_prompt",
    ):
        if privacy.get(field) is not False:
            fail(f"privacy.{field} must be false")

    evidence = unique_ids(record.get("evidence"), "evidence")
    now = datetime.now(timezone.utc)
    for evidence_id, item in evidence.items():
        observed = parse_time(item.get("observed_at"), f"evidence {evidence_id}.observed_at")
        if observed > now:
            fail(f"evidence {evidence_id} cannot be observed in the future")
        expires_raw = item.get("expires_at")
        if expires_raw is not None:
            expires = parse_time(expires_raw, f"evidence {evidence_id}.expires_at")
            if expires < observed:
                fail(f"evidence {evidence_id}.expires_at cannot precede observed_at")
            if expires <= now and item.get("status") == "current":
                fail(f"evidence {evidence_id} is expired but marked current")
        validate_public_url(item.get("public_url"), f"evidence {evidence_id}.public_url")

    assets = unique_ids(record.get("assets"), "asset")
    if not assets:
        fail("assets must contain at least one item")
    for asset_id, asset in assets.items():
        require_refs(asset.get("evidence_ids"), evidence, f"asset {asset_id}", current=status == "commercial_ready")
        rights = asset.get("rights_status")
        if rights not in {"owned", "licensed", "public_domain", "permissioned", "unknown", "incompatible", "expired"}:
            fail(f"asset {asset_id} has invalid rights_status")
        if asset.get("attribution_required") == "yes" and not asset.get("attribution_text_reference"):
            fail(f"asset {asset_id} requires an attribution reference")
        effective_raw = asset.get("effective_at")
        expires_raw = asset.get("expires_at")
        if effective_raw is not None:
            effective = parse_time(effective_raw, f"asset {asset_id}.effective_at")
            if expires_raw is not None:
                expires = parse_time(expires_raw, f"asset {asset_id}.expires_at")
                if expires < effective:
                    fail(f"asset {asset_id}.expires_at cannot precede effective_at")
                if expires <= now and rights not in {"expired", "unknown"}:
                    fail(f"asset {asset_id} rights expired but rights_status is {rights}")
        if rights in {"licensed", "permissioned"} and status == "commercial_ready":
            if not asset.get("terms_version") or not effective_raw:
                fail(f"commercial-ready asset {asset_id} needs terms_version and effective_at")
        if status == "commercial_ready" and asset.get("conflicts"):
            fail(f"commercial-ready asset {asset_id} has unresolved rights conflicts")

        if intended.get("commercial") and asset.get("commercial_use") in {"prohibited", "unknown"}:
            if status == "commercial_ready":
                fail(f"commercial-ready asset {asset_id} lacks commercial-use permission")
        if intended.get("redistribution") and asset.get("redistribution") in {"prohibited", "unknown"}:
            if status == "commercial_ready":
                fail(f"commercial-ready asset {asset_id} lacks redistribution permission")
        if intended.get("training_or_finetuning") and asset.get("training_reuse") in {"prohibited", "unknown"}:
            if status == "commercial_ready":
                fail(f"commercial-ready asset {asset_id} lacks training/reuse permission")
        if status == "commercial_ready" and rights in {"unknown", "incompatible", "expired"}:
            fail(f"commercial-ready asset {asset_id} has unresolved/incompatible rights")

    customer = record.get("customer_terms")
    if not isinstance(customer, dict):
        fail("customer_terms must be an object")
    require_refs(customer.get("evidence_ids"), evidence, "customer_terms", current=status == "commercial_ready" and intended.get("customer_deliverable"))
    if status == "commercial_ready" and intended.get("customer_deliverable"):
        if customer.get("input_use") == "unknown":
            fail("commercial-ready customer deliverable cannot leave input-use rights unknown")
        if customer.get("deliverable_ownership_promise") == "unknown":
            fail("commercial-ready customer deliverable cannot leave ownership promise unknown")
        if customer.get("provider_pass_through_reviewed") is not True:
            fail("commercial-ready customer deliverable requires provider pass-through review")
    if intended.get("training_or_finetuning") and customer.get("training_reuse") in {"prohibited", "unknown"}:
        if status == "commercial_ready":
            fail("commercial-ready training/fine-tuning cannot use customer data without resolved permission")

    output = record.get("output_rights")
    if not isinstance(output, dict):
        fail("output_rights must be an object")
    require_refs(output.get("evidence_ids"), evidence, "output_rights", current=status == "commercial_ready" and intended.get("customer_deliverable"))
    if status == "commercial_ready" and intended.get("customer_deliverable"):
        if output.get("provider_claim") == "unknown" or output.get("founder_claim") == "unknown":
            fail("commercial-ready customer deliverable requires resolved output-rights claims")

    review = record.get("review")
    if not isinstance(review, dict):
        fail("review must be an object")
    blockers = review.get("blockers")
    if not isinstance(blockers, list):
        fail("review.blockers must be a list")
    if status == "commercial_ready":
        if blockers:
            fail("commercial-ready record cannot have unresolved review blockers")
        if review.get("owner_review_required") and review.get("reviewed_at") is None:
            fail("commercial-ready record requiring owner review needs reviewed_at")
        if review.get("legal_review_required") and review.get("reviewed_at") is None:
            fail("commercial-ready record requiring legal review needs reviewed_at")
        if review.get("reviewed_at") is not None:
            parse_time(review.get("reviewed_at"), "review.reviewed_at")


def ensure_repo_path(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    if path != ROOT and ROOT not in path.parents:
        fail("record path must stay inside repository")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", nargs="?", default="templates/IP_RIGHTS_RECORD.json")
    args = parser.parse_args()
    path = ensure_repo_path(args.record)
    record = load_json(path)
    validate(record)
    print(f"ip rights OK: {record['record_id']} status={record['status']} assets={len(record['assets'])} evidence={len(record['evidence'])}")


if __name__ == "__main__":
    main()
