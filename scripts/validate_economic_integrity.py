#!/usr/bin/env python3
"""Validate the Agent Business economic action policy starter asset."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "templates" / "ECONOMIC_ACTION_POLICY.json"
SCHEMA = ROOT / "schemas" / "economic-action-policy.schema.json"

ACTIONS = {
    "purchase", "payout", "refund", "credit", "referral_reward", "marketplace_trade",
    "procurement_award", "withdrawal", "promotion", "discount", "service_credit", "other",
}
ASSURANCE = {"anonymous", "self_declared", "verified", "strong_verified"}
REQUIRED_EVIDENCE = {"identity", "authority", "risk_decision"}


def fail(message: str) -> None:
    raise SystemExit(f"economic integrity validation failed: {message}")


def load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot parse {path.relative_to(ROOT)}: {exc}")
    if not isinstance(data, dict):
        fail(f"{path.relative_to(ROOT)} must contain a JSON object")
    return data


def main() -> None:
    schema = load(SCHEMA)
    policy = load(POLICY)

    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("schema must declare JSON Schema draft 2020-12")
    if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        fail("schema must be a closed top-level object")

    if policy.get("schema_version") != "1.0.0":
        fail("policy schema_version must be 1.0.0")
    if policy.get("status") != "draft":
        fail("repository starter policy must remain draft")

    action = policy.get("action")
    if not isinstance(action, dict) or action.get("type") not in ACTIONS:
        fail("policy action.type is invalid")

    exposure = policy.get("exposure")
    if not isinstance(exposure, dict):
        fail("policy requires exposure")
    single = exposure.get("max_single_amount")
    daily = exposure.get("max_daily_amount")
    lifetime = exposure.get("max_lifetime_amount")
    if not isinstance(single, (int, float)) or single < 0:
        fail("max_single_amount must be non-negative")
    if not isinstance(daily, (int, float)) or daily < single:
        fail("max_daily_amount must be >= max_single_amount")
    if lifetime is not None and (not isinstance(lifetime, (int, float)) or lifetime < daily):
        fail("max_lifetime_amount must be null or >= max_daily_amount")

    identity = policy.get("identity")
    if not isinstance(identity, dict) or identity.get("minimum_assurance") not in ASSURANCE:
        fail("identity.minimum_assurance is invalid")

    authority = policy.get("authority")
    if not isinstance(authority, dict):
        fail("policy requires authority controls")
    for field in ("required", "must_be_current", "must_cover_action", "must_cover_amount"):
        if authority.get(field) is not True:
            fail(f"repository starter authority.{field} must be true")

    velocity = policy.get("velocity")
    if not isinstance(velocity, dict):
        fail("policy requires velocity controls")
    hourly = velocity.get("max_actions_per_hour")
    daily_actions = velocity.get("max_actions_per_day")
    if not isinstance(hourly, int) or hourly < 1:
        fail("max_actions_per_hour must be positive")
    if not isinstance(daily_actions, int) or daily_actions < hourly:
        fail("max_actions_per_day must be >= max_actions_per_hour")

    bands = policy.get("decision_bands")
    if not isinstance(bands, dict):
        fail("policy requires decision_bands")
    allow = bands.get("allow_max_risk")
    step_up = bands.get("step_up_max_risk")
    review = bands.get("review_max_risk")
    deny = bands.get("deny_above_risk")
    values = (allow, step_up, review, deny)
    if any(not isinstance(v, (int, float)) or v < 0 or v > 1 for v in values):
        fail("risk thresholds must be numbers from 0 to 1")
    if not (allow <= step_up <= review <= deny):
        fail("risk thresholds must be monotonic: allow <= step_up <= review <= deny")
    if bands.get("fail_closed_on_missing_risk") is not True:
        fail("repository starter must fail closed on missing risk")

    evidence = policy.get("evidence")
    if not isinstance(evidence, dict):
        fail("policy requires evidence controls")
    refs = evidence.get("required_references")
    if not isinstance(refs, list) or not REQUIRED_EVIDENCE.issubset(set(refs)):
        fail("required_references must include identity, authority, and risk_decision")
    if evidence.get("retain_decision_version") is not True:
        fail("risk decision version must be retained")

    reserve = policy.get("reserve")
    if not isinstance(reserve, dict):
        fail("policy requires reserve controls")
    if reserve.get("required") is False and reserve.get("basis_points") != 0:
        fail("reserve basis_points must be 0 when reserve is not required")

    incident = policy.get("incident")
    if not isinstance(incident, dict):
        fail("policy requires incident controls")
    for field in ("kill_switch_required", "freeze_on_compromise", "preserve_evidence"):
        if incident.get(field) is not True:
            fail(f"repository starter incident.{field} must be true")

    metadata = policy.get("metadata")
    if not isinstance(metadata, dict) or metadata.get("owner") != "REPLACE_ME":
        fail("repository starter owner must remain REPLACE_ME")
    if metadata.get("effective_at") is not None:
        fail("repository starter effective_at must remain null")

    print("economic integrity assets OK: draft policy is bounded, monotonic, fail-closed, and evidence-backed")


if __name__ == "__main__":
    main()
