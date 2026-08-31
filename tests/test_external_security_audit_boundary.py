import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ExternalSecurityAuditBoundaryTests(unittest.TestCase):
    def test_vince_does_not_embed_skillspector_or_a_skill_scan_gate(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "vince.py"), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )

        self.assertNotIn("skill-scan", result.stdout.lower())

        product_paths = [
            ROOT / "scripts",
            ROOT / "INSTALL.md",
            ROOT / "USER-GUIDE.md",
            ROOT / "docs",
        ]
        product_text = "\n".join(
            path.read_text(encoding="utf-8")
            if path.is_file()
            else "\n".join(
                child.read_text(encoding="utf-8")
                for child in path.rglob("*")
                if child.is_file() and child.suffix in {".md", ".py"}
            )
            for path in product_paths
        ).lower()
        self.assertNotIn("skillspector", product_text)
        self.assertNotIn("skip-skill-scan", product_text)
        self.assertNotIn("skill-scan-baseline", product_text)

    def test_executable_examples_are_pinned_or_project_local(self):
        cleanup = (ROOT / "skills" / "vince-cleanup" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        attack_playbook = (
            ROOT / "skills" / "vince-review" / "reference" / "attack-playbook.md"
        ).read_text(encoding="utf-8")

        self.assertNotIn("`npx serve`", cleanup)
        self.assertNotIn("`npx stryker run --incremental`", attack_playbook)
        self.assertNotIn("kill someone's IDE", cleanup)


if __name__ == "__main__":
    unittest.main()
