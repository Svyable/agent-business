#!/usr/bin/env python3
"""Dependency-free semantic validator for Agent Business diligence rooms."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

CLAIM_ID = re.compile(r"^claim-[A-Za-z0-9._-]+$")
EVIDENCE_ID = re.compile(r"^evidence-[A-Za-z0-9._-]+$")
RISK_ID = re.compile(r"^risk-[A-Za-z0-9._-]+$")
VALID_AUDIENCES = {
    "enterprise_customer", "investor", "acquirer", "insurer",
    "marketplace", "counterparty", "internal",
}


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate(room: dict, today: date) -> list[str]:
    errors: list[str] = []
    required = {"schema_version", "company", "generated_at", "audience", "claims", "evidence", "risks", "readiness"}
    missing = sorted(required - room.keys())
    if missing:
        errors.append(f"missing required top-level fields: {', '.join(missing)}")
        return errors

    if room["schema_version"] != "1.0":
        errors.append("schema_version must be 1.0")
    if room["audience"] not in VALID_AUDIENCES:
        errors.append(f"unknown audience: {room['audience']}")

    try:
        generated_at = parse_datetime(room["generated_at"])
        if generated_at.tzinfo is None:
            errors.append("generated_at must include a timezone")
        elif generated_at > datetime.now(timezone.utc):
            errors.append("generated_at cannot be in the future")
    except (TypeError, ValueError):
        errors.append("generated_at must be ISO-8601 datetime")

    evidence_by_id = {}
    for item in room.get("evidence", []):
        eid = item.get("id", "")
        if not EVIDENCE_ID.match(eid):
            errors.append(f"invalid evidence id: {eid!r}")
        if eid in evidence_by_id:
            errors.append(f"duplicate evidence id: {eid}")
        evidence_by_id[eid] = item
        audiences = item.get("allowed_audiences", [])
        if room["audience"] not in audiences:
            errors.append(f"{eid} is not authorized for audience {room['audience']}")
        if item.get("sensitivity") == "restricted" and not item.get("redaction"):
            errors.append(f"{eid} is restricted but has no redaction rule")
        expires = item.get("expires_on")
        if expires:
            try:
                if parse_date(expires) < today:
                    errors.append(f"stale evidence: {eid} expired {expires}")
            except ValueError:
                errors.append(f"invalid expires_on date for {eid}: {expires}")
        integrity = item.get("integrity") or {}
        if not integrity.get("method") or not integrity.get("value"):
            errors.append(f"{eid} lacks integrity metadata")
        if integrity.get("value") == "REPLACE_WITH_SHA256":
            errors.append(f"{eid} still contains placeholder integrity value")

    claim_by_id = {}
    normalized_claims: dict[tuple[str, str], list[dict]] = {}
    for claim in room.get("claims", []):
        cid = claim.get("id", "")
        if not CLAIM_ID.match(cid):
            errors.append(f"invalid claim id: {cid!r}")
        if cid in claim_by_id:
            errors.append(f"duplicate claim id: {cid}")
        claim_by_id[cid] = claim
        for eid in claim.get("evidence_ids", []):
            if eid not in evidence_by_id:
                errors.append(f"{cid} references unknown evidence: {eid}")
        expires = claim.get("expires_on")
        if expires:
            try:
                if parse_date(expires) < today:
                    errors.append(f"stale claim: {cid} expired {expires}")
            except ValueError:
                errors.append(f"invalid expires_on date for {cid}: {expires}")
        if claim.get("status") == "qualified" and not claim.get("qualification"):
            errors.append(f"qualified claim {cid} must explain its qualification")
        if claim.get("status") == "disputed":
            errors.append(f"disputed claim blocks readiness: {cid}")
        key = (claim.get("category", ""), " ".join(claim.get("statement", "").lower().split()))
        normalized_claims.setdefault(key, []).append(claim)

    for key, claims in normalized_claims.items():
        statuses = {c.get("status", "verified") for c in claims}
        if "verified" in statuses and "disputed" in statuses:
            ids = ", ".join(c.get("id", "?") for c in claims)
            errors.append(f"contradictory duplicate claim statuses: {ids}")

    risk_by_id = {}
    for risk in room.get("risks", []):
        rid = risk.get("id", "")
        if not RISK_ID.match(rid):
            errors.append(f"invalid risk id: {rid!r}")
        if rid in risk_by_id:
            errors.append(f"duplicate risk id: {rid}")
        risk_by_id[rid] = risk
        for eid in risk.get("evidence_ids", []):
            if eid not in evidence_by_id:
                errors.append(f"{rid} references unknown evidence: {eid}")

    readiness = room.get("readiness") or {}
    for cid in readiness.get("blocking_claim_ids", []):
        if cid not in claim_by_id:
            errors.append(f"readiness references unknown blocking claim: {cid}")
    for rid in readiness.get("blocking_risk_ids", []):
        if rid not in risk_by_id:
            errors.append(f"readiness references unknown blocking risk: {rid}")

    critical_open = [r["id"] for r in room.get("risks", []) if r.get("severity") == "critical" and r.get("status") != "closed"]
    high_open = [r["id"] for r in room.get("risks", []) if r.get("severity") == "high" and r.get("status") in {"open", "mitigating"}]
    if readiness.get("status") == "ready":
        if readiness.get("blocking_claim_ids") or readiness.get("blocking_risk_ids"):
            errors.append("readiness cannot be ready while blockers are listed")
        if critical_open:
            errors.append("readiness cannot be ready with open critical risks: " + ", ".join(critical_open))
        if any(c.get("status") in {"draft", "disputed"} for c in room.get("claims", [])):
            errors.append("readiness cannot be ready with draft or disputed claims")
    if critical_open and not set(critical_open).issubset(set(readiness.get("blocking_risk_ids", []))):
        errors.append("all open critical risks must be listed as readiness blockers")
    if high_open and readiness.get("status") == "ready":
        errors.append("ready rooms must close, accept, or explicitly downgrade high risks")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Path to a diligence room JSON file")
    parser.add_argument("--today", type=date.fromisoformat, default=date.today(), help="Validation date (YYYY-MM-DD)")
    args = parser.parse_args()

    try:
        room = json.loads(args.path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    errors = validate(room, args.today)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"FAILED: {len(errors)} diligence issue(s)")
        return 1

    print("OK: diligence room is internally consistent and audience-scoped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
