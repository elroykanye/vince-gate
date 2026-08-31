import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def skill_parts(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    _, frontmatter, body = text.split("---", 2)
    description = next(
        line.split(":", 1)[1].strip()
        for line in frontmatter.splitlines()
        if line.startswith("description:")
    )
    return description, body


class TokenEfficientSkillTests(unittest.TestCase):
    def test_discovery_descriptions_are_compact(self):
        for path in sorted(SKILLS.glob("*/SKILL.md")):
            description, _ = skill_parts(path)
            with self.subTest(skill=path.parent.name):
                self.assertLessEqual(len(description), 320)

    def test_primary_workflows_fit_activation_budget(self):
        for name in ("vince-implement", "vince-review"):
            _, body = skill_parts(SKILLS / name / "SKILL.md")
            with self.subTest(skill=name):
                self.assertLessEqual(
                    len(body),
                    20_000,
                    "activation body exceeds the conservative ~5k-token budget",
                )

    def test_detailed_shared_guidance_is_conditional(self):
        for path in sorted(SKILLS.glob("*/SKILL.md")):
            _, body = skill_parts(path)
            with self.subTest(skill=path.parent.name):
                self.assertNotIn("Read `reference/voice.md`", body)
                self.assertNotIn("Also read `reference/token-discipline.md`", body)

        implement = (SKILLS / "vince-implement" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Load `reference/token-discipline.md` only", implement)
        self.assertIn("Load `reference/voice.md` only", implement)

    def test_progressive_references_preserve_the_gate(self):
        expected = {
            "vince-implement": (
                "reference/contract-and-recon.md",
                "reference/tdd-and-wire-proof.md",
                "reference/completion-and-review.md",
            ),
            "vince-review": (
                "reference/review-method.md",
                "reference/verdict-and-rereview.md",
            ),
        }
        required = {
            "vince-implement": ("RED", "GREEN", "TAMPER", "E2E-WIRE", "vince-review"),
            "vince-review": ("Pass 0", "mutation", "data boundaries", "PASS", "FAIL"),
        }
        for skill, references in expected.items():
            skill_dir = SKILLS / skill
            combined = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
            for reference in references:
                self.assertIn(reference, combined)
                ref_path = skill_dir / reference
                self.assertTrue(ref_path.is_file(), reference)
                combined += ref_path.read_text(encoding="utf-8")
            for term in required[skill]:
                self.assertIn(term, combined)

    def test_gemini_uses_native_agent_skills(self):
        binding = json.loads((ROOT / "bindings" / "gemini.json").read_text(encoding="utf-8"))
        self.assertEqual("dir", binding["layout"])
        self.assertEqual("yaml", binding["frontmatter"])
        self.assertEqual(".gemini/skills", binding["project_dir"])
        self.assertEqual("~/.gemini/skills", binding["user_dir"])
        self.assertEqual("SKILL.md", binding["entry"])
        self.assertIsNone(binding["index"])
        self.assertNotIn("command", binding["invocation"].lower())

    def test_copilot_has_a_non_colliding_native_binding(self):
        binding = json.loads((ROOT / "bindings" / "copilot.json").read_text(encoding="utf-8"))
        self.assertEqual("dir", binding["layout"])
        self.assertEqual("yaml", binding["frontmatter"])
        self.assertEqual(".github/skills", binding["project_dir"])
        self.assertEqual("~/.copilot/skills", binding["user_dir"])
        codex = json.loads((ROOT / "bindings" / "codex.json").read_text(encoding="utf-8"))
        self.assertNotEqual(codex["project_dir"], binding["project_dir"])
        self.assertNotEqual(codex["user_dir"], binding["user_dir"])

    def test_every_binding_renders_native_skill_entries(self):
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
                capture_output=True,
                text=True,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("[gemini]", result.stdout)
        self.assertIn("[copilot]", result.stdout)
        self.assertGreaterEqual(result.stdout.count("vince-implement/SKILL.md"), 4)

    def test_docs_describe_progressive_native_bindings_truthfully(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        guide = (ROOT / "USER-GUIDE.md").read_text(encoding="utf-8")
        harnesses = (ROOT / "docs" / "harnesses.md").read_text(encoding="utf-8")
        combined = "\n".join((readme, guide, harnesses))
        self.assertIn("GitHub Copilot", combined)
        self.assertIn(".github/skills", combined)
        self.assertIn(".gemini/skills", combined)
        self.assertIn("progressive disclosure", combined.lower())
        self.assertNotIn("TOML commands for Gemini CLI", combined)
        self.assertNotIn("Gemini CLI | TOML custom commands", combined)
        self.assertIn("unverified", combined.lower())


if __name__ == "__main__":
    unittest.main()
