#!/usr/bin/env python3
"""Rebuild a task's state from its ledger alone, and say whether that is even possible.

Vince's claim is that you can clear context mid-task and pick up from the ledger. This is the
thing that makes the claim checkable instead of aspirational: it reads only the files on disk -
no conversation, no memory - and prints what a fresh session needs to continue.

If it cannot produce that, the ledger is not self-sufficient and clearing would lose work. It
says so, and names what is missing, which is the useful half.

Usage:
    python scripts/resume.py --task <task dir>      # briefing for a fresh session
    python scripts/resume.py --task <dir> --check   # sufficiency only
    python scripts/resume.py --root <task root>     # pick the most recently touched active task

Exit codes: 0 sufficient, 1 gaps found, 2 no ledger.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROVEN = "PROVEN"
OPEN_STATUSES = ("NOT-PROVEN", "RED", "GREEN", "TAMPER-PASSED", "BLOCKED")


def find_task(root: Path) -> Path | None:
    active = root if (root / "verification-ledger.md").is_file() else root / "active"
    if not active.is_dir():
        return None
    best, newest = None, -1.0
    for led in active.glob("*/verification-ledger.md"):
        m = led.stat().st_mtime
        if m > newest:
            best, newest = led.parent, m
    return best


def header_value(text: str, label: str) -> str:
    m = re.search(rf"^\s*{re.escape(label)}\s*:\s*(.+)$", text, re.M | re.I)
    return m.group(1).strip() if m else ""


def contract_rows(text: str):
    rows = []
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not re.fullmatch(r"(AC|DOD)-\w+", cells[0], re.I):
            continue
        rows.append({"id": cells[0], "requirement": cells[1],
                     "command": cells[-2] if len(cells) >= 4 else "",
                     "status": cells[-1].upper()})
    return rows


def resources(text: str):
    out = []
    m = re.search(r"^##\s*Session resources(.+?)(^##\s|\Z)", text, re.M | re.S)
    if not m:
        return out
    for line in m.group(1).splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4 or cells[0].lower() in ("resource", "----------") or set(cells[0]) <= {"-"}:
            continue
        if cells[0].startswith("<"):
            continue
        out.append({"what": cells[0], "where": cells[1], "torn_down": cells[-1].lower()})
    return out


def analyse(task: Path) -> dict:
    led = task / "verification-ledger.md"
    text = led.read_text(encoding="utf-8", errors="replace")
    rows = contract_rows(text)
    res = resources(text)

    gaps = []
    repo = header_value(text, "Repo(s)") or header_value(text, "Profile")
    if not re.search(r"^\s*\|?\s*\d+\s*\|", text, re.M) and not header_value(text, "Repo(s)"):
        gaps.append("no repo/branch recorded - a fresh session will not know where to work")
    if not header_value(text, "Profile"):
        gaps.append("no profile path recorded - resolve it with `install.py where` and add it")
    if not rows:
        gaps.append("no contract rows - the acceptance criteria are not on disk at all")
    if not re.search(r"^##\s*Resume", text, re.M | re.I):
        gaps.append("no Resume block - add current phase and the single next action")
    for r in rows:
        if r["status"].startswith(OPEN_STATUSES) and not r["command"].strip(" `"):
            gaps.append(f"{r['id']} is {r['status']} with no proof command recorded")
    if not re.search(r"Baseline", text, re.I):
        gaps.append("no suite baseline recorded - new failures cannot be told from inherited ones")

    return {"task": task, "text": text, "rows": rows, "resources": res,
            "gaps": gaps, "repo": repo,
            "resume": (re.search(r"^##\s*Resume.*?\n(.+?)(^##\s|\Z)", text, re.M | re.S | re.I)
                       or [None, ""])[1] if re.search(r"^##\s*Resume", text, re.M | re.I) else ""}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="resume.py", description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--task", help="task directory containing verification-ledger.md")
    g.add_argument("--root", help="task root; picks the most recently touched active task")
    ap.add_argument("--check", action="store_true", help="sufficiency verdict only")
    args = ap.parse_args(argv)

    task = Path(args.task).expanduser().resolve() if args.task else \
        find_task(Path(args.root).expanduser().resolve())
    if not task or not (task / "verification-ledger.md").is_file():
        print("error: no verification-ledger.md found", file=sys.stderr)
        return 2

    a = analyse(task)
    rows, res, gaps = a["rows"], a["resources"], a["gaps"]
    done = [r for r in rows if r["status"].startswith(PROVEN)]
    open_ = [r for r in rows if not r["status"].startswith(PROVEN)]
    live = [r for r in res if r["torn_down"] not in ("yes", "y", "done", "removed")]

    if not args.check:
        print(f"RESUME BRIEFING - {task.name}")
        print(f"  ledger   : {task / 'verification-ledger.md'}")
        if a["repo"]:
            print(f"  context  : {a['repo']}")
        print(f"  progress : {len(done)}/{len(rows)} criteria PROVEN")
        verdict = header_value(a["text"], "Reviewer verdict")
        if verdict:
            print(f"  review   : {verdict}")
        if a["resume"].strip():
            print("\n  Resume block says:")
            for line in a["resume"].strip().splitlines()[:8]:
                print(f"    {line}")
        if open_:
            print("\n  Still open:")
            for r in open_[:12]:
                print(f"    {r['id']:<8} {r['status']:<14} {r['requirement'][:52]}")
                if r["command"].strip(" `"):
                    print(f"             proof: {r['command']}")
        if live:
            print("\n  Live resources to tear down before done:")
            for r in live:
                print(f"    {r['what']} - {r['where']}")
        for extra in ("implementation-status.md", "review-verdict.md",
                      "completion-documentation.md"):
            if (task / extra).is_file():
                print(f"  also on disk: {extra}")
        print()

    if gaps:
        print(f"NOT SAFE TO CLEAR - {len(gaps)} gap(s); this would be lost with the conversation:")
        for g_ in gaps:
            print(f"  - {g_}")
        print("\nFix the ledger first, then clear.")
        return 1

    print("SAFE TO CLEAR - the ledger carries everything needed to continue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
