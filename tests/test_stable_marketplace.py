"""Native Git distribution must not depend on a ZIP-only materialization step."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class StableMarketplaceTests(unittest.TestCase):
    def test_git_source_contains_the_canonical_skill_resources(self):
        for skill in (ROOT / "skills").glob("vince-*/SKILL.md"):
            for shared in (ROOT / "skills/_shared").glob("*.md"):
                destination = skill.parent / "reference" / shared.name
                with self.subTest(skill=skill.parent.name, shared=shared.name):
                    self.assertTrue(destination.is_file(), str(destination))
                    self.assertEqual(shared.read_bytes(), destination.read_bytes())

    def test_builder_rejects_stale_native_source_resources(self):
        with tempfile.TemporaryDirectory() as raw:
            source = Path(raw) / "source"
            shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            reference = source / "skills/vince-review/reference/brief.md"
            reference.write_text("stale generated reference", encoding="utf-8")
            result = subprocess.run([sys.executable, str(source / "scripts/package_plugin.py"),
                                     "--output", str(Path(raw) / "dist")], text=True, capture_output=True, timeout=20)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("sync-shared", result.stdout + result.stderr)

    def test_install_docs_explain_one_git_marketplace_and_full_lifecycle(self):
        for relative in ("README.md", "INSTALL.md", "USER-GUIDE.md", "docs/install.md", "docs/plugin.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(path=relative):
                self.assertIn("codex plugin marketplace add elroykanye/vince-gate --ref main", text)
                self.assertIn("codex plugin marketplace upgrade vince-gate", text)
                self.assertIn("rollback", text.lower())
                self.assertIn("Python 3.11+", text)
        install = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
        self.assertLess(install.index("## Native Codex plugin"), install.index("## Legacy"))


if __name__ == "__main__":
    unittest.main()
