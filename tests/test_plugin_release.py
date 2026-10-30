import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

from tests.test_plugin_tools import exchange, call

ROOT = Path(__file__).resolve().parents[1]


class PluginReleaseTests(unittest.TestCase):
    def test_manifests_and_release_identity(self):
        version = (ROOT / "VERSION").read_text().strip()
        self.assertEqual("0.15.0", version)
        portable = json.loads((ROOT / "plugin.json").read_text())
        codex = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
        claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
        for manifest in (portable, codex, claude):
            self.assertEqual(version, manifest["version"])
            self.assertEqual("vince-gate", manifest["name"])
            self.assertNotIn("defaults to FAIL", manifest["description"])
        self.assertTrue(portable["extensions"]["com.openai"]["requires_local_executor"])
        self.assertNotIn("hooks", portable["extensions"]["com.openai"])
        listing = portable["extensions"]["com.openai"]["interface"]
        for field in ("websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL"):
            self.assertTrue(listing[field].startswith("https://"))
        cases = portable["extensions"]["com.openai"]["review"]["test_cases"]
        self.assertEqual(5, len(cases["positive"]))
        self.assertEqual(3, len(cases["negative"]))
        self.assertEqual("./skills/", codex["skills"])
        mcp = json.loads((ROOT / "mcp.json").read_text())
        server = mcp["mcpServers"]["vince"]
        self.assertEqual("stdio", server["type"])
        self.assertEqual(["${PLUGIN_ROOT}/scripts/mcp_server.py"], server["args"])
        self.assertIn("## v0.15.0", (ROOT / "CHANGELOG.md").read_text())

    def test_build_is_reproducible_and_runs_without_checkout(self):
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            hashes = []
            for name in ("a", "b"):
                output = base / name
                run = subprocess.run([sys.executable, str(ROOT / "scripts/package_plugin.py"),
                                      "--output", str(output)], capture_output=True, text=True, timeout=20)
                self.assertEqual(0, run.returncode, run.stdout + run.stderr)
                archive = output / "vince-gate-0.15.0.zip"
                hashes.append(hashlib.sha256(archive.read_bytes()).hexdigest())
                self.assertIn(hashes[-1], (output / "SHA256SUMS").read_text())
                self.assertTrue((output / "release-notes.md").is_file())
            self.assertEqual(*hashes)
            unpack = base / "unpacked"
            with zipfile.ZipFile(base / "a/vince-gate-0.15.0.zip") as archive:
                names = archive.namelist()
                self.assertIn("plugin.json", names)
                self.assertIn("skills/vince-review/SKILL.md", names)
                self.assertFalse(any("__pycache__" in n or n.startswith(("hooks/", ".git/", "tests/")) for n in names))
                archive.extractall(unpack)
            info = exchange(unpack, [call("vince_plugin_info")])[0]["result"]["structuredContent"]
            self.assertEqual("0.15.0", info["version"])
            for skill in info["skills"]:
                body = (unpack / "skills" / skill / "SKILL.md").read_text()
                self.assertTrue(body.startswith("---\n"))
                self.assertTrue((unpack / "skills" / skill / "reference/brief.md").is_file())
            project = base / "existing-project"
            project.mkdir()
            (project / "keep.txt").write_text("user data")
            self.assertEqual("user data", (project / "keep.txt").read_text())
            self.assertIn("All stated requirements are met", (unpack / "skills/vince-review/SKILL.md").read_text())

    def test_build_refuses_inconsistent_version(self):
        with tempfile.TemporaryDirectory() as raw:
            copied = Path(raw) / "source"
            shutil.copytree(ROOT, copied, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            (copied / "VERSION").write_text("9.0.0\n")
            result = subprocess.run([sys.executable, str(copied / "scripts/package_plugin.py"),
                                     "--output", str(Path(raw) / "dist")], capture_output=True, text=True, timeout=20)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("version", (result.stdout + result.stderr).lower())


if __name__ == "__main__":
    unittest.main()
