import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CodexBindingTests(unittest.TestCase):
    def test_codex_binding_records_live_verification(self):
        binding = json.loads((ROOT / "bindings" / "codex.json").read_text(encoding="utf-8"))

        self.assertEqual("verified", binding["status"])
        self.assertIn("live", binding["notes"].lower())

    def test_reviewer_agent_can_persist_its_verdict(self):
        template = (ROOT / "templates" / "codex-reviewer-agent.toml").read_text(encoding="utf-8")

        self.assertIn('sandbox_mode = "workspace-write"', template)
        self.assertNotIn('sandbox_mode = "read-only"', template)

    def test_codex_docs_describe_verified_stop_hook_support(self):
        harnesses = (ROOT / "docs" / "harnesses.md").read_text(encoding="utf-8")
        hooks = (ROOT / "hooks" / "README.md").read_text(encoding="utf-8")

        self.assertIn("| `codex` | Codex CLI", harnesses)
        codex_row = next(line for line in harnesses.splitlines() if line.startswith("| `codex` |"))
        self.assertIn("verified", codex_row)
        self.assertIn("Codex", hooks)
        self.assertIn("hooks.json", hooks)
        self.assertIn(
            "in-repo `.vince/tasks/active/` **or the repository's\nexternal store**",
            hooks,
        )


if __name__ == "__main__":
    unittest.main()
