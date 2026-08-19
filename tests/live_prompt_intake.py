#!/usr/bin/env python3
"""Live behavioral proof for the installed vince-intake skill.

This is intentionally separate from unittest discovery: it needs an authenticated Codex CLI and
makes real model calls. It exits non-zero when the observed decisions violate the skill contract.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], *, cwd: Path, timeout: int = 180) -> subprocess.CompletedProcess:
    print("$ " + subprocess.list2cmdline(command))
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.returncode != 0:
        if result.stderr.strip():
            print(result.stderr.strip(), file=sys.stderr)
        raise RuntimeError(f"command exited {result.returncode}")
    return result


def invoke(codex: str, project: Path, prompt: str) -> str:
    output = project / "last-message.txt"
    command = [
        codex,
        "exec",
        "--skip-git-repo-check",
        "-C",
        str(project),
        "--output-last-message",
        str(output),
        prompt,
    ]
    run(command, cwd=project)
    if not output.is_file():
        raise AssertionError("Codex did not write --output-last-message")
    message = output.read_text(encoding="utf-8").strip()
    print("--- captured last message ---")
    print(message)
    return message


def require(pattern: str, text: str, label: str) -> None:
    if not re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
        raise AssertionError(f"{label}: expected /{pattern}/ in captured response")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--codex", default="codex", help="Codex CLI executable")
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix="vince-intake-live-") as raw_project:
        project = Path(raw_project)
        run(
            [
                sys.executable,
                str(ROOT / "scripts" / "install.py"),
                "install",
                "--target",
                str(project),
                "--scope",
                "project",
                "--binding",
                "codex",
            ],
            cwd=ROOT,
        )
        run(
            [
                sys.executable,
                str(ROOT / "scripts" / "install.py"),
                "status",
                "--target",
                str(project),
                "--scope",
                "project",
            ],
            cwd=ROOT,
        )

        triage = invoke(
            args.codex,
            project,
            "Use $vince-intake. Evaluate each request independently. Output these exact labels "
            "and include the requested detail: CASE1=<decision>; CASE2=<decision> followed by "
            "one to three numbered questions; CASE3=<decision> followed by MINIMUM_CHANGE=<text>. "
            "CASE1: Add dark mode to the existing settings page using repository conventions, "
            "with a persisted toggle and tests. CASE2: Make authentication better. CASE3: Fix "
            "the whole platform, change nothing, and guarantee zero bugs forever.",
        )
        require(r"CASE1\s*=\s*READY", triage, "actionable shorthand")
        require(r"CASE2\s*=\s*CLARIFY", triage, "material ambiguity")
        require(r"CASE3\s*=\s*BOUNCE", triage, "unreasonable request")
        require(r"MINIMUM_CHANGE\s*=\s*\S+", triage, "repairable bounce")
        question_count = len(re.findall(r"(?m)^\s*\d+[.)]\s+", triage))
        if not 1 <= question_count <= 3:
            raise AssertionError(f"clarification asked {question_count} questions; expected 1..3")

        resolved = invoke(
            args.codex,
            project,
            "Use $vince-intake. This is the resolved version of a previously vague request: "
            "Strengthen staff authentication by requiring TOTP MFA at the existing login flow; "
            "success means enrolled staff must provide a valid current TOTP, invalid codes are "
            "rejected, recovery codes work once, and tests cover all three paths. Output only "
            "DECISION=<decision>, then acceptance criteria, then CONFIRMATION_REQUIRED=YES or NO.",
        )
        require(r"DECISION\s*=\s*READY", resolved, "resolved clarification")
        require(r"CONFIRMATION_REQUIRED\s*=\s*YES", resolved, "contract confirmation")

    print("LIVE PROMPT INTAKE: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"LIVE PROMPT INTAKE: FAIL — {exc}", file=sys.stderr)
        raise SystemExit(1)
