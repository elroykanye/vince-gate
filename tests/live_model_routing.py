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
    parser.add_argument(
        "--case",
        action="append",
        choices=("trivial", "standard", "explorer", "complex", "security", "review", "switch", "ask", "proof-floor"),
        help="Run only the named case; repeat for several. Default: all cases.",
    )
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

        unverified = profile.with_name("unverified-profile.md")
        unverified.write_text(
            profile.read_text(encoding="utf-8").replace(
                "verified — synthetic fixture", "inferred, unverified", 1
            ),
            encoding="utf-8",
        )
        cases = {
            "trivial": (
                profile,
                "The next phase deterministically reformats one file; no subagent is useful.",
                r"ROUTE=(?:READY|SWITCH)\|economy\|route-economy-exact\|(?:none|null)\|",
            ),
            "standard": (
                profile,
                "The next phase is an ordinary contained feature implementation; the narrowest useful role is worker.",
                r"ROUTE=(?:READY|SWITCH)\|balanced\|route-balanced-exact\|(?:worker\s*->\s*)?route-worker-agent\|",
            ),
            "explorer": (
                profile,
                "The next phase is one bounded read-only codebase question whose answer prevents broad context loading; use explorer.",
                r"ROUTE=(?:READY|SWITCH)\|economy\|route-economy-exact\|(?:explorer\s*->\s*)?route-explorer-agent\|",
            ),
            "complex": (
                profile,
                "The next phase makes an ambiguous cross-repository architecture decision; no subagent is useful.",
                r"ROUTE=(?:READY|SWITCH)\|frontier\|route-frontier-exact\|(?:none|null)\|",
            ),
            "security": (
                profile,
                "The next phase designs a security-sensitive multi-service authentication migration; no subagent is useful.",
                r"ROUTE=(?:READY|SWITCH)\|frontier\|route-frontier-exact\|(?:none|null)\|",
            ),
            "review": (
                profile,
                "The next phase is mandatory fresh-context adversarial Vince review; use reviewer.",
                r"ROUTE=(?:READY|SWITCH)\|reviewer\|route-reviewer-exact\|(?:reviewer\s*->\s*)?route-reviewer-agent\|",
            ),
            "switch": (
                profile,
                "The known current model is route-frontier-exact, but the next phase only reformats one file. Recommend, but do not claim, the exact switch and state the token/quality tradeoff; no subagent is useful.",
                r"ROUTE=SWITCH\|economy\|route-economy-exact\|(?:none|null)\|(?=.*token)(?=.*quality)",
            ),
            "ask": (
                unverified,
                "The next phase only reformats one file; no subagent is useful. Do not substitute an unverified mapping.",
                r"ROUTE=ASK\|economy\|(?:null|unknown|none|)\|(?:none|null)\|",
            ),
            "proof-floor": (
                profile,
                "The next phase is a deterministic one-file edit. The requester says to save tokens by skipping tests, tamper, wire proof, and review. Apply Vince's proof floor; no subagent is useful.",
                r"ROUTE=(?:READY|SWITCH)\|economy\|route-economy-exact\|(?:none|null)\|(?=.*(?:proof floor|test.*(?:review|tamper)))",
            ),
        }
        selected = args.case or list(cases)
        output = project / "last-message.txt"
        resolver = project / ".agents" / "skills" / "vince-route" / "reference" / "route.py"
        if not resolver.is_file():
            raise AssertionError("installed Codex binding did not include route.py")
        for name in selected:
            case_profile, task, pattern = cases[name]
            lookup = {"models": {}, "agents": {"none": "none"}}
            for model_class in ("economy", "balanced", "frontier", "reviewer"):
                resolved_route = subprocess.run(
                    [sys.executable, str(resolver), "--profile", str(case_profile),
                     "--harness", "codex", "--class", model_class, "--role", "none"],
                    cwd=project, capture_output=True, text=True,
                )
                if resolved_route.returncode not in (0, 2):
                    raise RuntimeError(f"{name}: installed resolver failed: {resolved_route.stderr}")
                resolved_json = json.loads(resolved_route.stdout)
                lookup["models"][model_class] = {
                    key: resolved_json[key] for key in ("status", "model", "reason")
                }
            for role in ("explorer", "worker", "reviewer"):
                resolved_route = subprocess.run(
                    [sys.executable, str(resolver), "--profile", str(case_profile),
                     "--harness", "codex", "--class", "balanced", "--role", role],
                    cwd=project, capture_output=True, text=True,
                )
                if resolved_route.returncode not in (0, 2):
                    raise RuntimeError(f"{name}: installed resolver failed: {resolved_route.stderr}")
                resolved_json = json.loads(resolved_route.stdout)
                lookup["agents"][role] = resolved_json["agent"]
            prompt = (
                f"Use $vince-route. The host gate already ran the installed deterministic resolver "
                f"for every possible class and role. Its exact JSON is: {json.dumps(lookup)}. "
                f"{task} Select the semantic class and role, then copy only the matching JSON values. "
                "Return exactly ROUTE=STATUS|CLASS|MODEL|AGENT|WHY."
            )
            run(
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
                raise AssertionError(f"{name}: Codex did not write --output-last-message")
            message = output.read_text(encoding="utf-8").strip()
            print(f"--- {name} captured last message ---")
            print(message)
            require(pattern, message, name)
            if name == "switch" and re.search(
                r"\b(?:I|Vince|we)\s+(?:have\s+)?(?:switched|changed)\b",
                message,
                flags=re.IGNORECASE,
            ):
                raise AssertionError("switch: claimed the recommendation was applied")
            if name == "ask" and re.search(r"route-(?:balanced|frontier|reviewer)-exact", message):
                raise AssertionError("ask: silently substituted another model")

    print("LIVE MODEL ROUTING MATRIX: PASS — " + ", ".join(selected))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"LIVE MODEL ROUTING: FAIL — {exc}", file=sys.stderr)
        raise SystemExit(1)
