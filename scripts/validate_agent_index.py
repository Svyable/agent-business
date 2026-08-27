#!/usr/bin/env python3
"""Validate the machine-readable Agent Business repository index."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "agent-index.json"


def fail(message: str) -> None:
    raise SystemExit(f"agent-index validation failed: {message}")


def main() -> None:
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    resources = data.get("resources")
    if not isinstance(resources, list) or not resources:
        fail("resources must be a non-empty list")

    ids: set[str] = set()
    stages: list[int] = []

    for resource in resources:
        resource_id = resource.get("id")
        if not isinstance(resource_id, str) or not resource_id:
            fail("every resource needs a non-empty string id")
        if resource_id in ids:
            fail(f"duplicate resource id: {resource_id}")
        ids.add(resource_id)

        path = resource.get("path")
        if not isinstance(path, str) or not path:
            fail(f"{resource_id}: path must be a non-empty string")
        if not (ROOT / path).is_file():
            fail(f"{resource_id}: indexed path does not exist: {path}")

        if resource.get("type") == "founder_stage":
            stage = resource.get("stage")
            if not isinstance(stage, int) or stage < 1:
                fail(f"{resource_id}: founder_stage requires a positive integer stage")
            stages.append(stage)

        for field in ("prerequisites", "next"):
            refs = resource.get(field, [])
            if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
                fail(f"{resource_id}: {field} must be a list of resource ids")

        outputs = resource.get("outputs")
        if not isinstance(outputs, list) or not outputs or any(not isinstance(item, str) or not item for item in outputs):
            fail(f"{resource_id}: outputs must be a non-empty list of strings")

    if sorted(stages) != list(range(1, len(stages) + 1)):
        fail("founder stages must be unique and contiguous starting at 1")

    for resource in resources:
        resource_id = resource["id"]
        for field in ("prerequisites", "next"):
            for ref in resource.get(field, []):
                if ref not in ids:
                    fail(f"{resource_id}: {field} references unknown id {ref}")
                if ref == resource_id:
                    fail(f"{resource_id}: {field} cannot self-reference")

    for entrypoint in ("canonical_entrypoint", "human_entrypoint", "llm_entrypoint"):
        path = data.get(entrypoint)
        if not isinstance(path, str) or not path or not (ROOT / path).is_file():
            fail(f"{entrypoint} must point to an existing file")

    print(
        f"agent-index OK: {len(resources)} resources, "
        f"{len(stages)} contiguous founder stages, no broken paths or resource references"
    )


if __name__ == "__main__":
    main()
