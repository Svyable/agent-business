#!/usr/bin/env python3
"""Validate third-party platform access records without third-party packages."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "agent-index.json"
ACTIVEISH = {"authorized_method_selected", "configured", "tested", "active", "restricted"}
CONSEQUENTIAL = {"write_update", "message", "purchase_order", "account_change", "permission_change", "delete_destroy"}
PROHIBITED_KEYS = {
    "password", "secret", "api_key", "access_token", "refresh_token", "session_token",
    "cookie", "cookies", "authorization", "private_key", "raw_private_content", "raw_prompt"
}


def fail(message: str) -> None:
    raise SystemExit(f"platform-access validation failed: {message}")


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
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        fail(f"{label} must be an ISO-8601 date-time")
    if parsed.tzinfo is None:
        fail(f"{label} must include a timezone")
    return parsed


def scan(value: object, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in PROHIBITED_KEYS:
                fail(f"prohibited sensitive field: {path}.{key}")
            scan(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan(child, f"{path}[{index}]")


def evidence_map(items: object) -> dict[str, dict]:
    if not isinstance(items, list):
        fail("evidence must be a list")
    mapped: dict[str, dict] = {}
    for item in items:
        if not isinstance(item, dict):
            fail("evidence entries must be objects")
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            fail("evidence entries need non-empty ids")
        if item_id in mapped:
            fail(f"duplicate evidence id: {item_id}")
        parse_time(item.get("observed_at"), f"evidence {item_id}.observed_at")
        reference = item.get("reference")
        if not isinstance(reference, str) or not reference:
            fail(f"evidence {item_id}.reference must be non-empty")
        mapped[item_id] = item
    return mapped


def require_current_refs(label: str, refs: object, evidence: dict[str, dict]) -> None:
    if not isinstance(refs, list):
        fail(f"{label} evidence_ids must be a list")
    if not refs:
        fail(f"{label} requires evidence")
    for ref in refs:
        if ref not in evidence:
            fail(f"{label} references unknown evidence: {ref}")
        if evidence[ref].get("status") != "current":
            fail(f"{label} must reference current evidence: {ref}")


def validate(record: dict) -> None:
    required = {
        "schema_version", "record_id", "status", "updated_at", "platform", "business_purpose",
        "principal_delegation", "platform_authorization", "access_method", "terms_policy", "identity",
        "credentials", "actions", "limits", "signals", "authority", "evidence", "privacy"
    }
    missing = sorted(required - set(record))
    if missing:
        fail(f"missing required fields: {', '.join(missing)}")
    if record.get("schema_version") != "1.0.0":
        fail("schema_version must be 1.0.0")
    status = record.get("status")
    statuses = {"proposed","platform_review","authorized_method_selected","configured","tested","active","restricted","suspended","retired"}
    if status not in statuses:
        fail("status is invalid")
    updated_at = parse_time(record.get("updated_at"), "updated_at")
    scan(record)

    resources = {item.get("id") for item in load(INDEX).get("resources", []) if isinstance(item, dict)}
    for resource_id in record.get("repository_resources", []):
        if resource_id not in resources:
            fail(f"unknown repository resource: {resource_id}")

    evidence = evidence_map(record.get("evidence"))
    principal = record.get("principal_delegation")
    platform_auth = record.get("platform_authorization")
    method = record.get("access_method")
    policy = record.get("terms_policy")
    identity = record.get("identity")
    credentials = record.get("credentials")
    actions = record.get("actions")
    limits = record.get("limits")
    signals = record.get("signals")
    authority = record.get("authority")
    privacy = record.get("privacy")
    objects = (principal, platform_auth, method, policy, identity, credentials, actions, limits, signals, authority, privacy)
    if not all(isinstance(item, dict) for item in objects):
        fail("delegation/authorization/method/policy/identity/credentials/actions/limits/signals/authority/privacy must be objects")

    for field in ("contains_credentials", "contains_session_tokens", "contains_private_customer_data", "contains_private_platform_content"):
        if privacy.get(field) is not False:
            fail(f"privacy.{field} must be false")
    if privacy.get("public_disclosure_confirmed") is not True:
        fail("privacy.public_disclosure_confirmed must be true")
    if credentials.get("embedded_secret_material") is not False:
        fail("credentials.embedded_secret_material must be false")
    if identity.get("spoofs_human_identity") is not False:
        fail("automation must not spoof human identity")

    max_retries = limits.get("max_retries")
    if not isinstance(max_retries, int) or max_retries < 0 or max_retries > 20:
        fail("limits.max_retries must be an integer from 0 to 20")
    if limits.get("backoff_required") is not True:
        fail("backoff must be required")
    if limits.get("challenge_action") not in {"stop_and_escalate", "human_review", "not_applicable"}:
        fail("challenge_action is invalid")
    if limits.get("block_action") not in {"suspend", "restrict", "stop_and_escalate"}:
        fail("block_action is invalid")

    action_values = {"allowed", "blocked", "review_required"}
    expected_actions = {"read_search", "write_update", "message", "upload_download", "purchase_order", "account_change", "permission_change", "delete_destroy"}
    if not expected_actions.issubset(actions):
        fail("actions matrix is incomplete")
    if any(actions.get(name) not in action_values for name in expected_actions):
        fail("action values must be allowed, blocked, or review_required")

    material_authority = any(authority.get(key) for key in ("can_activate", "can_resume", "can_write", "can_transact", "can_delete"))
    if material_authority:
        require_current_refs("material authority", authority.get("evidence_ids"), evidence)

    if principal.get("status") == "current":
        require_current_refs("principal delegation", principal.get("evidence_ids"), evidence)
        if not any(evidence[ref].get("type") == "principal_delegation" for ref in principal.get("evidence_ids", [])):
            fail("principal delegation must cite principal_delegation evidence")
    if platform_auth.get("status") == "current":
        require_current_refs("platform authorization", platform_auth.get("evidence_ids"), evidence)
        if not any(evidence[ref].get("type") in {"platform_terms","platform_policy","api_docs","oauth_grant","partner_approval","written_approval"} for ref in platform_auth.get("evidence_ids", [])):
            fail("platform authorization needs platform/API/OAuth/partner/written evidence")

    if status in ACTIVEISH:
        if principal.get("status") != "current":
            fail(f"{status} requires current principal delegation")
        if platform_auth.get("status") != "current":
            fail(f"{status} requires current platform authorization independent of principal delegation")
        if policy.get("automation_reviewed") is not True:
            fail(f"{status} requires reviewed automation terms/policy")
        if not policy.get("reference"):
            fail(f"{status} requires a terms/policy reference")
        retrieved = parse_time(policy.get("retrieved_at"), "terms_policy.retrieved_at")
        review_due = parse_time(policy.get("review_due_at"), "terms_policy.review_due_at")
        if review_due <= retrieved:
            fail("terms policy review_due_at must be after retrieved_at")
        if updated_at > review_due:
            fail("terms/policy evidence is stale for the record update time")
        if method.get("tested") is not True and status in {"tested", "active", "restricted"}:
            fail(f"{status} requires the selected access method to be tested")
        if not evidence:
            fail(f"{status} requires evidence")

    robots = policy.get("robots_signal")
    if method.get("type") == "scraping_or_crawling" and robots == "disallows_relevant_crawl":
        fail("cannot activate crawling against a recorded disallow signal")
    if robots == "allows_relevant_crawl" and platform_auth.get("status") != "current" and status in ACTIVEISH:
        fail("robots signal cannot substitute for platform authorization")

    objection = signals.get("explicit_objection") is True
    blocked = signals.get("blocked") is True
    challenged = signals.get("challenge_present") is True
    uncertain = signals.get("authorization_uncertain") is True
    policy_changed = signals.get("policy_changed") is True
    if status == "active" and any((objection, blocked, challenged, uncertain, policy_changed)):
        fail("active status is incompatible with objection/block/challenge/authorization uncertainty/policy change")
    if objection and status not in {"suspended", "retired"}:
        fail("explicit platform objection requires suspension or retirement")
    if challenged and limits.get("challenge_action") == "not_applicable":
        fail("observed challenge requires an explicit stop or human-review action")
    if blocked and limits.get("block_action") not in {"suspend", "restrict", "stop_and_escalate"}:
        fail("observed block requires a safe block action")

    if status == "active" and authority.get("can_activate") is not True:
        fail("active status requires explicit activation authority")
    if status == "restricted" and all(actions.get(name) == "allowed" for name in expected_actions):
        fail("restricted status must actually restrict at least one action")
    if status == "suspended" and any(actions.get(name) == "allowed" for name in CONSEQUENTIAL):
        fail("suspended records cannot leave consequential actions allowed")
    if status == "retired" and any(authority.get(key) for key in ("can_activate","can_resume","can_write","can_transact","can_delete")):
        fail("retired records cannot retain operational authority")

    if actions.get("write_update") == "allowed" or actions.get("message") == "allowed" or actions.get("account_change") == "allowed" or actions.get("permission_change") == "allowed":
        if authority.get("can_write") is not True:
            fail("allowed write/message/account/permission actions require write authority")
    if actions.get("purchase_order") == "allowed" and authority.get("can_transact") is not True:
        fail("allowed purchase/order requires transaction authority")
    if actions.get("delete_destroy") == "allowed" and authority.get("can_delete") is not True:
        fail("allowed delete/destroy requires delete authority")

    if status in {"configured","tested","active","restricted"} and credentials.get("reference") is None:
        fail(f"{status} requires a private credential/session reference when authentication is configured")

    if status == "active":
        if not any(item.get("type") == "test_result" and item.get("status") == "current" for item in evidence.values()):
            fail("active status requires current test-result evidence")
        if identity.get("mode") == "unknown":
            fail("active status requires a resolved identity mode")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", nargs="?", default="templates/PLATFORM_ACCESS_RECORD.json")
    args = parser.parse_args()
    path = (ROOT / args.record).resolve()
    if path != ROOT and ROOT not in path.parents:
        fail("record path must stay inside repository")
    record = load(path)
    validate(record)
    print(f"platform access OK: {record['record_id']} status={record['status']} evidence={len(record['evidence'])}")


if __name__ == "__main__":
    main()
