#!/usr/bin/env python3
"""Validate Agent Business founder outcome records without third-party packages."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "agent-index.json"

REQUIRED = {
    "schema_version",
    "outcome_id",
    "updated_at",
    "publication_status",
    "reporter",
    "business",
    "repository_usage",
    "baseline",
    "intervention",
    "outcomes",
    "evidence",
    "claims",
    "lessons",
    "privacy",
}
PUBLICATION_STATES = {"draft", "candidate", "published", "retired"}
CLAIM_CLASSES = {"observed_fact", "self_reported", "estimate", "editorial_interpretation"}
EVIDENCE_STATES = {"draft", "current", "disputed", "superseded"}
PROHIBITED_KEYS = {
    "password",
    "secret",
    "client_secret",
    "api_key",
    "access_token",
    "refresh_token",
    "authorization",
    "raw_prompt",
    "prompt_content",
    "card_number",
    "cvv",
    "payment_credential",
}
PLACEHOLDER_MARKERS = (
    "replace before publication",
    "replace with",
    "example business",
    "example vertical",
    "example customer",
    "example measurable",
    "draft template",
    "placeholder",
)


def fail(message: str) -> None:
    raise SystemExit(f"founder-outcome validation failed: {message}")


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


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot parse {path}: {exc}")
    if not isinstance(value, dict):
        fail("outcome record must be a JSON object")
    return value


def ensure_repo_path(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    if path != ROOT and ROOT not in path.parents:
        fail("record path must stay inside the repository")
    return path


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


def contains_placeholder(record: dict) -> str | None:
    text = json.dumps(record, sort_keys=True).lower()
    for marker in PLACEHOLDER_MARKERS:
        if marker in text:
            return marker
    return None


def validate(record: dict, *, allow_draft: bool) -> None:
    missing = sorted(REQUIRED - set(record))
    if missing:
        fail(f"missing required fields: {', '.join(missing)}")
    if record.get("schema_version") != "1.0.0":
        fail("schema_version must be 1.0.0")
    status = record.get("publication_status")
    if status not in PUBLICATION_STATES:
        fail("publication_status is invalid")
    if status == "draft" and not allow_draft:
        fail("draft records require --allow-draft")

    parse_time(record.get("updated_at"), "updated_at")
    scan_prohibited(record)

    index = load_json(INDEX)
    resources = {
        item.get("id"): item
        for item in index.get("resources", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }

    usage = record.get("repository_usage")
    if not isinstance(usage, list) or not usage:
        fail("repository_usage must contain at least one resource")
    used_ids: set[str] = set()
    for item in usage:
        if not isinstance(item, dict):
            fail("repository_usage entries must be objects")
        resource_id = item.get("resource_id")
        if resource_id not in resources:
            fail(f"repository_usage references unknown resource_id: {resource_id!r}")
        if resource_id in used_ids:
            fail(f"repository_usage duplicates resource_id: {resource_id}")
        used_ids.add(resource_id)
        if not isinstance(item.get("use"), str) or not item["use"].strip():
            fail(f"repository_usage {resource_id} needs a non-empty use description")

    reporter = record.get("reporter")
    if not isinstance(reporter, dict):
        fail("reporter must be an object")
    if reporter.get("identity_confidence") not in {"self_declared", "publicly_attributed", "verified_by_editor"}:
        fail("reporter.identity_confidence is invalid")

    intervention = record.get("intervention")
    if not isinstance(intervention, dict):
        fail("intervention must be an object")
    started = parse_time(intervention.get("started_at"), "intervention.started_at")
    ended_raw = intervention.get("ended_at")
    if ended_raw is not None:
        ended = parse_time(ended_raw, "intervention.ended_at")
        if ended < started:
            fail("intervention.ended_at cannot be before started_at")

    evidence = unique_ids(record.get("evidence"), "evidence")
    for evidence_id, item in evidence.items():
        if item.get("status") not in EVIDENCE_STATES:
            fail(f"evidence {evidence_id} has invalid status")
        parse_time(item.get("observed_at"), f"evidence {evidence_id}.observed_at")
        validate_public_url(item.get("public_url"), f"evidence {evidence_id}.public_url")
        if not isinstance(item.get("description"), str) or not item["description"].strip():
            fail(f"evidence {evidence_id} needs a description")

    outcomes = unique_ids(record.get("outcomes"), "outcome")
    if not outcomes:
        fail("outcomes must contain at least one item")
    for outcome_id, item in outcomes.items():
        refs = item.get("evidence_ids")
        if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
            fail(f"outcome {outcome_id}.evidence_ids must be a list of ids")
        unknown = sorted(set(refs) - set(evidence))
        if unknown:
            fail(f"outcome {outcome_id} references unknown evidence: {', '.join(unknown)}")
        if item.get("attribution_confidence") not in {"low", "medium", "high"}:
            fail(f"outcome {outcome_id} has invalid attribution_confidence")
        if item.get("result_value") is None and status in {"candidate", "published"}:
            fail(f"outcome {outcome_id} needs a result_value for {status} status")

    claims = unique_ids(record.get("claims"), "claim")
    if not claims:
        fail("claims must contain at least one item")
    for claim_id, item in claims.items():
        classification = item.get("classification")
        if classification not in CLAIM_CLASSES:
            fail(f"claim {claim_id} has invalid classification")
        refs = item.get("evidence_ids")
        if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
            fail(f"claim {claim_id}.evidence_ids must be a list of ids")
        unknown = sorted(set(refs) - set(evidence))
        if unknown:
            fail(f"claim {claim_id} references unknown evidence: {', '.join(unknown)}")
        if status == "published" and classification != "editorial_interpretation" and not refs:
            fail(f"published claim {claim_id} requires evidence")

    lessons = record.get("lessons")
    if not isinstance(lessons, list) or not lessons or any(not isinstance(item, str) or not item.strip() for item in lessons):
        fail("lessons must be a non-empty list of strings")

    privacy = record.get("privacy")
    if not isinstance(privacy, dict):
        fail("privacy must be an object")
    if privacy.get("public_disclosure_confirmed") is not True:
        fail("privacy.public_disclosure_confirmed must be true")
    for field in ("contains_secrets", "contains_private_prompts", "contains_payment_data", "contains_private_customer_data"):
        if privacy.get(field) is not False:
            fail(f"privacy.{field} must be false")

    if status in {"candidate", "published"} and not evidence:
        fail(f"{status} records require at least one evidence item")

    if status == "published":
        if not isinstance(record.get("source_issue"), int) or record["source_issue"] < 1:
            fail("published records require a positive source_issue for provenance")
        marker = contains_placeholder(record)
        if marker:
            fail(f"published record still contains placeholder text: {marker!r}")
        for outcome_id, item in outcomes.items():
            refs = item.get("evidence_ids", [])
            if not refs:
                fail(f"published outcome {outcome_id} requires evidence")
            non_current = [ref for ref in refs if evidence[ref].get("status") != "current"]
            if non_current:
                fail(f"published outcome {outcome_id} references non-current evidence: {', '.join(non_current)}")
        editorial = record.get("editorial")
        if not isinstance(editorial, dict) or editorial.get("reviewed_at") is None:
            fail("published records require editorial.reviewed_at")
        parse_time(editorial.get("reviewed_at"), "editorial.reviewed_at")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", nargs="?", default="templates/FOUNDER_OUTCOME_RECORD.json")
    parser.add_argument("--allow-draft", action="store_true", help="allow draft templates/candidates to validate")
    args = parser.parse_args()
    path = ensure_repo_path(args.record)
    record = load_json(path)
    validate(record, allow_draft=args.allow_draft)
    print(
        "founder outcome OK: "
        f"{record['outcome_id']} status={record['publication_status']} "
        f"resources={len(record['repository_usage'])} outcomes={len(record['outcomes'])} "
        f"evidence={len(record['evidence'])} claims={len(record['claims'])}"
    )


if __name__ == "__main__":
    main()
