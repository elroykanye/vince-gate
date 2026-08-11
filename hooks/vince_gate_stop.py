#!/usr/bin/env python3
"""Stop hook: refuse to let a session end while the active ledger says the work is unproven.

Vince's prime directive is "no done without a PASS verdict". As a skill instruction, a model
can forget it. As a Stop hook, it is enforced: exit code 2 blocks the stop and returns stderr
to the model as feedback.

Wire it up in .claude/settings.json (project) or ~/.claude/settings.json (user):

    {
      "hooks": {
        "Stop": [
          {
            "hooks": [
              { "type": "command",
                "command": "python /abs/path/to/vince-gate/hooks/vince_gate_stop.py" }
            ]
          }
        ]
      }
    }

Scope: only ledgers under <project>/.vince/tasks/active/ are considered, and only those touched
recently (VINCE_STOP_MAX_AGE_HOURS, default 24) - an old abandoned ledger must not hold a
session hostage forever. If nothing matches, the hook exits 0 and stays out of the way.

Environment:
    VINCE_STOP_MAX_AGE_HOURS   how recent a ledger must be to count (default 24)
    VINCE_STOP_DISABLE=1       turn the hook off without editing settings
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

MAX_AGE_HOURS = float(os.environ.get("VINCE_STOP_MAX_AGE_HOURS", "24"))
BLOCKING_STATUSES = ("NOT-PROVEN", "RED", "GREEN", "TAMPER-PASSED")


def project_root(payload: dict) -> Path:
    for key in ("cwd", "project_dir", "workspace_dir"):
        value = payload.get(key)
        if value and Path(value).is_dir():
            return Path(value)
    return Path.cwd()


def recent_ledgers(root: Path):
    active = root / ".vince" / "tasks" / "active"
    if not active.is_dir():
        return []
    cutoff = time.time() - MAX_AGE_HOURS * 3600
    out = []
    for ledger in active.glob("*/verification-ledger.md"):
        try:
            if ledger.stat().st_mtime >= cutoff:
                out.append(ledger)
        except OSError:
            continue
    return out


def inspect(ledger: Path):
    """Return (unproven_ids, verdict) for one ledger."""
    try:
        text = ledger.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [], None

    verdict = None
    m = re.search(r"^Reviewer[ -]verdict:\s*(NOT-RUN|FAIL|PASS)", text, re.M | re.I)
    if m:
        verdict = m.group(1).upper()

    unproven = []
    # Contract rows look like: | AC-1 | ... | E2E-WIRE | `cmd` | PROVEN |
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        row_id, status = cells[0], cells[-1]
        if not re.fullmatch(r"(AC|DOD)-\w+", row_id, re.I):
            continue
        if status.upper().startswith(BLOCKING_STATUSES):
            unproven.append(f"{row_id} ({status})")
    return unproven, verdict


def main() -> int:
    if os.environ.get("VINCE_STOP_DISABLE") == "1":
        return 0
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    # Never re-block a stop that was already blocked once - that is how a session deadlocks.
    if payload.get("stop_hook_active"):
        return 0

    problems = []
    for ledger in recent_ledgers(project_root(payload)):
        unproven, verdict = inspect(ledger)
        task = ledger.parent.name
        if unproven:
            problems.append(f"  {task}: {len(unproven)} row(s) not PROVEN - {', '.join(unproven[:4])}")
        if verdict in (None, "NOT-RUN"):
            problems.append(f"  {task}: reviewer verdict is {verdict or 'absent'}")
        elif verdict == "FAIL":
            problems.append(f"  {task}: reviewer verdict is FAIL")

    if not problems:
        return 0

    print(
        "vince-gate: this task is not done yet.\n"
        + "\n".join(problems)
        + "\n\nFinish the ledger and get a PASS from vince-review, or tell the user plainly "
          "what is unproven and why you are stopping. Do not report the task complete.",
        file=sys.stderr,
    )
    return 2  # exit 2 blocks the stop and feeds stderr back to the model


if __name__ == "__main__":
    sys.exit(main())
