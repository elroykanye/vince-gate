import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PromptIntakeSkillTests(unittest.TestCase):
    def test_skill_defines_ready_clarify_and_bounce_decisions(self):
        skill = (ROOT / "skills" / "vince-intake" / "SKILL.md").read_text(encoding="utf-8")

        for decision in ("READY", "CLARIFY", "BOUNCE"):
            with self.subTest(decision=decision):
                self.assertIn(f"| `{decision}` |", skill)
        self.assertIn("contradictory", skill)
        self.assertIn("impossible", skill)
        self.assertIn("unsafe", skill)
        self.assertIn("unauthorized", skill)
        self.assertIn("unbounded", skill)
        self.assertIn("minimum", skill.lower())

    def test_skill_preserves_intent_and_forbids_premature_implementation(self):
        skill = (ROOT / "skills" / "vince-intake" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Preserve the user's intent", skill)
        self.assertIn("Do not begin implementation", skill)
        self.assertIn("Do not insult", skill)
        self.assertIn("Do not invent", skill)

    def test_implementation_gate_runs_intake_before_contract_extraction(self):
        implement = (ROOT / "skills" / "vince-implement" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        intake = implement.index("vince-intake")
        phase_zero = implement.index("## Phase 0")

        self.assertLess(intake, phase_zero)
        self.assertIn("Do not continue on `CLARIFY` or `BOUNCE`", implement)

    def test_every_binding_renders_the_intake_skill(self):
        bindings = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted((ROOT / "bindings").glob("*.json"))
        ]
        with tempfile.TemporaryDirectory() as target:
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "install.py"),
                    "install",
                    "--target",
                    target,
                    "--scope",
                    "project",
                    "--binding",
                    "all",
                    "--dry-run",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(0, result.returncode, result.stderr)
        for binding in bindings:
            if binding.get("layout", "dir") == "dir":
                entry = f"vince-intake/{binding.get('entry', 'SKILL.md')}"
            else:
                entry = (
                    f"{binding.get('prefix', '')}vince-intake"
                    f"{binding.get('extension', '.md')}"
                )
            with self.subTest(binding=binding["id"]):
                self.assertIn(entry, result.stdout)
        self.assertIn("would install 9 skills", result.stdout)

    def test_docs_route_unclear_requests_through_intake(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        guide = (ROOT / "USER-GUIDE.md").read_text(encoding="utf-8")
        skills = (ROOT / "docs" / "skills.md").read_text(encoding="utf-8")

        for document in (readme, guide, skills):
            self.assertIn("vince-intake", document)
            self.assertIn("READY", document)
            self.assertIn("CLARIFY", document)
            self.assertIn("BOUNCE", document)

        installer = (ROOT / "scripts" / "install.py").read_text(encoding="utf-8")
        self.assertNotIn("eight skills", installer)


if __name__ == "__main__":
    unittest.main()
