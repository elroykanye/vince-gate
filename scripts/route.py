#!/usr/bin/env python3
"""Resolve exact Vince model and agent mappings from a project profile."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


MODEL_CLASSES = {"economy", "balanced", "frontier", "reviewer"}
AGENT_ROLES = {"none", "explorer", "worker", "reviewer"}


def cells(line: str) -> list[str]:
    return [part.strip() for part in line.strip().strip("|").split("|")]


def tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    lines = text.splitlines()
    found: list[tuple[list[str], list[list[str]]]] = []
    index = 0
    while index < len(lines):
        if not lines[index].lstrip().startswith("| Harness |"):
            index += 1
            continue
        header = [value.casefold() for value in cells(lines[index])]
        index += 2  # skip the Markdown separator row
        rows: list[list[str]] = []
        while index < len(lines) and lines[index].lstrip().startswith("|"):
            row = cells(lines[index])
            if len(row) == len(header):
                rows.append(row)
            index += 1
        found.append((header, rows))
    return found


def resolve(profile: Path, harness: str, model_class: str, role: str) -> dict:
    model = None
    agent = None if role == "none" else None
    reasons: list[str] = []
    model_verified = False
    agent_verified = role == "none"

    for header, rows in tables(profile.read_text(encoding="utf-8")):
        matching = next((row for row in rows if row[0].casefold() == harness.casefold()), None)
        if matching is None:
            continue
        record = dict(zip(header, matching))
        status = record.get("status / verification command", "").casefold()
        verified = status.startswith("verified") and "unverified" not in status
        if "economy" in header and model_class in header:
            model = record.get(model_class) or None
            model_verified = verified
        if role != "none" and role in header and "economy" not in header:
            agent = record.get(role) or None
            agent_verified = verified

    if not model:
        reasons.append(f"missing {model_class} model mapping")
    elif not model_verified:
        reasons.append(f"unverified {model_class} model mapping")
    if role != "none" and not agent:
        reasons.append(f"missing {role} agent mapping")
    elif role != "none" and not agent_verified:
        reasons.append(f"unverified {role} agent mapping")

    ready = not reasons
    return {
        "status": "READY" if ready else "ASK",
        "harness": harness,
        "class": model_class,
        "model": model if model_verified else None,
        "role": role,
        "agent": agent if agent_verified else None,
        "reason": "; ".join(reasons) if reasons else "exact verified mappings resolved",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--harness", required=True)
    parser.add_argument("--class", dest="model_class", required=True, choices=sorted(MODEL_CLASSES))
    parser.add_argument("--role", required=True, choices=sorted(AGENT_ROLES))
    args = parser.parse_args()
    decision = resolve(args.profile, args.harness, args.model_class, args.role)
    print(json.dumps(decision, sort_keys=True))
    return 0 if decision["status"] == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
