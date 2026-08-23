import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class VersionTests(unittest.TestCase):
    def test_release_version_is_0_11_1(self):
        self.assertEqual("0.11.1", (ROOT / "VERSION").read_text(encoding="utf-8").strip())
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## v0.11.1 — 2026-08-23", changelog)
        self.assertIn("## v0.11.0 — 2026-08-17", changelog)


if __name__ == "__main__":
    unittest.main()
