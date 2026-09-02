#!/usr/bin/env python3
"""Score a real Vince review against the planted-defect corpus.

Deliberately outside unittest discovery: scoring a review means a review has to have happened,
which costs a model run. What this does NOT do is drive the reviewer — the harness varies, and a
runner that shelled out to one CLI would rot. Produce the review however you normally do, then
point this at its two artifacts.

    python tests/live_reviewer_corpus.py --case C1-no-early-exit \\
        --manifest /path/to/review-coverage.json \\
        --verdict  /path/to/review-verdict.md

    python tests/live_reviewer_corpus.py --all --results-dir /path/to/results

For --all, `results-dir` holds one subdirectory per case id, each containing
`review-coverage.json` and `review-verdict.md`. A missing case scores as FAILED, not as skipped:
a corpus that quietly shrinks to the cases someone remembered to run measures nothing.

Exit codes: 0 every scored case passed, 1 at least one failed, 2 the invocation was wrong.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tests" / "fixtures" / "reviewer_corpus.json"
VALIDATOR = ROOT / "scripts" / "review_manifest.py"


def load_corpus() -> dict:
    return json.loads(CORPUS.read_text(encoding="utf-8"))


def verdict_is_fail(verdict_text: str) -> bool:
    """The corpus only contains defective work, so any PASS is a miss."""
    head = "\n".join(verdict_text.splitlines()[:40])
    if re.search(r"(?im)^\s*(#\s*Review verdict:|\*\*Current:)\s*.*\bFAIL\b", head):
        return True
    return not re.search(r"(?im)^\s*(#\s*Review verdict:|\*\*Current:)\s*.*\bPASS\b", head)


def manifest_validates(manifest_path: Path) -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "validate", str(manifest_path)],
        capture_output=True, text=True,
    )
    return result.returncode == 0, (result.stderr or result.stdout).strip()


def score(case: dict, manifest_path: Path, verdict_path: Path) -> tuple[bool, list[str]]:
    problems: list[str] = []

    if not manifest_path.is_file():
        problems.append(f"no manifest at {manifest_path}")
    if not verdict_path.is_file():
        problems.append(f"no verdict at {verdict_path}")
    if problems:
        return False, problems

    valid, detail = manifest_validates(manifest_path)
    if not valid:
        problems.append(f"manifest does not validate: {detail}")

    verdict_text = verdict_path.read_text(encoding="utf-8", errors="replace")
    if not verdict_is_fail(verdict_text):
        problems.append(f"verdict is not FAIL, but {case['id']} contains a planted defect")

    # Signals may be satisfied by either artifact: some findings live in the manifest rows, some
    # only in the verdict's prose. Requiring a specific home would score formatting, not detection.
    haystack = verdict_text + "\n" + manifest_path.read_text(encoding="utf-8", errors="replace")
    for pattern in case["required_signals"]:
        if not re.search(pattern, haystack):
            problems.append(f"missed signal: {pattern}")

    return not problems, problems


def report(case_id: str, passed: bool, problems: list[str]) -> None:
    print(f"{'PASS' if passed else 'FAIL'}  {case_id}")
    for problem in problems:
        print(f"        {problem}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", help="corpus case id")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--verdict", type=Path)
    parser.add_argument("--all", action="store_true", help="score every case in the corpus")
    parser.add_argument("--results-dir", type=Path, help="one subdirectory per case id")
    args = parser.parse_args()

    corpus = load_corpus()
    by_id = {case["id"]: case for case in corpus["cases"]}

    if args.all:
        if not args.results_dir:
            parser.error("--all needs --results-dir")
        failures = 0
        for case_id, case in by_id.items():
            directory = args.results_dir / case_id
            passed, problems = score(
                case, directory / "review-coverage.json", directory / "review-verdict.md"
            )
            report(case_id, passed, problems)
            failures += 0 if passed else 1
        print(f"\n{len(by_id) - failures}/{len(by_id)} cases passed")
        return 1 if failures else 0

    if not (args.case and args.manifest and args.verdict):
        parser.error("give --case with --manifest and --verdict, or --all with --results-dir")
    if args.case not in by_id:
        parser.error(f"unknown case {args.case}; known: {', '.join(by_id)}")

    passed, problems = score(by_id[args.case], args.manifest, args.verdict)
    report(args.case, passed, problems)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
