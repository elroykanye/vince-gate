import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NPX_TOKEN = re.compile(r"\bnpx(?:\.(?:cmd|exe|bat))?\b", re.IGNORECASE)


def contains_unpinned_npx(markdown):
    return NPX_TOKEN.search(markdown) is not None


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
            ROOT / "skills",
            ROOT / "INSTALL.md",
            ROOT / "USER-GUIDE.md",
            ROOT / "docs",
        ]
        product_files = []
        for path in product_paths:
            if path.is_file():
                product_files.append(path)
            else:
                product_files.extend(
                    child
                    for child in path.rglob("*")
                    if child.is_file() and child.suffix in {".md", ".py"}
                )

        for product_file in product_files:
            product_text = product_file.read_text(encoding="utf-8").lower()
            with self.subTest(product_file=product_file.relative_to(ROOT)):
                for forbidden in (
                    "skillspector",
                    "skip-skill-scan",
                    "skill-scan-baseline",
                ):
                    self.assertFalse(
                        forbidden in product_text,
                        f"{forbidden} found in {product_file.relative_to(ROOT)}",
                    )

    def test_executable_examples_are_pinned_or_project_local(self):
        cleanup = (ROOT / "skills" / "vince-cleanup" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        for skill_doc in (ROOT / "skills").rglob("*.md"):
            with self.subTest(skill_doc=skill_doc.relative_to(ROOT)):
                self.assertFalse(
                    contains_unpinned_npx(skill_doc.read_text(encoding="utf-8")),
                    f"unpinned npx executable in {skill_doc.relative_to(ROOT)}",
                )
        self.assertNotIn("kill someone's IDE", cleanup)

    def test_unpinned_npx_variants_are_rejected(self):
        variants = [
            "`npx serve`",
            "`npx --yes serve`",
            "`npx stryker run --incremental`",
            "`npx --yes stryker run --incremental`",
            "`npx.cmd --yes stryker run --incremental`",
            "`npx.exe --yes stryker run --incremental`",
            "`C:\\tools\\node\\npx.cmd --yes stryker run --incremental`",
            "`./tools/npx --yes stryker run --incremental`",
            "`cmd /c npx.cmd --yes stryker run --incremental`",
            "`\"C:\\Program Files\\node\\npx.cmd\" --yes stryker`",
            "~~~bash\nnpx serve\n~~~",
            "Do not use npx for executable examples.",
        ]

        for command in variants:
            with self.subTest(command=command):
                self.assertTrue(contains_unpinned_npx(command))


if __name__ == "__main__":
    unittest.main()
