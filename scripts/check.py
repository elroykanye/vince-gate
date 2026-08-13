#!/usr/bin/env python3
"""Run the mechanical half of a Vince review as a script, not as model turns.

A large part of the reviewer's A1/A2/A5 passes is deterministic: grep the diff for skips, look
for attribution trailers, spot stray files, check the branch is not behind. Done by an agent that
is ~10 shell commands whose raw output all lands in context. Done here it is one compact report,
and it cannot be forgotten, mis-parsed or quietly skipped.

This does NOT replace the review. It replaces the boring part, so the model's context and
judgement go to the parts that need judgement: the blind pass, behaviour attacks, data isolation
and blast radius.

Usage:
    python scripts/check.py [--repo DIR] [--base REF] [--json]

Exit codes: 0 nothing found, 1 findings, 2 could not run (not a repo, bad base).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

TEST_HINT = re.compile(r"(^|/)(tests?|spec|__tests__)/|[._-](test|spec)\.[a-z]+$|Test\.[a-z]+$", re.I)
SKIP_MARKERS = re.compile(
    r"\.skip\b|\.only\b|\bxfail\b|\[Ignore\]|@pytest\.mark\.skip|\bt\.Skip\(|@Disabled|@Ignore",
    re.I)
DEBUG_MARKERS = {
    "js": re.compile(r"\bconsole\.(log|warn|debug)\s*\(|\bdebugger\b"),
    "py": re.compile(r"^\s*print\s*\(|\bbreakpoint\s*\(|\bpdb\.set_trace\b", re.M),
    "jvm": re.compile(r"System\.out\.print|printStackTrace\s*\("),
    "net": re.compile(r"Console\.Write|Debug\.Write"),
    "go": re.compile(r"fmt\.Print"),
}
SECRETS = re.compile(
    r"(?i)\b(api[_-]?key|secret|passwd|password|token|private[_-]?key)\b\s*[:=]\s*['\"][^'\"]{8,}",
)
STRAY = re.compile(
    r"(^|/)(\.serena|node_modules|\.venv|__pycache__|\.vince|\.superpowers|\.playwright-mcp)/"
    r"|(^|/)\.env$|\.(orig|rej|stackdump|pyc)$|(^|/)(nohup\.out|npm-debug\.log)$")
TRAILERS = re.compile(r"(?im)^\s*(co-authored-by:.*(claude|bot|copilot|cursor)|.*generated with.*)|🤖")


def git(repo: Path, args: list, ok_codes=(0,)):
    r = subprocess.run(["git", "-C", str(repo)] + args,
                       capture_output=True, text=True, errors="replace")
    return r.stdout if r.returncode in ok_codes else ""


def detect_base(repo: Path, explicit: str | None) -> str | None:
    if explicit:
        return explicit if git(repo, ["rev-parse", "--verify", explicit]) else None
    for cand in ("origin/main", "origin/master", "origin/dev", "origin/develop",
                 "main", "master"):
        if git(repo, ["rev-parse", "--verify", cand]).strip():
            head = git(repo, ["rev-parse", "HEAD"]).strip()
            if git(repo, ["rev-parse", cand]).strip() != head:
                return cand
    return None


def language_of(path: str) -> str | None:
    ext = Path(path).suffix.lower()
    if ext in (".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte"):
        return "js"
    if ext == ".py":
        return "py"
    if ext in (".java", ".kt", ".kts", ".scala"):
        return "jvm"
    if ext in (".cs", ".vb"):
        return "net"
    if ext == ".go":
        return "go"
    return None


def added_lines(repo: Path, base: str):
    """[(file, lineno, text)] for added lines only - the reviewer only cares about new code."""
    diff = git(repo, ["diff", "-U0", f"{base}...HEAD"])
    out, current, lineno = [], None, 0
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
        elif line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            lineno = int(m.group(1)) if m else 0
        elif line.startswith("+") and not line.startswith("+++") and current:
            out.append((current, lineno, line[1:]))
            lineno += 1
    return out


def run(repo: Path, base: str) -> dict:
    findings, facts = [], {}

    def add(sev, code, msg, where=""):
        findings.append({"severity": sev, "check": code, "detail": msg, "where": where})

    # --- state ------------------------------------------------------------
    dirty = [l for l in git(repo, ["status", "--porcelain"]).splitlines() if l.strip()]
    facts["uncommitted_files"] = len(dirty)
    if dirty:
        add("MEDIUM", "dirty-tree",
            f"{len(dirty)} uncommitted file(s) - proofs may depend on state that is not committed",
            "; ".join(d[3:] for d in dirty[:5]))

    behind = git(repo, ["rev-list", "--count", f"HEAD..{base}"]).strip() or "0"
    facts["commits_behind_base"] = int(behind)
    if behind != "0":
        add("MEDIUM", "behind-base", f"branch is {behind} commit(s) behind {base}")

    commits = [c for c in git(repo, ["log", "--format=%H", f"{base}..HEAD"]).splitlines() if c]
    facts["commits"] = len(commits)
    facts["base"] = base

    # --- commit hygiene ---------------------------------------------------
    bodies = git(repo, ["log", "--format=%B%x00", f"{base}..HEAD"]).split("\0")
    for body in bodies:
        for m in TRAILERS.finditer(body):
            add("MEDIUM", "ai-trailer", "AI/bot attribution trailer in a commit message",
                m.group(0).strip()[:70])
            break
    subjects = [s for s in git(repo, ["log", "--format=%s", f"{base}..HEAD"]).splitlines() if s]
    for s in subjects:
        if len(s) > 72:
            add("MINOR", "subject-length", f"commit subject is {len(s)} chars (>72)", s[:60] + "...")

    # --- files in the diff -------------------------------------------------
    changed = [f for f in git(repo, ["diff", "--name-only", f"{base}...HEAD"]).splitlines() if f]
    facts["files_changed"] = len(changed)
    facts["test_files_changed"] = sum(1 for f in changed if TEST_HINT.search(f))
    for f in changed:
        if STRAY.search(f):
            add("MEDIUM", "stray-artifact", "artifact that does not belong in history", f)

    # whole-file rewrites (the CRLF-flip shape): every line replaced
    for line in git(repo, ["diff", "--numstat", f"{base}...HEAD"]).splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
            addc, delc, path = int(parts[0]), int(parts[1]), parts[2]
            if addc > 30 and addc == delc:
                add("MEDIUM", "whole-file-rewrite",
                    f"{addc} added / {delc} removed - every line changed, likely a line-ending flip",
                    path)

    # --- added-line content ------------------------------------------------
    adds = added_lines(repo, base)
    facts["added_lines"] = len(adds)
    for path, ln, text in adds:
        if TEST_HINT.search(path) and SKIP_MARKERS.search(text):
            add("CRITICAL", "new-skip", "a skipped/disabled test was added", f"{path}:{ln}")
        lang = language_of(path)
        if lang and not TEST_HINT.search(path) and DEBUG_MARKERS[lang].search(text):
            add("MINOR", "debug-statement", "debug output left in non-test code", f"{path}:{ln}")
        if SECRETS.search(text):
            add("CRITICAL", "possible-secret", "possible hardcoded credential", f"{path}:{ln}")

    # --- test-shaped signals ----------------------------------------------
    if facts["files_changed"] and not facts["test_files_changed"]:
        add("MEDIUM", "no-test-files",
            "no test files in the diff - every AC needs a test that was seen to fail")
    return {"facts": facts, "findings": findings}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="check.py", description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--base", default=None, help="base ref (default: auto-detect)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    repo = Path(args.repo).expanduser().resolve()
    if not git(repo, ["rev-parse", "--git-dir"]):
        print(f"error: not a git repository: {repo}", file=sys.stderr)
        return 2
    base = detect_base(repo, args.base)
    if not base:
        print("error: could not determine a base ref; pass --base", file=sys.stderr)
        return 2

    result = run(repo, base)
    if args.json:
        print(json.dumps(result, indent=2))
        return 1 if result["findings"] else 0

    f = result["facts"]
    print(f"vince mechanical check - {repo.name} vs {f['base']}")
    print(f"  {f['commits']} commit(s), {f['files_changed']} file(s) changed "
          f"({f['test_files_changed']} test), {f['added_lines']} added line(s)")
    if not result["findings"]:
        print("\n  no mechanical findings. The judgement passes are still yours.")
        return 0

    order = {"CRITICAL": 0, "MEDIUM": 1, "MINOR": 2}
    print()
    for x in sorted(result["findings"], key=lambda x: order.get(x["severity"], 9)):
        where = f"  [{x['where']}]" if x["where"] else ""
        print(f"  {x['severity']:<8} {x['check']:<20} {x['detail']}{where}")
    print(f"\n  {len(result['findings'])} finding(s). These are mechanical only - they do not "
          "substitute for\n  the blind pass, behaviour attacks, isolation checks or blast radius.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
