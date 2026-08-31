import re
import shlex
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INLINE_CODE = re.compile(r"`([^`\r\n]+)`")
EXECUTABLE_SUFFIXES = (".cmd", ".exe", ".bat")


def executable_name(token):
    name = token.strip("'\"").replace("\\", "/").rsplit("/", 1)[-1].lower()
    for suffix in EXECUTABLE_SUFFIXES:
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def contains_unpinned_npx(markdown):
    candidates = INLINE_CODE.findall(markdown)
    in_fence = False
    for line in markdown.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
        elif in_fence and line.strip() and not line.lstrip().startswith("#"):
            candidates.append(line.strip())

    for candidate in candidates:
        try:
            tokens = shlex.split(candidate, posix=False)
        except ValueError:
            tokens = candidate.split()
        if any(executable_name(token) == "npx" for token in tokens):
            return True
    return False


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
        ]

        for command in variants:
            with self.subTest(command=command):
                self.assertTrue(contains_unpinned_npx(command))


if __name__ == "__main__":
    unittest.main()
