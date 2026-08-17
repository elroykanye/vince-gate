import json
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "vince_gate_stop.py"


class VinceGateStopTests(unittest.TestCase):
    def test_blocks_for_recent_unproven_ledger_in_external_store(self):
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            repo = base / "repo"
            repo.mkdir()
            self._git(repo, "init")
            self._git(repo, "remote", "add", "origin", "https://github.com/example/vince-target.git")

            ledger = (
                base
                / "store"
                / "repos"
                / "github.com__example__vince-target"
                / "tasks"
                / "active"
                / "task-1"
                / "verification-ledger.md"
            )
            ledger.parent.mkdir(parents=True)
            ledger.write_text(
                "# task-1 Verification Ledger\n\n"
                "Reviewer verdict: NOT-RUN\n\n"
                "| ID | Requirement | Proof | Command | Status |\n"
                "|----|-------------|-------|---------|--------|\n"
                "| AC-1 | works | E2E-WIRE | test | NOT-PROVEN |\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps({"cwd": str(repo)}),
                text=True,
                capture_output=True,
                env={**os.environ, "VINCE_STORE": str(base / "store")},
                timeout=10,
            )

            self.assertEqual(2, result.returncode, result.stderr)
            self.assertIn("task-1", result.stderr)
            self.assertIn("AC-1", result.stderr)

    def test_blocks_external_store_for_repo_without_origin_remote(self):
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            repo = base / "local-repo"
            repo.mkdir()
            self._git(repo, "init")
            digest = hashlib.sha256(str(repo.resolve()).replace("\\", "/").lower().encode()).hexdigest()[:8]
            key = f"local__local-repo__{digest}"
            ledger = base / "store" / "repos" / key / "tasks" / "active" / "task-2" / "verification-ledger.md"
            ledger.parent.mkdir(parents=True)
            ledger.write_text(
                "# task-2 Verification Ledger\n\nReviewer verdict: NOT-RUN\n\n"
                "| ID | Requirement | Proof | Command | Status |\n"
                "|----|-------------|-------|---------|--------|\n"
                "| AC-2 | works | E2E-WIRE | test | RED |\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps({"cwd": str(repo)}),
                text=True,
                capture_output=True,
                env={**os.environ, "VINCE_STORE": str(base / "store")},
                timeout=10,
            )

            self.assertEqual(2, result.returncode, result.stderr)
            self.assertIn("task-2", result.stderr)

    @staticmethod
    def _git(repo: Path, *args: str):
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            text=True,
            capture_output=True,
            timeout=10,
        )
        if result.returncode:
            raise AssertionError(result.stderr)


if __name__ == "__main__":
    unittest.main()
