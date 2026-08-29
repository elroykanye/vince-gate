import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VINCE = ROOT / "scripts" / "vince.py"


class AllImprovementsTests(unittest.TestCase):
    def run_vince(self, *args, cwd=None):
        return subprocess.run(
            [sys.executable, str(VINCE), *args],
            cwd=cwd or ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_health_report_flags_bindings_tasks_routes_and_next_actions(self):
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            profile = base / "profile.md"
            manifest = base / "install.json"
            tasks = base / "tasks"
            active = tasks / "active" / "stale-fail"
            active.mkdir(parents=True)
            (active / "verification-ledger.md").write_text(
                "Reviewer verdict: FAIL\nCurrent phase: `8`\nNext action: `fix finding`\n",
                encoding="utf-8",
            )
            profile.write_text(
                """## Model routing
| Harness | economy | balanced | frontier | reviewer | Status / verification command |
|---|---|---|---|---|---|
| codex | fast | | deep | review | verified 2020-01-01 - stale |
| generic | fast | balanced | deep | review | verified 2020-01-01 - stale |
| claude | | | | | inferred, unverified |
""",
                encoding="utf-8",
            )
            manifest.write_text(
                json.dumps(
                    {
                        "installs": {
                            "codex": {"version": "0.11.1", "root": str(base / "codex")},
                            "cursor": {"version": "0.11.1", "root": str(base / "cursor")},
                        }
                    }
                ),
                encoding="utf-8",
            )
            result = self.run_vince(
                "health",
                "--profile", str(profile),
                "--manifest", str(manifest),
                "--task-root", str(tasks),
                "--today", "2026-08-29",
            )
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual("ATTENTION", report["status"])
        self.assertIn("codex", report["bindings"])
        self.assertEqual("render-only", report["bindings"]["cursor"]["verification"])
        self.assertTrue(any(item["status"] == "FAIL" for item in report["tasks"]))
        self.assertTrue(any("missing balanced" in item for item in report["route_findings"]))
        self.assertTrue(any("generic: refresh route mappings" in item for item in report["route_findings"]))
        self.assertTrue(any("refresh route mappings" in item.lower() for item in report["next_actions"]))

    def test_route_refresh_updates_profile_from_explicit_inventory(self):
        with tempfile.TemporaryDirectory() as raw:
            profile = Path(raw) / "profile.md"
            profile.write_text(
                """# Profile

## Model routing

| Harness | economy | balanced | frontier | reviewer | Status / verification command |
|---|---|---|---|---|---|
| codex | old-fast | old-mid | old-deep | old-review | verified 2020-01-01 - stale |

## Agent routing

| Harness | explorer | worker | reviewer | Status / verification command |
|---|---|---|---|---|
| codex | old-explorer | old-worker | old-reviewer | verified 2020-01-01 - stale |
""",
                encoding="utf-8",
            )
            result = self.run_vince(
                "route-refresh",
                "--profile", str(profile),
                "--harness", "codex",
                "--economy", "gpt-spark",
                "--balanced", "gpt-balanced",
                "--frontier", "gpt-frontier",
                "--reviewer", "gpt-reviewer",
                "--explorer-agent", "explorer",
                "--worker-agent", "worker",
                "--reviewer-agent", "reviewer",
                "--verified-date", "2026-08-29",
            )
            text = profile.read_text(encoding="utf-8")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("| codex | gpt-spark | gpt-balanced | gpt-frontier | gpt-reviewer | verified 2026-08-29 - route-refresh |", text)
        self.assertIn("| codex | explorer | worker | reviewer | verified 2026-08-29 - route-refresh |", text)

    def test_release_check_validates_version_changelog_tag_and_install(self):
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            (repo / "VERSION").write_text("0.11.2\n", encoding="utf-8")
            (repo / "CHANGELOG.md").write_text("## v0.11.2 - 2026-08-29\n", encoding="utf-8")
            manifest = repo / "install.json"
            manifest.write_text(json.dumps({"installs": {"codex": {"version": "0.11.2"}}}), encoding="utf-8")
            ok = self.run_vince(
                "release-check",
                "--repo", str(repo),
                "--expected-version", "0.11.2",
                "--expected-tag", "v0.11.2",
                "--manifest", str(manifest),
                "--skip-git-tag",
            )
            (repo / "CHANGELOG.md").write_text("", encoding="utf-8")
            bad = self.run_vince(
                "release-check",
                "--repo", str(repo),
                "--expected-version", "0.11.2",
                "--expected-tag", "v0.11.2",
                "--manifest", str(manifest),
                "--skip-git-tag",
            )
        self.assertEqual(0, ok.returncode, ok.stdout + ok.stderr)
        self.assertEqual(1, bad.returncode)
        self.assertIn("missing changelog heading", bad.stdout)

    def test_codex_discovery_probe_is_documented_and_callable(self):
        guide = (ROOT / "USER-GUIDE.md").read_text(encoding="utf-8")
        self.assertIn("codex-discovery", guide)
        result = self.run_vince("codex-discovery", "--dry-run", "--codex", "codex")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        proof = json.loads(result.stdout)
        self.assertEqual("codex-discovery", proof["probe"])
        self.assertTrue(any("vince-route" in skill for skill in proof["expected_skills"]))

    def test_task_archive_moves_only_passed_clean_tasks(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            passed = root / "active" / "passed"
            failed = root / "active" / "failed"
            current_fail_with_history = root / "active" / "current-fail"
            passed.mkdir(parents=True)
            failed.mkdir(parents=True)
            current_fail_with_history.mkdir(parents=True)
            (passed / "verification-ledger.md").write_text(
                "Reviewer verdict: PASS\n", encoding="utf-8"
            )
            (failed / "verification-ledger.md").write_text(
                "Reviewer verdict: FAIL\n", encoding="utf-8"
            )
            (current_fail_with_history / "verification-ledger.md").write_text(
                "Reviewer verdict: FAIL 2026-08-30\n\n"
                "## History\n"
                "Older text: Reviewer verdict: PASS 2026-08-29\n",
                encoding="utf-8",
            )
            result = self.run_vince("archive-task", "--task-root", str(root), "--task", "passed")
            refused = self.run_vince("archive-task", "--task-root", str(root), "--task", "failed")
            refused_history = self.run_vince(
                "archive-task", "--task-root", str(root), "--task", "current-fail"
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertTrue((root / "archive" / "passed").is_dir())
            self.assertEqual(1, refused.returncode)
            self.assertTrue((root / "active" / "failed").is_dir())
            self.assertEqual(1, refused_history.returncode)
            self.assertTrue((root / "active" / "current-fail").is_dir())


if __name__ == "__main__":
    unittest.main()
