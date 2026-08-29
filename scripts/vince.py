#!/usr/bin/env python3
"""Operational Vince helpers: health, routing refresh, release checks and archiving."""

from __future__ import annotations

import argparse
from datetime import date, datetime
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SKILLS = [
    "vince-cleanup", "vince-doctor", "vince-document", "vince-implement", "vince-intake",
    "vince-learn", "vince-review", "vince-route", "vince-setup", "vince-update",
]


def emit(text: str) -> None:
    sys.stdout.write(text + "\n")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def table_cells(line: str) -> list[str]:
    return [part.strip() for part in line.strip().strip("|").split("|")]


def routing_rows(profile: Path) -> list[dict[str, str]]:
    rows = []
    lines = read(profile).splitlines()
    i = 0
    while i < len(lines):
        if not lines[i].lstrip().startswith("| Harness |"):
            i += 1
            continue
        header = [cell.casefold() for cell in table_cells(lines[i])]
        i += 2
        while i < len(lines) and lines[i].lstrip().startswith("|"):
            cells = table_cells(lines[i])
            if len(cells) == len(header):
                rows.append(dict(zip(header, cells)))
            i += 1
    return rows


def stale(status: str, today: date, max_age_days: int) -> bool:
    match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", status)
    if not match:
        return True
    verified = datetime.strptime(match.group(1), "%Y-%m-%d").date()
    return (today - verified).days > max_age_days


def current_reviewer_verdict(ledger: str) -> str:
    for line in ledger.splitlines():
        match = re.match(r"\s*Reviewer verdict:\s*([A-Z-]+)", line)
        if match:
            return match.group(1)
    return "UNKNOWN"


