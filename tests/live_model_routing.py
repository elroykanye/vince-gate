#!/usr/bin/env python3
"""Live behavioral proof for the installed vince-route skill.

This is separate from unittest discovery because it invokes an authenticated Codex CLI.
Only synthetic tasks and synthetic profile identifiers are sent to the model.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], *, cwd: Path, timeout: int = 240) -> subprocess.CompletedProcess:
    print("$ " + subprocess.list2cmdline(command))
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.returncode != 0:
        if result.stderr.strip():
            print(result.stderr.strip(), file=sys.stderr)
        raise RuntimeError(f"command exited {result.returncode}")
    return result


def require(pattern: str, text: str, label: str) -> None:
    if not re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
        raise AssertionError(f"{label}: expected /{pattern}/ in captured response")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--codex", default="codex")
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix="vince-route-live-") as raw_project:
        project = Path(raw_project)
        os.environ["VINCE_STORE"] = str(project / ".vince-store")
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
        resolved = run(
            [
                sys.executable,
                str(ROOT / "scripts" / "install.py"),
                "where",
                "--repo",
                str(project),
                "--json",
            ],
            cwd=ROOT,
        )
        profile = Path(json.loads(resolved.stdout)["profile"])
        profile.parent.mkdir(parents=True)
        profile.write_text(
            """# Synthetic profile

## Model routing

| Harness | economy | balanced | frontier | reviewer | Status / verification command |
|---------|---------|----------|----------|----------|-------------------------------|
| codex | route-economy-exact | route-balanced-exact | route-frontier-exact | route-reviewer-exact | verified — synthetic fixture |

| Harness | explorer | worker | reviewer | Status / verification command |
|---------|----------|--------|----------|-------------------------------|
| codex | route-explorer-agent | route-worker-agent | route-reviewer-agent | verified — synthetic fixture |
""",
            encoding="utf-8",
        )

        output = project / "last-message.txt"
        prompt = (
            "Use $vince-route and the project profile. Evaluate each synthetic case independently. "
            "Return exactly one line per case in the form CASEn=STATUS|CLASS|MODEL|AGENT|WHY. "
            "CASE1: next phase only reformats one file deterministically; no subagent is useful. "
            "CASE2: next phase is an ordinary contained feature implementation; use the narrowest "
            "implementation role. CASE3: next phase designs a security-sensitive multi-service "
            "authentication migration. CASE4: next phase is fresh adversarial Vince review. "
            "CASE5: same trivial work as CASE1, but the known current model is route-frontier-exact; "
            "recommend rather than claim a switch and state the token/quality tradeoff. CASE6: "
            "same trivial work, but in this independent hypothetical profile snapshot the economy "
            "mapping is missing and unverified; do not silently substitute."
        )
        result = run(
            [
                args.codex,
                "exec",
                "--skip-git-repo-check",
                "-C",
                str(project),
                "--output-last-message",
                str(output),
                prompt,
            ],
            cwd=project,
        )
        if not output.is_file():
            raise AssertionError("Codex did not write --output-last-message")
        message = output.read_text(encoding="utf-8").strip()
        print("--- captured last message ---")
        print(message)
        require(r"CASE1=READY\|economy\|route-economy-exact\|none\|", message, "trivial route")
        require(r"CASE2=READY\|balanced\|route-balanced-exact\|worker\s*->\s*route-worker-agent\|", message, "standard route")
        require(r"CASE3=READY\|frontier\|route-frontier-exact\|", message, "security route")
        require(r"CASE4=READY\|reviewer\|route-reviewer-exact\|reviewer\s*->\s*route-reviewer-agent\|", message, "review route")
        require(r"CASE5=SWITCH\|economy\|route-economy-exact\|none\|.*token", message, "model downgrade")
        require(r"CASE6=ASK\|economy\|", message, "missing mapping")
        case6 = next(line for line in message.splitlines() if line.upper().startswith("CASE6="))
        if "route-balanced-exact" in case6 or "route-frontier-exact" in case6:
            raise AssertionError("missing mapping silently substituted another model")

    print("LIVE MODEL ROUTING: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"LIVE MODEL ROUTING: FAIL — {exc}", file=sys.stderr)
        raise SystemExit(1)
