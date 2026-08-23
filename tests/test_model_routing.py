import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ModelRoutingTests(unittest.TestCase):
    def setUp(self):
        self.skill = (ROOT / "skills" / "vince-route" / "SKILL.md").read_text(
            encoding="utf-8"
        )

    def test_route_skill_defines_classes_roles_and_conservative_rules(self):
        for model_class in ("economy", "balanced", "frontier", "reviewer"):
            self.assertIn(f"`{model_class}`", self.skill)
        for role in ("none", "explorer", "worker", "reviewer"):
            self.assertIn(f"`{role}`", self.skill)
        self.assertIn("smallest capable", self.skill)
        self.assertIn("Do not spawn", self.skill)
        self.assertIn("Do not weaken", self.skill)

    def test_fast_lane_hands_complex_work_back_to_the_full_model(self):
        self.assertIn("fast lane", self.skill.lower())
        self.assertIn("handoff", self.skill.lower())
        self.assertIn("multi-file", self.skill.lower())
        self.assertIn("explicitly run", self.skill.lower())
        self.assertIn("availability", self.skill.lower())

    def test_exact_models_come_from_profile_and_are_never_silently_substituted(self):
        self.assertIn("exact model", self.skill)
        self.assertIn("project profile", self.skill)
        self.assertIn("ask the user", self.skill)
        self.assertIn("Do not substitute", self.skill)
        for concrete_model in ("gpt-5.6", "claude-", "gemini-"):
            self.assertNotIn(concrete_model, self.skill.lower())

    def test_agent_identifier_is_copied_verbatim_from_its_own_mapping(self):
        self.assertIn("copy the exact agent identifier verbatim", self.skill.lower())
        self.assertIn("never derive", self.skill.lower())
        self.assertIn("model identifier", self.skill.lower())

    def test_route_runs_before_implementation_planning(self):
        implement = (ROOT / "skills" / "vince-implement" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        invocation = "Invoke `vince-route` after intake is `READY`, before implementation planning"
        self.assertIn(invocation, implement)
        route = implement.index(invocation)
        planning = implement.index("## Phase 2")
        self.assertLess(route, planning)
        self.assertIn("model switch", implement)

    def test_setup_and_doctor_own_mapping_discovery_and_staleness(self):
        setup = (ROOT / "skills" / "vince-setup" / "SKILL.md").read_text(encoding="utf-8")
        doctor = (ROOT / "skills" / "vince-doctor" / "SKILL.md").read_text(encoding="utf-8")
        template = (ROOT / "templates" / "profile.template.md").read_text(encoding="utf-8")

        self.assertIn("model routing", setup.lower())
        self.assertIn("exact model", setup.lower())
        self.assertIn("stale", doctor.lower())
        self.assertIn("model routing", doctor.lower())
        for heading in ("economy", "balanced", "frontier", "reviewer"):
            self.assertIn(heading, template)
        for harness in ("claude", "codex", "cursor", "gemini", "generic", "windsurf"):
            self.assertIn(f"| {harness} |", template.lower())

    def test_every_binding_renders_the_route_skill(self):
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
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        for binding in bindings:
            if binding.get("layout", "dir") == "dir":
                entry = f"vince-route/{binding.get('entry', 'SKILL.md')}"
            else:
                entry = (
                    f"{binding.get('prefix', '')}vince-route"
                    f"{binding.get('extension', '.md')}"
                )
            with self.subTest(binding=binding["id"]):
                self.assertIn(entry, result.stdout)
        self.assertIn("would install 10 skills", result.stdout)

    def test_docs_explain_routing_and_harness_verification_boundaries(self):
        documents = [
            (ROOT / "README.md").read_text(encoding="utf-8"),
            (ROOT / "USER-GUIDE.md").read_text(encoding="utf-8"),
            (ROOT / "docs" / "skills.md").read_text(encoding="utf-8"),
        ]
        for document in documents:
            self.assertIn("vince-route", document)
            self.assertIn("economy", document)
            self.assertIn("frontier", document)
            self.assertIn("unverified", document.lower())


if __name__ == "__main__":
    unittest.main()
