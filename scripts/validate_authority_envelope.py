#!/usr/bin/env python3
"""Dependency-free semantic checks for an Agent Business authority envelope.

This validator intentionally does not verify cryptographic signatures or legal authority.
It checks conservative invariants that can be evaluated locally and fails closed.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


PLACEHOLDER_MARKERS = ("replace_me", "replace_with", "example")


def parse_time(value, field, errors):
    try:
        text = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            raise ValueError("timezone required")
        return parsed
    except Exception as exc:
        errors.append(f"{field}: invalid date-time ({exc})")
        return None


def as_set(scope, key):
    value = scope.get(key, []) if isinstance(scope, dict) else []
    return set(value) if isinstance(value, list) else set()


def check_placeholders(value, path, errors):
    if isinstance(value, dict):
        for key, child in value.items():
            check_placeholders(child, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            check_placeholders(child, f"{path}[{index}]", errors)
    elif isinstance(value, str) and any(marker in value.lower() for marker in PLACEHOLDER_MARKERS):
        errors.append(f"{path}: placeholder value must be replaced before activation")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("envelope", type=Path)
    parser.add_argument("--parent", type=Path, help="Optional parent envelope for attenuation checks")
    parser.add_argument("--used", type=int, default=0, help="Observed uses for replay-bound validation")
    args = parser.parse_args()

    errors = []
    try:
        doc = json.loads(args.envelope.read_text())
    except Exception as exc:
        print(f"ERROR: cannot read envelope: {exc}", file=sys.stderr)
        return 2

    required = ["schema_version", "authority_id", "principal", "delegate", "purpose", "validity", "status", "scopes", "delegation", "replay", "audit"]
    for field in required:
        if field not in doc:
            errors.append(f"missing required field: {field}")

    if doc.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")

    validity = doc.get("validity", {})
    start = parse_time(validity.get("not_before", ""), "validity.not_before", errors)
    expiry = parse_time(validity.get("expires_at", ""), "validity.expires_at", errors)
    now = datetime.now(timezone.utc)
    if start and expiry:
        if expiry <= start:
            errors.append("validity.expires_at must be after not_before")
        if doc.get("status", {}).get("state") == "active" and not (start <= now < expiry):
            errors.append("active authority is outside its validity window")

    status = doc.get("status", {})
    state = status.get("state")
    if state in {"revoked", "suspended", "expired"}:
        errors.append(f"authority state {state!r} is not executable")
    if state == "revoked" and not status.get("revoked_at"):
        errors.append("revoked authority must record revoked_at")

    scopes = doc.get("scopes", {})
    for name in ("actions", "tools", "geography"):
        scope = scopes.get(name, {})
        overlap = as_set(scope, "allowed") & as_set(scope, "prohibited")
        if overlap:
            errors.append(f"scopes.{name}: values cannot be both allowed and prohibited: {sorted(overlap)}")

    data = scopes.get("data", {})
    overlap = as_set(data, "allowed") & as_set(data, "prohibited")
    if overlap:
        errors.append(f"scopes.data: values cannot be both allowed and prohibited: {sorted(overlap)}")
    if data.get("onward_sharing") != "none" and not data.get("consent_reference"):
        errors.append("data onward sharing requires an explicit consent_reference")

    spend = scopes.get("spend", {})
    for field in ("per_action_max", "total_max", "approval_threshold"):
        value = spend.get(field)
        if not isinstance(value, (int, float)) or value < 0:
            errors.append(f"scopes.spend.{field} must be a non-negative number")
    if isinstance(spend.get("per_action_max"), (int, float)) and isinstance(spend.get("total_max"), (int, float)):
        if spend["per_action_max"] > spend["total_max"]:
            errors.append("per_action_max cannot exceed total_max")
    if isinstance(spend.get("approval_threshold"), (int, float)) and isinstance(spend.get("total_max"), (int, float)):
        if spend["approval_threshold"] > spend["total_max"]:
            errors.append("approval_threshold cannot exceed total_max")

    delegation = doc.get("delegation", {})
    depth = delegation.get("current_depth")
    max_depth = delegation.get("max_depth")
    if isinstance(depth, int) and isinstance(max_depth, int) and depth > max_depth:
        errors.append("delegation.current_depth exceeds max_depth")
    if not delegation.get("permitted") and max_depth not in (0, None):
        errors.append("delegation.max_depth must be 0 when delegation is not permitted")
    if delegation.get("child_must_narrow") is not True:
        errors.append("delegation.child_must_narrow must be true")

    replay = doc.get("replay", {})
    if replay.get("mode") == "single_use" and replay.get("max_uses") != 1:
        errors.append("single_use authority must have max_uses=1")
    max_uses = replay.get("max_uses")
    if isinstance(max_uses, int) and args.used >= max_uses:
        errors.append(f"replay budget exhausted: used={args.used}, max_uses={max_uses}")

    if state == "active":
        check_placeholders(doc, "$", errors)
        audit = doc.get("audit", {})
        if not audit.get("evidence_reference"):
            errors.append("active authority requires audit.evidence_reference")

    if args.parent:
        try:
            parent = json.loads(args.parent.read_text())
        except Exception as exc:
            errors.append(f"cannot read parent envelope: {exc}")
            parent = None
        if parent:
            if doc.get("parent_authority_id") != parent.get("authority_id"):
                errors.append("parent_authority_id does not match parent authority_id")
            pd = parent.get("delegation", {})
            if not pd.get("permitted"):
                errors.append("parent does not permit delegation")
            if doc.get("delegation", {}).get("current_depth") != pd.get("current_depth", 0) + 1:
                errors.append("child delegation depth must equal parent depth + 1")
            if doc.get("purpose") != parent.get("purpose"):
                errors.append("child purpose must not drift from parent purpose")
            for name in ("actions", "tools"):
                child_allowed = as_set(doc.get("scopes", {}).get(name, {}), "allowed")
                parent_allowed = as_set(parent.get("scopes", {}).get(name, {}), "allowed")
                if not child_allowed <= parent_allowed:
                    errors.append(f"child {name} scope widens parent: {sorted(child_allowed - parent_allowed)}")
            child_spend = doc.get("scopes", {}).get("spend", {})
            parent_spend = parent.get("scopes", {}).get("spend", {})
            for field in ("per_action_max", "total_max", "approval_threshold"):
                cv, pv = child_spend.get(field), parent_spend.get(field)
                if isinstance(cv, (int, float)) and isinstance(pv, (int, float)) and cv > pv:
                    errors.append(f"child spend {field} exceeds parent")
            child_expiry = parse_time(doc.get("validity", {}).get("expires_at", ""), "child expiry", errors)
            parent_expiry = parse_time(parent.get("validity", {}).get("expires_at", ""), "parent expiry", errors)
            if child_expiry and parent_expiry and child_expiry > parent_expiry:
                errors.append("child authority cannot outlive parent")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: {doc.get('authority_id')} passes local semantic checks")
    print("NOTE: this does not verify signatures, identity, consent, or legal authority")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
