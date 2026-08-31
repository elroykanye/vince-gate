#!/usr/bin/env python3
"""Operational Vince helpers: health, routing refresh, release checks and archiving."""

from __future__ import annotations

import argparse
from datetime import date, datetime
import hashlib
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


SKILL_SCAN_RULES = [
    {
        "id": "prompt-injection.ignore-previous",
        "category": "prompt-injection",
        "severity": "critical",
        "pattern": re.compile(r"\bignore (all )?(previous|prior|above) instructions\b", re.I),
        "message": "Skill attempts to override higher-priority instructions.",
    },
    {
        "id": "data-exfiltration.secrets-to-url",
        "category": "data-exfiltration",
        "severity": "critical",
        "pattern": re.compile(
            r"\b(?:send|post|upload|exfiltrate)\b(?=.{0,220}\b(?:secret|token|credential|api[_ -]?key)s?\b)(?=.{0,220}https?://).{0,240}",
            re.I,
        ),
        "message": "Skill instructs the agent to send secrets to a network endpoint.",
    },
    {
        "id": "destructive-command.rm-home",
        "category": "destructive-command",
        "severity": "critical",
        "pattern": re.compile(r"\brm\s+-[^\n]*r[^\n]*f[^\n]*(?:\$HOME|~|/)\b", re.I),
        "message": "Skill contains a broad recursive delete command.",
    },
    {
        "id": "privilege-escalation.sudo",
        "category": "privilege-escalation",
        "severity": "high",
        "pattern": re.compile(r"\bsudo\b|\brunas\b|\bset-executionpolicy\b", re.I),
        "message": "Skill asks for elevated local privileges.",
    },
    {
        "id": "hidden-network.download-execute",
        "category": "hidden-network",
        "severity": "high",
        "pattern": re.compile(r"\b(curl|wget|Invoke-WebRequest|iwr)\b.{0,160}\|\s*(sh|bash|pwsh|powershell|python)", re.I),
        "message": "Skill downloads remote content and pipes it into an interpreter.",
    },
    {
        "id": "tool-misuse.bypass-approval",
        "category": "unsafe-tool-instruction",
        "severity": "high",
        "pattern": re.compile(r"\b(bypass|disable|ignore)\b.{0,80}\b(approval|sandbox|permission|safety)\b", re.I),
        "message": "Skill tells the agent to bypass tool safety controls.",
    },
    {
        "id": "mcp-permission.wildcard",
        "category": "suspicious-mcp-permission",
        "severity": "medium",
        "pattern": re.compile(r"\bmcp\b.{0,120}(\*|all permissions|full access|admin)", re.I),
        "message": "Skill appears to request broad MCP/plugin permissions.",
    },
]


def finding_fingerprint(skill: str, rel: str, rule_id: str, line_no: int, line: str) -> str:
    raw = "\0".join([skill, rel, rule_id, str(line_no), line.strip()])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def iter_skill_files(skills_root: Path):
    for skill_dir in sorted(skills_root.iterdir()) if skills_root.is_dir() else []:
        if not skill_dir.is_dir() or skill_dir.name.startswith("_"):
            continue
        for path in sorted(skill_dir.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".md", ".toml", ".json", ".yaml", ".yml", ".py", ".sh", ".ps1"}:
                yield skill_dir.name, path


def vince_static_skill_scan(skills_root: Path) -> dict:
    findings = []
    for skill, path in iter_skill_files(skills_root):
        text = read(path)
        rel = path.relative_to(skills_root).as_posix()
        for line_no, line in enumerate(text.splitlines(), start=1):
            for rule in SKILL_SCAN_RULES:
                if rule["pattern"].search(line):
                    findings.append({
                        "severity": rule["severity"],
                        "category": rule["category"],
                        "message": rule["message"],
                        "skill": skill,
                        "file": rel,
                        "line": line_no,
                        "rule": rule["id"],
                        "fingerprint": finding_fingerprint(skill, rel, rule["id"], line_no, line),
                    })
    return {
        "engine": "vince-static",
        "status": "FAIL" if findings else "PASS",
        "risk_score": 100 if any(f["severity"] == "critical" for f in findings) else (60 if findings else 0),
        "findings": findings,
        "suppressed": [],
    }


def accepted_fingerprints(path: Path | None) -> set[str]:
    if not path or not path.is_file():
        return set()
    data = json.loads(read(path))
    accepted = data.get("accepted", data if isinstance(data, list) else [])
    return set(str(item) for item in accepted)


