#!/usr/bin/env python3
"""Live behavioral proof for the installed vince-intake skill.

This is intentionally separate from unittest discovery: it needs an authenticated Codex CLI and
makes real model calls. It exits non-zero when the observed decisions violate the skill contract.
"""

from __future__ import annotations

import argparse
import json
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


def thread_id_from_jsonl(output: str) -> str:
    for line in output.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "thread.started" and event.get("thread_id"):
            return str(event["thread_id"])
        for key in ("thread_id", "session_id"):
            if event.get(key):
                return str(event[key])
    raise AssertionError("Codex JSON output did not contain a thread/session id")


def invoke(codex: str, project: Path, prompt: str) -> tuple[str, str]:
    output = project / "last-message.txt"
    command = [
        codex,
        "exec",
        "--json",
        "--skip-git-repo-check",
        "-C",
        str(project),
        "--output-last-message",
        str(output),
        prompt,
    ]
    result = run(command, cwd=project)
    if not output.is_file():
        raise AssertionError("Codex did not write --output-last-message")
    message = output.read_text(encoding="utf-8").strip()
    print("--- captured last message ---")
    print(message)
    return message, thread_id_from_jsonl(result.stdout)


def resume(codex: str, project: Path, thread_id: str, prompt: str) -> str:
    output = project / "last-message.txt"
    command = [
        codex,
        "exec",
        "resume",
        "--skip-git-repo-check",
        "--json",
        "--output-last-message",
        str(output),
        thread_id,
        prompt,
    ]
    run(command, cwd=project)
    if not output.is_file():
        raise AssertionError("Codex resume did not write --output-last-message")
    message = output.read_text(encoding="utf-8").strip()
    print("--- captured resumed message ---")
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

        triage, thread_id = invoke(
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

        partial = resume(
            args.codex,
            project,
            thread_id,
            "For CASE2, my follow-up answers are: improve security; staff users and the existing "
            "login flow are in scope. I have not yet defined the observable success result. "
            "Continue the same vince-intake clarification. Output DECISION=<decision> and only "
            "the remaining numbered questions.",
        )
        require(r"DECISION\s*=\s*CLARIFY", partial, "continued clarification")
        partial_questions = len(re.findall(r"(?m)^\s*\d+[.)]\s+", partial))
        if not 1 <= partial_questions <= 3:
            raise AssertionError(
                f"continued clarification asked {partial_questions} questions; expected 1..3"
            )

        resolved = resume(
            args.codex,
            project,
            thread_id,
            "My remaining answer is: success means enrolled staff must provide a valid current "
            "TOTP; invalid codes are rejected; recovery codes work once; tests cover all three "
            "paths. Continue the same intake conversation. Output DECISION=<decision>, then the "
            "resolved acceptance criteria, then CONFIRMATION_REQUIRED=YES or NO.",
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
