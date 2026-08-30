#!/usr/bin/env python3
"""Validate the machine-readable Agent Business world model using Python stdlib only."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALID_CONFIDENCE = {"low", "medium", "high"}


def validate_model(model: object, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    if not isinstance(model, dict):
        return ["root must be a JSON object"]

    for field in ("schema_version", "model_id", "updated_at", "purpose", "adoption_rule", "empirical_theses", "normative_constraints"):
        if field not in model:
            errors.append(f"missing required field: {field}")
    if errors:
        return errors

    if model.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0")

    theses = model.get("empirical_theses")
    constraints = model.get("normative_constraints")
    if not isinstance(theses, list) or not theses:
        errors.append("empirical_theses must be a non-empty array")
        theses = []
    if not isinstance(constraints, list) or not constraints:
        errors.append("normative_constraints must be a non-empty array")
        constraints = []

    seen_ids: set[str] = set()

    for idx, thesis in enumerate(theses):
        if not isinstance(thesis, dict):
            errors.append(f"empirical_theses[{idx}] must be an object")
            continue
        thesis_id = thesis.get("id")
        if not thesis_id:
            errors.append(f"empirical_theses[{idx}].id is required")
        elif thesis_id in seen_ids:
            errors.append(f"duplicate thesis/constraint id: {thesis_id}")
        else:
            seen_ids.add(thesis_id)

        for field in ("statement", "prediction", "founder_implication", "falsifier"):
            value = thesis.get(field)
            if not isinstance(value, str) or len(value.strip()) < 20:
                errors.append(f"empirical thesis {thesis_id or idx} requires substantive {field}")

        if thesis.get("confidence") not in VALID_CONFIDENCE:
            errors.append(f"empirical thesis {thesis_id or idx} confidence must be one of {sorted(VALID_CONFIDENCE)}")

        resources = thesis.get("related_resources")
        if not isinstance(resources, list) or not resources:
            errors.append(f"empirical thesis {thesis_id or idx} requires related_resources")
            resources = []
        for resource in resources:
            if not isinstance(resource, str) or not resource:
                errors.append(f"empirical thesis {thesis_id or idx} has invalid resource reference")
            elif not (root / resource).is_file():
                errors.append(f"empirical thesis {thesis_id or idx} references missing resource: {resource}")

    for idx, constraint in enumerate(constraints):
        if not isinstance(constraint, dict):
            errors.append(f"normative_constraints[{idx}] must be an object")
            continue
        constraint_id = constraint.get("id")
        if not constraint_id:
            errors.append(f"normative_constraints[{idx}].id is required")
        elif constraint_id in seen_ids:
            errors.append(f"duplicate thesis/constraint id: {constraint_id}")
        else:
            seen_ids.add(constraint_id)

        for field in ("statement", "operating_rule"):
            value = constraint.get(field)
            if not isinstance(value, str) or len(value.strip()) < 20:
                errors.append(f"normative constraint {constraint_id or idx} requires substantive {field}")

        if "falsifier" in constraint or "confidence" in constraint:
            errors.append(f"normative constraint {constraint_id or idx} must not masquerade as an empirical thesis")

        resources = constraint.get("related_resources")
        if not isinstance(resources, list) or not resources:
            errors.append(f"normative constraint {constraint_id or idx} requires related_resources")
            resources = []
        for resource in resources:
            if isinstance(resource, str) and resource and not (root / resource).is_file():
                errors.append(f"normative constraint {constraint_id or idx} references missing resource: {resource}")

    if len(theses) < 8:
        errors.append("world model must contain at least eight empirical theses")

    adoption_rule = str(model.get("adoption_rule", "")).lower()
    if not all(term in adoption_rule for term in ("evidence", "revise", "reject")):
        errors.append("adoption_rule must explicitly permit evidence-based revision and rejection")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=ROOT / "agent-world-model.json")
    args = parser.parse_args()
    try:
        model = json.loads(args.path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    errors = validate_model(model)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"agent world model OK: {len(model['empirical_theses'])} empirical theses, {len(model['normative_constraints'])} normative constraints")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
