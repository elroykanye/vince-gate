"""Compact Vince profile and lesson files without discarding custom content."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path


PROFILE_MAX_CHARS = 12_000
LESSONS_MAX_CHARS = 8_000
PROFILE_MARKER = f"<!-- vince-profile: compact-v1; budget: {PROFILE_MAX_CHARS} chars -->"
LESSONS_MARKER = f"<!-- vince-lessons: compact-v1; budget: {LESSONS_MAX_CHARS} chars -->"


@dataclass(frozen=True)
class SanitizeResult:
    path: Path
    kind: str
    changed: bool
    before_chars: int
    after_chars: int
    backup: Path | None = None
    over_budget: bool = False


def _tidy(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def sanitize_profile(text: str) -> str:
    """Compress known generated profile prose while preserving all other content."""
    out = text
    out = re.sub(r"^<!-- vince-profile: compact-v1[^\n]*-->\s*", "", out)
    out = re.sub(
        r"^Written by `vince-setup`[^\n]*\n+", "", out, flags=re.MULTILINE
    )
    out = re.sub(
        r"^Things that have bitten in this codebase before\.[^\n]*\n+",
        "", out, flags=re.MULTILINE,
    )
    out = re.sub(
        r"^\*\*Repo:\*\*\s*([^\n·]+?)\s*·\s*\*\*Key:\*\*\s*([^\n·]+?)\s*·\s*\*\*Stored:\*\*\s*([^\n]+)$",
        lambda m: f"repo: {m.group(1).strip()} | key: {m.group(2).strip()} | stored: {m.group(3).strip()}",
        out, flags=re.MULTILINE,
    )
    out = re.sub(
        r"^\*\*Inherits from:\*\*\s*(.+)$", r"inherits: \1", out, flags=re.MULTILINE
    )
    return _tidy(f"{PROFILE_MARKER}\n{out}")


_LESSON = re.compile(
    r"^##\s+(?P<title>\d{4}-\d{2}-\d{2}\s+—\s+[^\n]+)\n+"
    r"\*\*Seen in:\*\*\s*(?P<seen>[^\n]+)\n+"
    r"\*\*What happened:\*\*\s*(?P<happened>[^\n]+)\n+"
    r"\*\*Why it happened:\*\*\s*(?P<why>[^\n]+)\n+"
    r"\*\*How to avoid it:\*\*\s*(?P<rule>[^\n]+)\n+"
    r"\*\*Promoted to:\*\*\s*(?P<gate>[^\n]+)",
    re.MULTILINE,
)


def sanitize_lessons(text: str) -> str:
    """Turn Vince-generated narrative lessons into one-line operational rules."""
    out = re.sub(r"^<!-- vince-lessons: compact-v1[^\n]*-->\s*", "", text)
    out = re.sub(
        r"^What reviews have caught in this codebase\.[^\n]*\n+", "", out,
        flags=re.MULTILINE,
    )

    def compact(match: re.Match) -> str:
        date, _, title = match.group("title").partition(" — ")
        return (
            f"- {date} | RULE={match.group('rule').strip()} | "
            f"SOURCE={match.group('seen').strip()} | GATE={match.group('gate').strip()}"
            f" | NOTE={title.strip()}"
        )

    out = _LESSON.sub(compact, out)
    return _tidy(f"{LESSONS_MARKER}\n{out}")


def sanitize_file(path: Path, kind: str, *, fix: bool) -> SanitizeResult:
    path = Path(path).resolve()
    before = path.read_text(encoding="utf-8")
    if kind == "profile":
        after, budget = sanitize_profile(before), PROFILE_MAX_CHARS
    elif kind == "lessons":
        after, budget = sanitize_lessons(before), LESSONS_MAX_CHARS
    else:
        raise ValueError(f"unknown document kind: {kind}")
    changed = before != after
    backup = None
    if changed and fix:
        digest = hashlib.sha256(before.encode("utf-8")).hexdigest()[:12]
        backup_dir = path.parent / ".vince-backups"
        backup = backup_dir / f"{path.stem}.{digest}{path.suffix}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            backup.write_text(before, encoding="utf-8", newline="")
        path.write_text(after, encoding="utf-8", newline="")
    return SanitizeResult(path, kind, changed, len(before), len(after), backup, len(after) > budget)


def discover_documents(root: Path) -> list[Path]:
    """Find workspace and per-repository Vince documents, excluding task/backup data."""
    root = Path(root).resolve()
    found = []
    if not root.is_dir():
        return found
    for path in root.rglob("*.md"):
        if path.name not in {"profile.md", "lessons.md"}:
            continue
        rel = path.relative_to(root)
        if "tasks" in rel.parts or ".vince-backups" in rel.parts:
            continue
        found.append(path.resolve())
    return sorted(found)
