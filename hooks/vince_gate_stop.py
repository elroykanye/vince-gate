#!/usr/bin/env python3
"""Claude Code/Codex Stop hook: refuse to end while active work is unproven.

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

Scope: ledgers in the project's in-repo .vince directory or its external Vince store are
considered, and only those touched recently (VINCE_STOP_MAX_AGE_HOURS, default 24) - an old
abandoned ledger must not hold a session hostage forever. If nothing matches, the hook exits 0.

Environment:
    VINCE_STOP_MAX_AGE_HOURS   how recent a ledger must be to count (default 24)
    VINCE_STOP_DISABLE=1       turn the hook off without editing settings
"""

from __future__ import annotations

import json
import os
import re
import subprocess
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


def normalise_remote(url: str) -> str:
    """Match scripts/install.py's stable remote-derived repository key."""
    url = url.strip().rstrip("/")
    url = re.sub(r"^[a-z+]+://", "", url, flags=re.I)
    url = re.sub(r"^[^/@]+@", "", url)
    if url.endswith(".git"):
        url = url[:-4]
    url = url.replace(":", "/")
    return "__".join(p for p in re.split(r"[/\\]", url) if p).lower()


def repo_key(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return normalise_remote(result.stdout) if result.returncode == 0 else ""


def active_dirs(root: Path):
    """Return the in-repo and external-store active task directories for this repo."""
    out = [root / ".vince" / "tasks" / "active"]
    key = repo_key(root)
    if key:
        store = Path(os.environ.get("VINCE_STORE", Path.home() / ".vince")).expanduser()
        out.append(store / "repos" / key / "tasks" / "active")
    return out


def recent_ledgers(root: Path):
    cutoff = time.time() - MAX_AGE_HOURS * 3600
    out = []
    seen = set()
    for active in active_dirs(root):
        if not active.is_dir():
            continue
        for ledger in active.glob("*/verification-ledger.md"):
            try:
                resolved = ledger.resolve()
                if resolved not in seen and ledger.stat().st_mtime >= cutoff:
                    seen.add(resolved)
                    out.append(ledger)
            except OSError:
                continue
    return out


def leaked_worktrees(text: str):
    """Paths the ledger recorded as worktrees that still exist on disk.

    Only meaningful once the task has passed: before that the worktree is supposed to be there.
    Conservative by design - a path that no longer exists, or that cannot be parsed, is not a leak.
    """
    out = []
    for m in re.finditer(r"^\s*(?:\|\s*)?worktree\b[^|\n]*\|?\s*`([^`]+)`", text, re.M | re.I):
        candidate = m.group(1).strip()
        if candidate and not candidate.startswith("<") and Path(candidate).is_dir():
            out.append(candidate)
    return out


def inspect(ledger: Path):
    """Return (unproven_ids, verdict, leaked) for one ledger."""
    try:
        text = ledger.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [], None, []

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
    return unproven, verdict, leaked_worktrees(text)


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

    problems, leaks = [], []
    for ledger in recent_ledgers(project_root(payload)):
        unproven, verdict, worktrees = inspect(ledger)
        task = ledger.parent.name
        if unproven:
            problems.append(f"  {task}: {len(unproven)} row(s) not PROVEN - {', '.join(unproven[:4])}")
        if verdict in (None, "NOT-RUN"):
            problems.append(f"  {task}: reviewer verdict is {verdict or 'absent'}")
        elif verdict == "FAIL":
            problems.append(f"  {task}: reviewer verdict is FAIL")
        elif verdict == "PASS":
            # Passed and finished, but a worktree it recorded is still on disk: teardown was
            # skipped. Cheap to catch now, tedious to track down weeks later.
            for wt in worktrees:
                leaks.append(f"  {task}: worktree still on disk - {wt}")

    if not problems and not leaks:
        return 0

    lines = ["vince-gate: this session is not finished."]
    if problems:
        lines += ["", "Not done:"] + problems
        lines += ["", "Finish the ledger and get a PASS from vince-review, or tell the user "
                      "plainly what is unproven and why you are stopping."]
    if leaks:
        lines += ["", "Not cleaned up:"] + leaks
        lines += ["", "Tear it down (`git -C <repo> worktree remove <path>` then `prune`) and "
                      "mark it torn down in the ledger's Session resources block. If it refuses "
                      "because the tree is dirty or has unpushed commits, that is a STOP - "
                      "report it, do not force. Stuck because something is holding the "
                      "directory open? That is vince-cleanup."]
    print("\n".join(lines), file=sys.stderr)
    return 2  # exit 2 blocks the stop and feeds stderr back to the model


if __name__ == "__main__":
    sys.exit(main())
