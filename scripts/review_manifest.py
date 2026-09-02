#!/usr/bin/env python3
"""Validate that a Vince review exhausted its frozen coverage manifest."""

import argparse
import hashlib
import json
import sys
from pathlib import Path


TERMINAL = {"PROVEN", "FINDING", "BLOCKED", "UNREVIEWED"}
KINDS = {"acceptance", "definition-of-done", "material-claim", "entry-point", "dependent"}


def nonblank_strings(value: object, *, allow_empty: bool = False, min_length: int = 1) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(isinstance(item, str) and len(item.strip()) >= min_length for item in value)
    )


def frozen_inventory(items: list[object]) -> dict[str, object]:
    normalized = []
    counts = {kind: 0 for kind in sorted(KINDS)}
    for item in items:
        if isinstance(item, dict):
            kind = item.get("kind")
            if kind in counts:
                counts[kind] += 1
            normalized.append(
                {field: item.get(field) for field in ("id", "kind", "claim", "source")}
            )
    payload = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "item_count": len(items),
        "kind_counts": counts,
        "items_sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
    }


def validate(data: object) -> list[str]:
    if not isinstance(data, dict):
        return ["manifest must be a JSON object"]
    errors = []
    if not isinstance(data.get("task"), str) or not data["task"].strip():
        errors.append("task must be a non-empty string")
    for flag, expected in (
        ("frozen_before_ledger", True),
        ("discovery_complete", True),
        ("early_exit", False),
    ):
        if data.get(flag) is not expected:
            errors.append(f"{flag} must be {str(expected).lower()}")

    items = data.get("items")
    if not isinstance(items, list) or not items:
        errors.append("items must be a non-empty list")
        items = []
    inventory = data.get("inventory")
    expected_inventory = frozen_inventory(items)
    if inventory != expected_inventory:
        errors.append("inventory must match the frozen item count, kind counts, and SHA-256")
    if expected_inventory["kind_counts"]["acceptance"] < 1:
        errors.append("inventory must include at least one acceptance item")
    if expected_inventory["kind_counts"]["material-claim"] < 1:
        errors.append("inventory must include at least one material-claim item")
    seen = set()
    for index, item in enumerate(items):
        label = f"items[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        item_id = item.get("id")
        valid_id = isinstance(item_id, str) and bool(item_id.strip())
        if not valid_id or item_id in seen:
            errors.append(f"{label}.id must be non-empty and unique")
        if valid_id:
            seen.add(item_id)
        if item.get("kind") not in KINDS:
            errors.append(f"{label}.kind must identify a review surface")
        for field in ("claim", "source"):
            if not isinstance(item.get(field), str) or len(item[field].strip()) < 3:
                errors.append(f"{label}.{field} is required")
        status = item.get("status")
        if status not in TERMINAL:
            errors.append(f"{label}.status must be terminal")
        evidence = item.get("evidence")
        if not nonblank_strings(evidence, min_length=3):
            errors.append(f"{label}.evidence must record proof or the blocking reason")
        attacks = item.get("attacks")
        if status in {"PROVEN", "FINDING"} and not nonblank_strings(attacks, min_length=3):
            errors.append(f"{label}.attacks must record an adversarial check")

    passes = data.get("attack_passes")
    if not isinstance(passes, dict):
        errors.append("attack_passes must contain A0 through A7")
        passes = {}
    for name in (f"A{i}" for i in range(8)):
        attack = passes.get(name)
        if not isinstance(attack, dict) or attack.get("status") not in TERMINAL:
            errors.append(f"attack_passes.{name} must have a terminal status")
        elif not nonblank_strings(attack.get("evidence"), min_length=3):
            errors.append(f"attack_passes.{name}.evidence is required")

    for field in ("previous_findings", "adjacent_variants", "untouched_surfaces"):
        value = data.get(field)
        if not nonblank_strings(value, allow_empty=field != "untouched_surfaces"):
            errors.append(f"{field} must be a list of non-blank strings")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("freeze", "validate"))
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        sys.stderr.write(f"INVALID: {error}\n")
        return 2
    if args.command == "freeze":
        items = data.get("items")
        if not isinstance(data, dict) or not isinstance(items, list) or not items:
            sys.stderr.write("INVALID: add review items before freezing\n")
            return 1
        data["inventory"] = frozen_inventory(items)
        data["frozen_before_ledger"] = True
        args.manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        sys.stdout.write("PASS: review inventory frozen\n")
        return 0
    errors = validate(data)
    if errors:
        for error in errors:
            sys.stderr.write(f"INVALID: {error}\n")
        return 1
    sys.stdout.write("PASS: exhaustive review manifest is complete\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
