#!/usr/bin/env python3
"""Validate and negotiate portable Agent Business compatibility profiles."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "1.0.0"
SUPPORT_RANK = {
    "declared": 0,
    "tested": 1,
    "observed_in_production": 2,
    "independently_verified": 3,
}
KNOWN_CONVENTIONS = {
    "evidence-provenance",
    "bounded-authority",
    "versioned-commercial-truth",
    "economic-state-separation",
    "fully-loaded-outcome-economics",
    "machine-rfq",
    "machine-proposal",
    "machine-payment-reconciliation",
    "execution-evidence",
    "capability-specific-reputation",
}
CORE_CONVENTIONS = {
    "evidence-provenance",
    "bounded-authority",
    "economic-state-separation",
}


def parse_time(value: object, field: str, errors: list[str]) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        errors.append(f"{field} must be an RFC3339 string or null")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{field} is not a valid RFC3339 timestamp")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{field} must include a timezone")
        return None
    return parsed.astimezone(timezone.utc)


def parse_semver(value: object, field: str, errors: list[str]) -> tuple[int, int, int] | None:
    if not isinstance(value, str):
        errors.append(f"{field} must be a semantic version")
        return None
    parts = value.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        errors.append(f"{field} must be MAJOR.MINOR.PATCH")
        return None
    return tuple(int(part) for part in parts)  # type: ignore[return-value]


def validate_profile(profile: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(profile, dict):
        return ["root must be a JSON object"]

    required = [
        "schema_version", "profile_id", "profile_version", "publisher", "updated_at",
        "expires_at", "world_model", "conventions", "publication", "disclosure",
        "compatibility_grants_authority",
    ]
    for key in required:
        if key not in profile:
            errors.append(f"missing required field: {key}")
    if errors:
        return errors

    if profile.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    parse_semver(profile.get("profile_version"), "profile_version", errors)

    updated_at = parse_time(profile.get("updated_at"), "updated_at", errors)
    expires_at = parse_time(profile.get("expires_at"), "expires_at", errors)
    if updated_at and expires_at and expires_at <= updated_at:
        errors.append("expires_at must be after updated_at")

    publisher = profile.get("publisher")
    if not isinstance(publisher, dict):
        errors.append("publisher must be an object")
    elif not publisher.get("agent_or_business_ref"):
        errors.append("publisher.agent_or_business_ref is required")

    world_model = profile.get("world_model")
    if not isinstance(world_model, dict):
        errors.append("world_model must be an object")
    else:
        if world_model.get("model_id") != "agent-business-world-model":
            errors.append("world_model.model_id must be agent-business-world-model")
        parse_semver(world_model.get("schema_version"), "world_model.schema_version", errors)

    if profile.get("compatibility_grants_authority") is not False:
        errors.append("compatibility_grants_authority must be false")
    certification_claim = profile.get("certification_claim")
    if certification_claim not in (None, ""):
        errors.append("compatibility profiles must not claim Agent Business certification")

    disclosure = profile.get("disclosure")
    if not isinstance(disclosure, dict):
        errors.append("disclosure must be an object")
    else:
        for flag in (
            "contains_secrets", "contains_credentials", "contains_private_customer_data",
            "contains_private_prompts",
        ):
            if disclosure.get(flag) is not False:
                errors.append(f"disclosure.{flag} must be false")
        if disclosure.get("public_disclosure_confirmed") is not True:
            errors.append("disclosure.public_disclosure_confirmed must be true")

    conventions = profile.get("conventions")
    if not isinstance(conventions, list) or not conventions:
        errors.append("conventions must be a non-empty array")
        return errors

    seen: set[str] = set()
    for idx, convention in enumerate(conventions):
        prefix = f"conventions[{idx}]"
        if not isinstance(convention, dict):
            errors.append(f"{prefix} must be an object")
            continue
        convention_id = convention.get("id")
        if not isinstance(convention_id, str) or not convention_id:
            errors.append(f"{prefix}.id is required")
            continue
        if convention_id in seen:
            errors.append(f"duplicate convention id: {convention_id}")
        seen.add(convention_id)
        if convention_id not in KNOWN_CONVENTIONS and not convention_id.startswith("x-"):
            errors.append(f"unknown convention {convention_id} must use x- namespace")

        parse_semver(convention.get("spec_version"), f"{prefix}.spec_version", errors)
        support_state = convention.get("support_state")
        if support_state not in SUPPORT_RANK:
            errors.append(f"{prefix}.support_state is not recognized")
            continue
        if convention.get("required_for_transaction") not in (True, False):
            errors.append(f"{prefix}.required_for_transaction must be boolean")

        evidence_expires = parse_time(
            convention.get("evidence_expires_at"), f"{prefix}.evidence_expires_at", errors
        )

        if support_state == "declared":
            # A declaration may intentionally have no evidence expiry.
            continue

        if evidence_expires is None:
            errors.append(f"{prefix} non-declared support requires evidence_expires_at")

        if support_state == "tested":
            tested_at = parse_time(convention.get("tested_at"), f"{prefix}.tested_at", errors)
            if not convention.get("test_evidence_ref"):
                errors.append(f"{prefix} tested support requires test_evidence_ref")
            if tested_at is None:
                errors.append(f"{prefix} tested support requires tested_at")
            elif evidence_expires and evidence_expires <= tested_at:
                errors.append(f"{prefix} evidence expiry must be after tested_at")

        elif support_state == "observed_in_production":
            observed_at = parse_time(convention.get("observed_at"), f"{prefix}.observed_at", errors)
            if not convention.get("production_evidence_ref"):
                errors.append(f"{prefix} production support requires production_evidence_ref")
            if not convention.get("observation_scope"):
                errors.append(f"{prefix} production support requires observation_scope")
            if observed_at is None:
                errors.append(f"{prefix} production support requires observed_at")
            elif evidence_expires and evidence_expires <= observed_at:
                errors.append(f"{prefix} evidence expiry must be after observed_at")

        elif support_state == "independently_verified":
            verified_at = parse_time(convention.get("verified_at"), f"{prefix}.verified_at", errors)
            if not convention.get("verifier_ref"):
                errors.append(f"{prefix} independent verification requires verifier_ref")
            if not convention.get("verification_evidence_ref"):
                errors.append(f"{prefix} independent verification requires verification_evidence_ref")
            if verified_at is None:
                errors.append(f"{prefix} independent verification requires verified_at")
            elif evidence_expires and evidence_expires <= verified_at:
                errors.append(f"{prefix} evidence expiry must be after verified_at")

    return errors


def convention_map(profile: dict) -> dict[str, dict]:
    return {item["id"]: item for item in profile["conventions"] if isinstance(item, dict) and item.get("id")}


def negotiate(left: dict, right: dict) -> dict:
    left_map = convention_map(left)
    right_map = convention_map(right)
    shared: list[dict] = []
    custom_shared: list[dict] = []
    blockers: list[dict] = []
    fallbacks: list[dict] = []

    all_ids = sorted(set(left_map) | set(right_map))
    required_ids = {
        convention_id
        for convention_id in all_ids
        if left_map.get(convention_id, {}).get("required_for_transaction") is True
        or right_map.get(convention_id, {}).get("required_for_transaction") is True
    }

    for convention_id in all_ids:
        left_item = left_map.get(convention_id)
        right_item = right_map.get(convention_id)
        required = convention_id in required_ids

        if left_item is None or right_item is None:
            if required:
                blockers.append({
                    "convention_id": convention_id,
                    "reason": "required_convention_missing",
                    "missing_from": "left" if left_item is None else "right",
                })
            else:
                present = left_item or right_item
                if present and present.get("fallback"):
                    fallbacks.append({
                        "convention_id": convention_id,
                        "fallback": present["fallback"],
                        "reason": "optional_convention_not_shared",
                    })
            continue

        left_version = tuple(int(p) for p in left_item["spec_version"].split("."))
        right_version = tuple(int(p) for p in right_item["spec_version"].split("."))
        if left_version[0] != right_version[0]:
            if required:
                blockers.append({
                    "convention_id": convention_id,
                    "reason": "required_major_version_mismatch",
                    "left_version": left_item["spec_version"],
                    "right_version": right_item["spec_version"],
                })
            else:
                fallback = left_item.get("fallback") or right_item.get("fallback")
                if fallback:
                    fallbacks.append({
                        "convention_id": convention_id,
                        "fallback": fallback,
                        "reason": "optional_major_version_mismatch",
                    })
            continue

        effective_state = min(
            (left_item["support_state"], right_item["support_state"]),
            key=lambda state: SUPPORT_RANK[state],
        )
        negotiated_version = ".".join(str(p) for p in min(left_version, right_version))
        result = {
            "convention_id": convention_id,
            "negotiated_version": negotiated_version,
            "effective_support_state": effective_state,
            "required": required,
        }
        if convention_id in KNOWN_CONVENTIONS:
            shared.append(result)
        else:
            result["semantics"] = "counterparty-defined; not an Agent Business standard convention"
            custom_shared.append(result)

    shared_known_ids = {item["convention_id"] for item in shared}
    if blockers:
        mode = "stop"
    elif CORE_CONVENTIONS.issubset(shared_known_ids):
        mode = "structured" if not fallbacks else "reduced"
    else:
        mode = "reduced"

    return {
        "left_profile_id": left.get("profile_id"),
        "right_profile_id": right.get("profile_id"),
        "transaction_mode": mode,
        "shared": shared,
        "custom_shared": custom_shared,
        "blockers": blockers,
        "fallbacks": fallbacks,
        "authority_granted": False,
        "note": "Compatibility negotiation never grants transaction authority, capability, certification, or trust.",
    }


def load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("--negotiate", type=Path, metavar="COUNTERPARTY")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable negotiation output")
    args = parser.parse_args()

    try:
        left = load(args.profile)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    left_errors = validate_profile(left)
    if left_errors:
        for error in left_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.negotiate is None:
        assert isinstance(left, dict)
        print(f"compatibility profile OK: {left.get('profile_id')} conventions={len(left.get('conventions', []))}")
        return 0

    try:
        right = load(args.negotiate)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    right_errors = validate_profile(right)
    if right_errors:
        for error in right_errors:
            print(f"COUNTERPARTY ERROR: {error}", file=sys.stderr)
        return 1

    assert isinstance(left, dict) and isinstance(right, dict)
    result = negotiate(left, right)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(
            f"compatibility handshake: mode={result['transaction_mode']} "
            f"shared={len(result['shared'])} blockers={len(result['blockers'])} "
            f"fallbacks={len(result['fallbacks'])}"
        )
    return 3 if result["transaction_mode"] == "stop" else 0


if __name__ == "__main__":
    raise SystemExit(main())
