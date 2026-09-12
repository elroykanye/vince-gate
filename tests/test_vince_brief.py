import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


class VinceBriefTests(unittest.TestCase):
    def test_brief_skill_and_shared_contract_are_shipped(self):
        skill = (SKILLS / "vince-brief" / "SKILL.md").read_text(encoding="utf-8")
        shared = (SKILLS / "_shared" / "brief.md").read_text(encoding="utf-8")
        self.assertIn("persistent", skill.lower())
        self.assertIn("normal mode", skill.lower())
        self.assertLessEqual(len(shared.split()), 250)
        for rule in ("Result:", "Problem:", "Next:", "unknown", "safety"):
            self.assertIn(rule, shared)

    def test_every_vince_workflow_applies_brief_only_at_response_time(self):
        expected = {
            path.parent.name
            for path in SKILLS.glob("vince-*/SKILL.md")
            if path.parent.name != "vince-brief"
        }
        for name in expected:
            text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("reference/brief.md", text, name)
            self.assertIn("before the final user-facing response", text.lower(), name)

    def test_brief_contract_preserves_detail_and_safety_escape_hatches(self):
        shared = (SKILLS / "_shared" / "brief.md").read_text(encoding="utf-8").lower()
        for phrase in (
            "user explicitly asks for detail",
            "destructive",
            "real ambiguity",
            "do not invent a cause",
            "does not limit analysis",
        ):
            self.assertIn(phrase, shared)

    def test_paired_eval_fixture_covers_concision_regressions(self):
        fixture = ROOT / "evals" / "vince-brief-cases.jsonl"
        cases = [json.loads(line) for line in fixture.read_text(encoding="utf-8").splitlines() if line]
        self.assertGreaterEqual(len(cases), 6)
        self.assertEqual(len(cases), len({case["id"] for case in cases}))
        for case in cases:
            self.assertTrue(case["prompt"].strip())
            self.assertGreaterEqual(len(case["expect"]), 2)
        self.assertIn("unknown-cause", {case["id"] for case in cases})
        self.assertIn("unsafe-delete", {case["id"] for case in cases})

    def test_every_binding_installs_the_shared_brief_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "install.py"), "install", "--target", str(target),
                 "--scope", "project", "--binding", "all"],
                capture_output=True, text=True,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            manifest = json.loads((target / ".vince" / "install.json").read_text(encoding="utf-8"))
            for binding, install in manifest["installs"].items():
                files = install["files"]
                brief_entries = [path for path in files if "vince-brief" in path]
                references = [path for path in files if path.endswith("brief.md")]
                self.assertTrue(brief_entries, binding)
                self.assertTrue(references, binding)


if __name__ == "__main__":
    unittest.main()
