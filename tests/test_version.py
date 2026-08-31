import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class VersionTests(unittest.TestCase):
    def test_release_version_is_0_12_0(self):
        self.assertEqual("0.12.0", (ROOT / "VERSION").read_text(encoding="utf-8").strip())
        plugin = json.loads(
            (ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual("0.12.0", plugin["version"])
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## v0.12.0 — 2026-08-31", changelog)
        self.assertIn("progressive disclosure", changelog.lower())
        self.assertIn("GitHub Copilot", changelog)
        self.assertIn("## v0.11.2 — 2026-08-31", changelog)
        self.assertIn("## v0.11.1 — 2026-08-23", changelog)
        self.assertIn("## v0.11.0 — 2026-08-17", changelog)


if __name__ == "__main__":
    unittest.main()
