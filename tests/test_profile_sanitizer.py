import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import sanitize  # noqa: E402


VERBOSE_LESSONS = """# Vince lessons — demo

What reviews have caught in this codebase. Newest first. Read before designing anything.

## 2026-09-02 — Keep upgrade proof real

**Seen in:** task-1 (CRITICAL, caught by lifecycle)
**What happened:** Clean installs passed while upgrades retained legacy files.
**Why it happened:** Only the clean path was tested.
**How to avoid it:** Run the prior-release upgrade in disposable project scope.
**Promoted to:** known_traps

## Custom operator note

Keep this exact paragraph because it belongs to the user.
"""

VERBOSE_PROFILE = """# Vince profile — demo

Written by `vince-setup` on 2026-09-01. Every command below was run in this repo and observed to work.

**Repo:** `C:\\repo`  ·  **Key:** `demo`  ·  **Stored:** `store`
**Inherits from:** none — standalone repo

## Project

- Root: `C:\\repo`
- Stack: Python
- Shape: single repository

## Known traps

Things that have bitten in this codebase before. The reviewer sweeps these in A5.

- Upgrade tests must use the previous release tag.

## Custom policy

Never remove this user-authored sentence.
"""


class ProfileSanitizerTests(unittest.TestCase):
    def test_new_templates_are_compact_and_budgeted(self):
        profile = (ROOT / "templates" / "profile.template.md").read_text(encoding="utf-8")
        lessons = (ROOT / "templates" / "lessons.template.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(profile), sanitize.PROFILE_MAX_CHARS)
        self.assertLessEqual(len(lessons), sanitize.LESSONS_MAX_CHARS)
        self.assertIn("vince-profile: compact-v1", profile)
        self.assertIn("vince-lessons: compact-v1", lessons)
        self.assertIn("RULE=", lessons)
        workspace = (ROOT / "templates" / "workspace-profile.template.md").read_text(encoding="utf-8")
        self.assertIn("vince-profile: compact-v1", workspace)
        self.assertIn(str(sanitize.PROFILE_MAX_CHARS), workspace)

    def test_lessons_become_compact_rules_and_preserve_custom_content(self):
        compact = sanitize.sanitize_lessons(VERBOSE_LESSONS)
        self.assertIn("<!-- vince-lessons: compact-v1", compact)
        self.assertIn("RULE=Run the prior-release upgrade in disposable project scope.", compact)
        self.assertIn("SOURCE=task-1 (CRITICAL, caught by lifecycle)", compact)
        self.assertIn("GATE=known_traps", compact)
        self.assertNotIn("What happened:", compact)
        self.assertNotIn("Why it happened:", compact)
        self.assertIn("Keep this exact paragraph because it belongs to the user.", compact)
        self.assertLessEqual(len(compact), sanitize.LESSONS_MAX_CHARS)

    def test_profile_removes_generated_prose_but_preserves_facts_and_custom_sections(self):
        compact = sanitize.sanitize_profile(VERBOSE_PROFILE)
        self.assertIn("<!-- vince-profile: compact-v1", compact)
        self.assertIn("repo: `C:\\repo` | key: `demo` | stored: `store`", compact)
        self.assertIn("inherits: none — standalone repo", compact)
        self.assertNotIn("Written by `vince-setup`", compact)
        self.assertNotIn("Things that have bitten", compact)
        self.assertIn("Never remove this user-authored sentence.", compact)
        self.assertLessEqual(len(compact), sanitize.PROFILE_MAX_CHARS)

    def test_generated_words_in_custom_sections_are_never_deleted(self):
        text = "# Profile\n\n## Custom operator policy\n\nWritten by `vince-setup` is user policy.\nThings that have bitten in this codebase before. Keep it.\n"
        compact = sanitize.sanitize_profile(text)
        self.assertIn("Written by `vince-setup` is user policy.", compact)
        self.assertIn("Things that have bitten in this codebase before. Keep it.", compact)

    def test_file_update_creates_content_addressed_backup_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            path = base / "lessons.md"
            path.write_text(VERBOSE_LESSONS, encoding="utf-8")
            first = sanitize.sanitize_file(path, "lessons", fix=True)
            second = sanitize.sanitize_file(path, "lessons", fix=True)
            self.assertTrue(first.changed)
            self.assertIsNotNone(first.backup)
            self.assertEqual(VERBOSE_LESSONS, first.backup.read_text(encoding="utf-8"))
            self.assertFalse(second.changed)
            self.assertEqual(1, len(list((base / ".vince-backups").glob("lessons.*.md"))))

    def test_dry_run_reports_change_without_writing_or_backing_up(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.md"
            path.write_text(VERBOSE_PROFILE, encoding="utf-8")
            result = sanitize.sanitize_file(path, "profile", fix=False)
            self.assertTrue(result.changed)
            self.assertIsNone(result.backup)
            self.assertEqual(VERBOSE_PROFILE, path.read_text(encoding="utf-8"))
            self.assertFalse((path.parent / ".vince-backups").exists())

    def test_oversized_custom_content_is_preserved_and_flagged(self):
        custom = "## Custom\n\n" + ("operator-owned text " * 1000)
        compact = sanitize.sanitize_profile(custom)
        self.assertIn(custom.strip(), compact)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.md"
            path.write_text(custom, encoding="utf-8")
            result = sanitize.sanitize_file(path, "profile", fix=False)
            self.assertTrue(result.over_budget)
            with self.assertRaisesRegex(ValueError, "limits exceeded"):
                sanitize.sanitize_file(path, "profile", fix=True)
            self.assertEqual(custom, path.read_text(encoding="utf-8"))

    def test_exact_budget_boundary_is_allowed(self):
        base = "# custom\n"
        payload = "x" * (sanitize.PROFILE_MAX_CHARS - len(sanitize.sanitize_profile(base)))
        text = base.rstrip() + payload + "\n"
        self.assertEqual(sanitize.PROFILE_MAX_CHARS, len(sanitize.sanitize_profile(text)))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.md"
            path.write_text(text, encoding="utf-8")
            self.assertFalse(sanitize.sanitize_file(path, "profile", fix=False).over_budget)

    def test_backup_collision_and_links_refuse_without_source_write(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            path = base / "lessons.md"
            path.write_text(VERBOSE_LESSONS, encoding="utf-8")
            import hashlib
            digest = hashlib.sha256(VERBOSE_LESSONS.encode()).hexdigest()
            backup = base / ".vince-backups" / f"lessons.{digest}.md"
            backup.parent.mkdir()
            backup.write_text("wrong", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "backup collision"):
                sanitize.sanitize_file(path, "lessons", fix=True)
            self.assertEqual(VERBOSE_LESSONS, path.read_text(encoding="utf-8"))
            victim = base / "victim.md"
            victim.write_text(VERBOSE_PROFILE, encoding="utf-8")
            link = base / "profile.md"
            try:
                link.symlink_to(victim)
            except OSError:
                return
            with self.assertRaisesRegex(ValueError, "linked"):
                sanitize.sanitize_file(link, "profile", fix=True)
            self.assertEqual(VERBOSE_PROFILE, victim.read_text(encoding="utf-8"))

    def test_lesson_incident_cause_and_rule_limit(self):
        compact = sanitize.sanitize_lessons(VERBOSE_LESSONS)
        self.assertIn("INCIDENT=Clean installs passed", compact)
        self.assertIn("CAUSE=Only the clean path was tested.", compact)
        text = "# Lessons\n\n" + "\n".join(
            f"- 2026-09-{i:02d} | RULE=x | SOURCE=y | GATE=watch" for i in range(1, 32)
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lessons.md"
            path.write_text(text, encoding="utf-8")
            self.assertTrue(sanitize.sanitize_file(path, "lessons", fix=False).over_budget)
            with self.assertRaisesRegex(ValueError, "limits exceeded"):
                sanitize.sanitize_file(path, "lessons", fix=True)
            self.assertEqual(text, path.read_text(encoding="utf-8"))

    def test_partial_lesson_is_not_destructively_rewritten(self):
        partial = "# Lessons\n\n## 2026-09-09 — Partial\n\n**Seen in:** task-2\nCustom tail.\n"
        compact = sanitize.sanitize_lessons(partial)
        self.assertIn("**Seen in:** task-2", compact)
        self.assertIn("Custom tail.", compact)

    def test_discovery_covers_workspace_and_every_repo_but_not_backups_or_tasks(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Path(directory)
            expected = []
            for base in (store, store / "repos" / "a", store / "repos" / "b"):
                base.mkdir(parents=True, exist_ok=True)
                for name in ("profile.md", "lessons.md"):
                    path = base / name
                    path.write_text("x", encoding="utf-8")
                    expected.append(path.resolve())
            ignored = store / "repos" / "a" / "tasks" / "active" / "x" / "profile.md"
            ignored.parent.mkdir(parents=True)
            ignored.write_text("x", encoding="utf-8")
            self.assertEqual(sorted(expected), sanitize.discover_documents(store))

    def test_doctor_fix_sanitizes_every_discovered_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            target = base / "target"
            store = base / "store"
            target.mkdir()
            env = {**os.environ, "VINCE_STORE": str(store)}
            install = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "install.py"), "install", "--target", str(target), "--scope", "project", "--binding", "codex"],
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(0, install.returncode, install.stderr)
            for key in ("one", "two"):
                config = store / "repos" / key
                config.mkdir(parents=True)
                (config / "profile.md").write_text(VERBOSE_PROFILE, encoding="utf-8")
                (config / "lessons.md").write_text(VERBOSE_LESSONS, encoding="utf-8")
            doctor = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "install.py"), "doctor", "--target", str(target), "--scope", "project", "--fix"],
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(0, doctor.returncode, doctor.stdout + doctor.stderr)
            self.assertIn("sanitized 4 document(s)", doctor.stdout)
            for path in store.glob("repos/*/*.md"):
                self.assertIn("compact-v1", path.read_text(encoding="utf-8"))
            second = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "install.py"), "doctor", "--target", str(target), "--scope", "project", "--fix"],
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(0, second.returncode, second.stdout + second.stderr)
            self.assertIn("0 document(s) changed", second.stdout)

    def test_doctor_still_sanitizes_store_when_target_has_no_install(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            store = base / "store"
            config = store / "repos" / "orphan"
            config.mkdir(parents=True)
            lesson = config / "lessons.md"
            lesson.write_text(VERBOSE_LESSONS, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "install.py"), "doctor", "--target", str(base / "target"), "--scope", "project", "--fix"],
                capture_output=True, text=True, env={**os.environ, "VINCE_STORE": str(store)},
            )
            self.assertEqual(1, result.returncode)
            self.assertIn("sanitized 1 document(s)", result.stdout)
            self.assertIn("compact-v1", lesson.read_text(encoding="utf-8"))

    def test_doctor_preflight_prevents_partial_write_on_invalid_document(self):
        with tempfile.TemporaryDirectory() as directory:
            base, store, target = Path(directory), Path(directory) / "store", Path(directory) / "target"
            first = store / "repos" / "a" / "profile.md"
            second = store / "repos" / "b" / "lessons.md"
            first.parent.mkdir(parents=True)
            second.parent.mkdir(parents=True)
            target.mkdir()
            first.write_text(VERBOSE_PROFILE, encoding="utf-8")
            second.write_bytes(b"\xff\xfe")
            run = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "install.py"), "doctor", "--target", str(target), "--scope", "project", "--fix"],
                capture_output=True, text=True, env={**os.environ, "VINCE_STORE": str(store)},
            )
            self.assertEqual(2, run.returncode)
            self.assertNotIn("Traceback", run.stderr)
            self.assertEqual(VERBOSE_PROFILE, first.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
