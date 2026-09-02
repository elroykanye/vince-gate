#!/usr/bin/env python3
"""Freeze and validate an exhaustive Vince review plan and its results."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

TERMINAL = {"PROVEN", "FINDING", "BLOCKED", "UNREVIEWED"}
KINDS = {"acceptance", "definition-of-done", "material-claim", "entry-point", "dependent"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def strings(value: object, *, empty: bool = False) -> bool:
    return isinstance(value, list) and (empty or bool(value)) and all(
        isinstance(item, str) and len(item.strip()) >= 3 for item in value
    )


def records(value: object, fields: tuple[str, str]) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(record, dict) and all(
            isinstance(record.get(field), str) and len(record[field].strip()) >= 3
            for field in fields
        ) for record in value
    )


def frozen_plan(data: dict[str, object]) -> dict[str, object]:
    items = data.get("items")
    passes = data.get("attack_passes")
    normalized = []
    counts = {kind: 0 for kind in sorted(KINDS)}
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                normalized.append(item)
                continue
            kind = item.get("kind")
            if kind in counts:
                counts[kind] += 1
            normalized.append({field: item.get(field) for field in (
                "id", "kind", "claim", "source", "proof_plan", "attack_plan"
            )})
    pass_plans = ({
        name: attack.get("plan") if isinstance(attack, dict) else None
        for name, attack in sorted(passes.items())
    } if isinstance(passes, dict) else passes)
    sealed = {
        "task": data.get("task"), "review_id": data.get("review_id"), "items": normalized,
        "attack_passes": pass_plans, "previous_findings": data.get("previous_findings"),
        "adjacent_variants": data.get("adjacent_variants"),
        "untouched_surfaces": data.get("untouched_surfaces"),
    }
    payload = json.dumps(sealed, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {"item_count": len(items) if isinstance(items, list) else 0, "kind_counts": counts,
            "plan_sha256": hashlib.sha256(payload.encode()).hexdigest()}


def validate(data: object) -> list[str]:
    if not isinstance(data, dict):
        return ["manifest must be a JSON object"]
    errors = []
    for field in ("task", "review_id"):
        if not isinstance(data.get(field), str) or len(data[field].strip()) < 3:
            errors.append(f"{field} must be a non-empty identifying string")
    for flag, expected in (("frozen_before_ledger", True), ("discovery_complete", True), ("early_exit", False)):
        if data.get(flag) is not expected:
            errors.append(f"{flag} must be {str(expected).lower()}")
    items = data.get("items")
    if not isinstance(items, list) or not items:
        errors.append("items must be a non-empty list")
        items = []
    expected = frozen_plan(data)
    if data.get("inventory") != expected:
        errors.append("inventory must match the frozen review plan and SHA-256")
    if expected["kind_counts"]["acceptance"] < 1:
        errors.append("inventory must include at least one acceptance item")
    if expected["kind_counts"]["material-claim"] < 1:
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
        for field in ("proof_plan", "attack_plan"):
            if not strings(item.get(field)):
                errors.append(f"{label}.{field} must be planned before freeze")
        status = item.get("status")
        if status not in TERMINAL:
            errors.append(f"{label}.status must be terminal")
        if not records(item.get("evidence"), ("command", "result")):
            errors.append(f"{label}.evidence must contain command/result records")
        if status in {"PROVEN", "FINDING"} and not records(item.get("attacks"), ("attack", "result")):
            errors.append(f"{label}.attacks must contain attack/result records")
    passes = data.get("attack_passes")
    if not isinstance(passes, dict):
        errors.append("attack_passes must contain A0 through A7")
        passes = {}
    for name in (f"A{i}" for i in range(8)):
        attack = passes.get(name)
        if not isinstance(attack, dict):
            errors.append(f"attack_passes.{name} must be an object")
            continue
        if not strings(attack.get("plan")):
            errors.append(f"attack_passes.{name}.plan must be frozen before review")
        if attack.get("status") not in TERMINAL:
            errors.append(f"attack_passes.{name} must have a terminal status")
        if not records(attack.get("evidence"), ("command", "result")):
            errors.append(f"attack_passes.{name}.evidence must contain command/result records")
    for field in ("previous_findings", "adjacent_variants", "untouched_surfaces"):
        if not strings(data.get(field), empty=field != "untouched_surfaces"):
            errors.append(f"{field} must be a planned list of non-blank strings")
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
        if not isinstance(data, dict):
            sys.stderr.write("INVALID: manifest must be a JSON object\n")
            return 1
        inventory = data.get("inventory")
        if isinstance(inventory, dict) and SHA256.fullmatch(str(inventory.get("plan_sha256", ""))):
            sys.stderr.write("INVALID: review plan is already frozen; create a new review_id and manifest\n")
            return 1
        if not isinstance(data.get("items"), list) or not data["items"]:
            sys.stderr.write("INVALID: add review items before freezing\n")
            return 1
        data["inventory"] = frozen_plan(data)
        data["frozen_before_ledger"] = True
        args.manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        sys.stdout.write("PASS: review plan frozen\n")
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