def normalize_external_report(text: str) -> dict:
    data = json.loads(text)
    findings = data.get("findings", [])
    for finding in findings:
        finding.setdefault("skill", Path(finding.get("file", "")).parts[0] if finding.get("file") else "unknown")
        finding.setdefault("fingerprint", hashlib.sha256(json.dumps(finding, sort_keys=True).encode("utf-8")).hexdigest()[:16])
    data["engine"] = "skillspector"
    data["findings"] = findings
    data["suppressed"] = data.get("suppressed", [])
    data["status"] = "FAIL" if findings or str(data.get("status", "")).upper() == "FAIL" else "PASS"
    data.setdefault("risk_score", 100 if findings else 0)
    return data


def run_external_skillspector(skills_root: Path, timeout: int) -> dict | None:
    exe = shutil.which("skillspector")
    if not exe:
        return None
    result = subprocess.run(
        [exe, "scan", str(skills_root), "--format", "json"],
        capture_output=True, text=True, check=False, timeout=timeout,
    )
    if not result.stdout.strip():
        return {
            "engine": "skillspector",
            "status": "FAIL",
            "risk_score": 100,
            "findings": [{
                "severity": "critical",
                "category": "scanner-failure",
                "message": result.stderr.strip() or f"skillspector exited {result.returncode} without JSON output",
                "skill": "unknown",
                "file": str(skills_root),
                "line": 0,
                "fingerprint": hashlib.sha256(result.stderr.encode("utf-8")).hexdigest()[:16],
            }],
            "suppressed": [],
        }
    try:
        report = normalize_external_report(result.stdout)
    except json.JSONDecodeError:
        return {
            "engine": "skillspector",
            "status": "FAIL",
            "risk_score": 100,
            "findings": [{
                "severity": "critical",
                "category": "scanner-failure",
                "message": "skillspector returned malformed JSON output",
                "skill": "unknown",
                "file": str(skills_root),
                "line": 0,
                "fingerprint": hashlib.sha256(result.stdout.encode("utf-8")).hexdigest()[:16],
            }],
            "suppressed": [],
        }
    if result.returncode != 0 and not report["findings"]:
        report["status"] = "FAIL"
        report["findings"].append({
            "severity": "critical",
            "category": "scanner-failure",
            "message": result.stderr.strip() or f"skillspector exited {result.returncode}",
            "skill": "unknown",
            "file": str(skills_root),
            "line": 0,
            "fingerprint": hashlib.sha256(result.stderr.encode("utf-8")).hexdigest()[:16],
        })
    return report


def apply_skill_scan_baseline(report: dict, baseline: Path | None) -> dict:
    accepted = accepted_fingerprints(baseline)
    if not accepted:
        return report
    active = []
    suppressed = list(report.get("suppressed", []))
    for finding in report.get("findings", []):
        if finding.get("fingerprint") in accepted:
            suppressed.append(finding)
        else:
            active.append(finding)
    report["findings"] = active
    report["suppressed"] = suppressed
    report["status"] = "FAIL" if active else "PASS"
    report["risk_score"] = 100 if any(f.get("severity") == "critical" for f in active) else (60 if active else 0)
    return report


def cmd_skill_scan(args) -> int:
    report = None if args.no_external else run_external_skillspector(args.skills, args.timeout)
    if report is None:
        report = vince_static_skill_scan(args.skills)
    report = apply_skill_scan_baseline(report, args.baseline)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.format == "json":
        emit(json.dumps(report, indent=2, sort_keys=True))
    else:
        emit(f"{report['engine']} skill scan: {report['status']} ({len(report['findings'])} finding(s), {len(report.get('suppressed', []))} suppressed)")
        for finding in report["findings"]:
            emit(f"{finding['severity'].upper()} {finding['category']} {finding['file']}:{finding.get('line', 0)} {finding['message']}")
    return 1 if report["status"] == "FAIL" else 0


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

    scan = sub.add_parser("skill-scan")
    scan.add_argument("--skills", required=True, type=Path)
    scan.add_argument("--baseline", type=Path)
    scan.add_argument("--format", choices=("json", "terminal"), default="json")
    scan.add_argument("--output", type=Path)
    scan.add_argument("--no-external", action="store_true")
    scan.add_argument("--timeout", type=int, default=120)
    scan.set_defaults(func=cmd_skill_scan)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