def cmd_health(args) -> int:
    today = args.today or date.today()
    manifest = json.loads(read(args.manifest) or "{}")
    report = {"status": "OK", "bindings": {}, "tasks": [], "route_findings": [], "next_actions": []}

    for name, record in sorted(manifest.get("installs", {}).items()):
        root = Path(record.get("root", ""))
        verification = "live-verified" if name in {"claude", "codex", "generic"} else "render-only"
        report["bindings"][name] = {
            "version": record.get("version", "unknown"),
            "root": str(root),
            "verification": verification,
            "present": root.exists(),
        }
        if not root.exists():
            report["next_actions"].append(f"reinstall {name} binding")

    for task in sorted((args.task_root / "active").glob("*")) if (args.task_root / "active").is_dir() else []:
        if not task.is_dir():
            continue
        ledger = read(task / "verification-ledger.md")
        verdict = current_reviewer_verdict(ledger)
        next_action = ""
        match = re.search(r"Next action:\s*`?([^`\n]+)", ledger)
        if match:
            next_action = match.group(1).strip()
        report["tasks"].append({"task": task.name, "status": verdict, "next_action": next_action})
        if verdict != "PASS":
            report["next_actions"].append(f"continue task {task.name}: {next_action or 'inspect ledger'}")

    for row in routing_rows(args.profile):
        harness = row.get("harness", "unknown")
        status = row.get("status / verification command", "")
        for model_class in ("economy", "balanced", "frontier", "reviewer"):
            if model_class in row and not row[model_class]:
                report["route_findings"].append(f"{harness}: missing {model_class} model mapping")
        if "economy" in row and (not status.startswith("verified") or "unverified" in status or stale(status, today, args.max_age_days)):
            report["route_findings"].append(f"{harness}: refresh route mappings ({status or 'missing status'})")
        for role in ("explorer", "worker", "reviewer"):
            if role in row and not row[role]:
                report["route_findings"].append(f"{harness}: missing {role} agent mapping")

    if report["route_findings"]:
        report["next_actions"].append("refresh route mappings with explicit current inventory")
    if report["next_actions"] or report["route_findings"]:
        report["status"] = "ATTENTION"
    emit(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "OK" else 1


def replace_or_append_row(text: str, harness: str, values: list[str], has_model: bool) -> str:
    lines = text.splitlines()
    in_target = False
    new_row = "| " + " | ".join([harness, *values]) + " |"
    out = []
    replaced = False
    for line in lines:
        if line.lstrip().startswith("| Harness |"):
            header = [cell.casefold() for cell in table_cells(line)]
            in_target = ("economy" in header) == has_model
        elif in_target and line.lstrip().startswith("|") and table_cells(line)[0].casefold() == harness.casefold():
            out.append(new_row)
            replaced = True
            continue
        elif in_target and line and not line.lstrip().startswith("|"):
            if not replaced:
                out.append(new_row)
                replaced = True
            in_target = False
        out.append(line)
    if not replaced:
        out.append(new_row)
    return "\n".join(out) + "\n"


def cmd_route_refresh(args) -> int:
    missing = [name for name in (
        "economy", "balanced", "frontier", "reviewer",
        "explorer_agent", "worker_agent", "reviewer_agent",
    ) if not getattr(args, name)]
    if missing:
        emit("missing explicit values: " + ", ".join(missing))
        return 1
    status = f"verified {args.verified_date.isoformat()} - route-refresh"
    text = read(args.profile)
    text = replace_or_append_row(
        text, args.harness,
        [args.economy, args.balanced, args.frontier, args.reviewer, status],
        True,
    )
    text = replace_or_append_row(
        text, args.harness,
        [args.explorer_agent, args.worker_agent, args.reviewer_agent, status],
        False,
    )
    args.profile.write_text(text, encoding="utf-8")
    emit(f"refreshed {args.harness} route mappings in {args.profile}")
    return 0


def cmd_release_check(args) -> int:
    problems = []
    version = read(args.repo / "VERSION").strip()
    changelog = read(args.repo / "CHANGELOG.md")
    if version != args.expected_version:
        problems.append(f"VERSION is {version or 'missing'}, expected {args.expected_version}")
    heading_re = rf"(?m)^## v{re.escape(args.expected_version)}\b"
    if not re.search(heading_re, changelog):
        problems.append(f"missing changelog heading for v{args.expected_version}")
    if args.manifest and args.manifest.is_file():
        manifest = json.loads(read(args.manifest))
        for name, record in sorted(manifest.get("installs", {}).items()):
            if record.get("version") != args.expected_version:
                problems.append(f"{name} install is {record.get('version')}, expected {args.expected_version}")
    if not args.skip_git_tag:
        tag = subprocess.run(
            ["git", "-C", str(args.repo), "rev-parse", "-q", "--verify", f"refs/tags/{args.expected_tag}"],
            capture_output=True, text=True, check=False,
        )
        if tag.returncode != 0:
            problems.append(f"missing git tag {args.expected_tag}")
    result = {"status": "FAIL" if problems else "PASS", "problems": problems}
    emit(json.dumps(result, indent=2, sort_keys=True))
    return 1 if problems else 0


def cmd_codex_discovery(args) -> int:
    proof = {
        "probe": "codex-discovery",
        "codex": args.codex,
        "mode": "dry-run" if args.dry_run else "live",
        "expected_skills": SKILLS,
    }
    if args.dry_run:
        emit(json.dumps(proof, indent=2, sort_keys=True))
        return 0
    result = subprocess.run(
        [args.codex, "exec", "--json", "List the installed Vince skills by name only."],
        capture_output=True, text=True, check=False, timeout=args.timeout,
    )
    proof["returncode"] = result.returncode
    proof["stdout"] = result.stdout[-4000:]
    proof["stderr"] = result.stderr[-4000:]
    missing = [skill for skill in SKILLS if skill not in result.stdout]
    proof["missing"] = missing
    emit(json.dumps(proof, indent=2, sort_keys=True))
    return 0 if result.returncode == 0 and not missing else 1


def cmd_archive_task(args) -> int:
    active = args.task_root / "active" / args.task
    archive = args.task_root / "archive" / args.task
    ledger = read(active / "verification-ledger.md")
    if not active.is_dir():
        emit(f"task not found: {active}")
        return 1
    if current_reviewer_verdict(ledger) != "PASS":
        emit(f"refused: task {args.task} is not PASS")
        return 1
    if archive.exists():
        emit(f"refused: archive target already exists: {archive}")
        return 1
    archive.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(active), str(archive))
    emit(f"archived {args.task} -> {archive}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    health = sub.add_parser("health")
    health.add_argument("--profile", required=True, type=Path)
    health.add_argument("--manifest", required=True, type=Path)
    health.add_argument("--task-root", required=True, type=Path)
    health.add_argument("--today", type=date.fromisoformat)
    health.add_argument("--max-age-days", type=int, default=30)
    health.set_defaults(func=cmd_health)

    refresh = sub.add_parser("route-refresh")
    refresh.add_argument("--profile", required=True, type=Path)
    refresh.add_argument("--harness", required=True)
    for name in ("economy", "balanced", "frontier", "reviewer"):
        refresh.add_argument(f"--{name}", required=True)
    refresh.add_argument("--explorer-agent", required=True)
    refresh.add_argument("--worker-agent", required=True)
    refresh.add_argument("--reviewer-agent", required=True)
    refresh.add_argument("--verified-date", type=date.fromisoformat, default=date.today())
    refresh.set_defaults(func=cmd_route_refresh)

    release = sub.add_parser("release-check")
    release.add_argument("--repo", required=True, type=Path)
    release.add_argument("--expected-version", required=True)
    release.add_argument("--expected-tag", required=True)
    release.add_argument("--manifest", type=Path)
    release.add_argument("--skip-git-tag", action="store_true")
    release.set_defaults(func=cmd_release_check)

    codex = sub.add_parser("codex-discovery")
    codex.add_argument("--codex", default="codex")
    codex.add_argument("--dry-run", action="store_true")
    codex.add_argument("--timeout", type=int, default=120)
    codex.set_defaults(func=cmd_codex_discovery)

    archive = sub.add_parser("archive-task")
    archive.add_argument("--task-root", required=True, type=Path)
    archive.add_argument("--task", required=True)
    archive.set_defaults(func=cmd_archive_task)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
