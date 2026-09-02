import json
import re
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
        descriptions = {}
        for path in sorted(SKILLS.glob("*/SKILL.md")):
            description, _ = skill_parts(path)
            descriptions[path.parent.name] = description
            with self.subTest(skill=path.parent.name):
                self.assertLessEqual(len(description), 320)

        self.assertEqual(len(descriptions), len(set(descriptions.values())))
        trigger_matrix = {
            "vince-cleanup": ("cleanup", "worktree", "stray processes"),
            "vince-doctor": ("broken bindings", "profiles", "health check"),
            "vince-document": ("completion documentation", "publish", "handoffs"),
            "vince-implement": ("features", "fixes", "refactors", "changes code"),
            "vince-intake": ("vague", "unsafe", "actionable contract", "refusal"),
            "vince-learn": ("review findings", "lessons", "known traps", "PASS"),
            "vince-review": ("Adversarially review", "PASS", "FAIL", "done"),
            "vince-route": ("model", "agent role", "planning", "review"),
            "vince-setup": ("profile", "onboarding", "missing profiles", "drift"),
            "vince-update": ("upgrade", "roll back", "version", "outdated"),
        }
        self.assertEqual(set(descriptions), set(trigger_matrix))
        for skill, triggers in trigger_matrix.items():
            with self.subTest(skill=skill):
                lowered = descriptions[skill].lower()
                for trigger in triggers:
                    self.assertIn(trigger.lower(), lowered)

        words = {
            skill: set(re.findall(r"[a-z0-9]+", description.lower()))
            for skill, description in descriptions.items()
        }
        for left, left_words in words.items():
            for right, right_words in words.items():
                if left >= right:
                    continue
                overlap = len(left_words & right_words) / len(left_words | right_words)
                self.assertLessEqual(overlap, 0.35, f"routing descriptions overlap: {left}/{right}")

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

    def test_implement_activation_preserves_non_negotiable_behavior(self):
        _, body = skill_parts(SKILLS / "vince-implement" / "SKILL.md")
        required_clauses = (
            "No implementation before a test fails for the expected reason.",
            "No completion claim before `vince-review` writes a PASS verdict.",
            "No claim such as “verified” or “tests pass” without the command and observed result.",
            "Never weaken RED, GREEN, TAMPER, regression, wire proof, or independent review to save tokens.",
            "The diff contains only the intended change.",
            "The suite is no worse than baseline.",
            "Nothing user-observable changed.",
            "No secret, debug artifact, or stray file is present.",
            "The commit message and version change follow the profile.",
        )
        for clause in required_clauses:
            self.assertIn(clause, body)

    def test_review_verdict_contract_supports_learning_and_closure(self):
        text = (SKILLS / "vince-review" / "reference" / "verdict-and-rereview.md").read_text(
            encoding="utf-8"
        )
        self.assertGreaterEqual(text.count("[caught: <attack>]"), 2)
        self.assertIn("Reviewer verdict", text)
        self.assertIn("review-verdict.md", text)
        self.assertIn("verification ledger", text.lower())
        self.assertIn("Every finding must carry one `[caught: <attack>]` tag", text)
        self.assertIn("update the verification ledger's `Reviewer verdict` field", text)

    def test_review_requires_exhaustive_manifest_before_any_verdict(self):
        core = (SKILLS / "vince-review" / "SKILL.md").read_text(encoding="utf-8")
        method = (SKILLS / "vince-review" / "reference" / "review-method.md").read_text(
            encoding="utf-8"
        )
        combined = core + method
        required = (
            "Create and freeze `review-coverage.json` before opening the ledger",
            "Finding enough evidence for FAIL never ends discovery early.",
            "Every acceptance criterion, definition-of-done item, material claim, changed entry point, and applicable attack pass",
            "PROVEN, FINDING, BLOCKED, or UNREVIEWED",
            "A later pass must cover previous findings, adjacent variants, and previously untouched surfaces.",
            "python <toolkit>/scripts/review_manifest.py validate",
        )
        for clause in required:
            self.assertIn(clause, combined)
        self.assertTrue((ROOT / "templates" / "review-coverage.template.json").is_file())
        self.assertTrue((ROOT / "scripts" / "review_manifest.py").is_file())

    def test_review_manifest_validator_rejects_incomplete_coverage(self):
        validator = ROOT / "scripts" / "review_manifest.py"
        incomplete = {
            "task": "T",
            "frozen_before_ledger": True,
            "discovery_complete": True,
            "early_exit": False,
            "items": [{"id": "AC-1", "kind": "acceptance", "status": "PROVEN"}],
            "attack_passes": {},
        }
        complete = {
            "task": "T",
            "frozen_before_ledger": True,
            "discovery_complete": True,
            "early_exit": False,
            "items": [
                {
                    "id": "AC-1",
                    "kind": "acceptance",
                    "claim": "observable result",
                    "source": "original contract",
                    "status": "PROVEN",
                    "evidence": ["command => result"],
                    "attacks": ["mutation killed"],
                },
                {
                    "id": "CLAIM-1",
                    "kind": "material-claim",
                    "claim": "nine cases",
                    "source": "completion documentation",
                    "status": "FINDING",
                    "evidence": ["raw cases mapped 1:1"],
                    "attacks": ["count reconciliation"],
                },
            ],
            "attack_passes": {
                f"A{i}": {"status": "PROVEN", "evidence": ["attack recorded"]}
                for i in range(8)
            },
            "previous_findings": [],
            "adjacent_variants": ["semantic reversal"],
            "untouched_surfaces": ["none — all manifest items terminal"],
        }
        with tempfile.TemporaryDirectory() as directory:
            bad = Path(directory) / "bad.json"
            good = Path(directory) / "good.json"
            missing_a7 = Path(directory) / "missing-a7.json"
            bad.write_text(json.dumps(incomplete), encoding="utf-8")
            good.write_text(json.dumps(complete), encoding="utf-8")
            without_a7 = json.loads(json.dumps(complete))
            del without_a7["attack_passes"]["A7"]
            missing_a7.write_text(json.dumps(without_a7), encoding="utf-8")
            rejected = subprocess.run([sys.executable, str(validator), "validate", str(bad)])
            accepted = subprocess.run([sys.executable, str(validator), "validate", str(good)])
            rejected_a7 = subprocess.run(
                [sys.executable, str(validator), "validate", str(missing_a7)]
            )
        self.assertNotEqual(0, rejected.returncode)
        self.assertNotEqual(0, rejected_a7.returncode)
        self.assertEqual(0, accepted.returncode)

    def test_gemini_uses_native_agent_skills(self):
        binding = json.loads((ROOT / "bindings" / "gemini.json").read_text(encoding="utf-8"))
        self.assertEqual("dir", binding["layout"])
        self.assertEqual("yaml", binding["frontmatter"])
        self.assertEqual(".gemini/skills", binding["project_dir"])
        self.assertEqual("~/.gemini/skills", binding["user_dir"])
        self.assertEqual("SKILL.md", binding["entry"])
        self.assertIsNone(binding["index"])
        self.assertNotIn("command", binding["invocation"].lower())
        self.assertEqual("unverified", binding["status"])

    def test_copilot_has_a_non_colliding_native_binding(self):
        binding = json.loads((ROOT / "bindings" / "copilot.json").read_text(encoding="utf-8"))
        self.assertEqual("dir", binding["layout"])
        self.assertEqual("yaml", binding["frontmatter"])
        self.assertEqual(".github/skills", binding["project_dir"])
        self.assertEqual("~/.copilot/skills", binding["user_dir"])
        codex = json.loads((ROOT / "bindings" / "codex.json").read_text(encoding="utf-8"))
        self.assertNotEqual(codex["project_dir"], binding["project_dir"])
        self.assertNotEqual(codex["user_dir"], binding["user_dir"])
        self.assertEqual("unverified", binding["status"])

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
        self.assertIn("review-coverage.json", readme)
        self.assertIn("does not stop discovery after finding enough evidence to FAIL", guide)
        self.assertIn("exhaustive review manifest", harnesses.lower())
        self.assertNotIn("TOML commands for Gemini CLI", combined)
        self.assertNotIn("Gemini CLI | TOML custom commands", combined)
        self.assertIn(
            "Gemini CLI and GitHub Copilot follow their\n"
            "documented native skill paths but remain `unverified`",
            readme,
        )
        self.assertIn(
            "Both bindings follow current vendor documentation and are render-tested, but\n"
            "remain `unverified`",
            guide,
        )
        self.assertIn(
            "| `gemini` | Gemini CLI | `.gemini/skills/<skill>/SKILL.md` (user: `~/.gemini/skills/`) | native Agent Skill, YAML frontmatter | unverified |",
            harnesses,
        )
        for name, document in (("README", readme), ("USER-GUIDE", guide), ("harnesses", harnesses)):
            affirmative = re.findall(
                r"(?im)^.*(?:Gemini|Copilot).*(?:are|is|status:?)\s+`?(?:live-verified|verified)`?.*$",
                document,
            )
            self.assertEqual([], affirmative, f"false live-verification claim in {name}")
        self.assertIn(
            "| `copilot` | GitHub Copilot | `.github/skills/<skill>/SKILL.md` (user: `~/.copilot/skills/`) | native Agent Skill, YAML frontmatter | unverified |",
            harnesses,
        )


if __name__ == "__main__":
    unittest.main()
