#!/usr/bin/env python3
"""Install the Vince skills into any agent harness.

The canonical skills live in skills/*/SKILL.md. A *binding* (bindings/*.json) says how a
given harness wants them on disk: which directory, one-file-per-skill or a directory each,
which frontmatter dialect, and whether an index file needs a pointer block. Rendering is
deterministic, so every installed byte can be checked against its source later.

Location-independent: the toolkit root comes from this file's location, or $VINCE_HOME.

Usage:
    python scripts/install.py bindings
    python scripts/install.py list
    python scripts/install.py install   [--target DIR] [--scope project|user]
                                        [--binding auto|all|claude,cursor,...]
                                        [--dry-run] [--force]
    python scripts/install.py status    [--target DIR] [--scope project|user]
    python scripts/install.py doctor    [--target DIR] [--scope project|user] [--fix] [--force]
    python scripts/install.py uninstall [--target DIR] [--scope project|user]
                                        [--binding ...] [--dry-run] [--force]

Exit codes: 0 healthy / done, 1 problems found (or not installed), 2 refused to clobber.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

MANIFEST_REL = Path(".vince") / "install.json"
LEGACY_MANIFEST_REL = Path(".claude") / ".vince-install.json"
MANIFEST_VERSION = 2
SKIP_DIRS = {"__pycache__", ".git"}
SKIP_SUFFIXES = {".pyc", ".pyo"}
INDEX_BEGIN = "<!-- BEGIN vince -->"
INDEX_END = "<!-- END vince -->"


# --------------------------------------------------------------------------- toolkit

def toolkit_root() -> Path:
    env = os.environ.get("VINCE_HOME")
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


def version() -> str:
    f = toolkit_root() / "VERSION"
    return f.read_text(encoding="utf-8").strip() if f.is_file() else "unknown"


def load_bindings() -> dict:
    out = {}
    bdir = toolkit_root() / "bindings"
    for f in sorted(bdir.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        out[data["id"]] = data
    return out


def skill_names() -> list:
    src = toolkit_root() / "skills"
    if not src.is_dir():
        return []
    return sorted(
        d.name for d in src.iterdir()
        if d.is_dir() and d.name not in SKIP_DIRS and (d / "SKILL.md").is_file()
    )


def reference_files(skill: str) -> list:
    """Reference docs of one skill, as paths relative to the skill directory."""
    root = toolkit_root() / "skills" / skill
    out = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.name == "SKILL.md":
            continue
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts) or p.suffix in SKIP_SUFFIXES:
            continue
        out.append(rel)
    return out


# --------------------------------------------------------------------------- rendering

def split_frontmatter(text: str):
    """Return (fields, body). Handles the simple `key: value` frontmatter the skills use."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end].strip("\n")
    body = text[end + 4:].lstrip("\n")
    fields = {}
    key = None
    for line in raw.splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            key = m.group(1)
            fields[key] = m.group(2).strip()
        elif key and line.strip():
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields, body


def toml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def render_entry(binding: dict, name: str, description: str, body: str) -> str:
    style = binding.get("frontmatter", "none")
    if style == "yaml":
        return f"---\nname: {name}\ndescription: {description}\n---\n\n{body}"
    if style == "mdc":
        return (f"---\ndescription: {description}\nglobs:\nalwaysApply: false\n---\n\n{body}")
    if style == "windsurf":
        return (f"---\ntrigger: model_decision\ndescription: {description}\n---\n\n{body}")
    if style == "toml-command":
        prompt = body.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
        return (f'description = "{toml_escape(description)}"\n\n'
                f'prompt = """\n{prompt}\n"""\n')
    # none: plain markdown, description kept as a lead blockquote so it stays discoverable
    lines = body.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("# "):
            lines.insert(i + 1, f"\n> {description}")
            return "\n".join(lines)
    return f"> {description}\n\n{body}"


def rewrite_links(text: str, skill: str, binding: dict) -> str:
    """In flat layouts a reference/ subdirectory does not exist; point at the sibling file."""
    if binding.get("layout") != "flat":
        return text
    prefix = binding.get("prefix", "")

    def repl(m):
        return f"{prefix}{skill}-{m.group(1)}.md"

    return re.sub(r"reference/([\w.-]+)\.md", repl, text)


def render_skill(binding: dict, skill: str):
    """Return [(relative path under the binding's dir, bytes)] for one skill."""
    src = toolkit_root() / "skills" / skill
    fields, body = split_frontmatter((src / "SKILL.md").read_text(encoding="utf-8"))
    name = fields.get("name", skill)
    description = fields.get("description", "")
    body = rewrite_links(body, skill, binding)

    out = []
    layout = binding.get("layout", "dir")
    if layout == "dir":
        entry = f"{skill}/{binding.get('entry', 'SKILL.md')}"
        out.append((entry, render_entry(binding, name, description, body)))
        for rel in reference_files(skill):
            out.append((f"{skill}/{rel.as_posix()}",
                        (src / rel).read_text(encoding="utf-8")))
    else:
        prefix = binding.get("prefix", "")
        ext = binding.get("extension", ".md")
        out.append((f"{prefix}{skill}{ext}", render_entry(binding, name, description, body)))
        for rel in reference_files(skill):
            text = rewrite_links((src / rel).read_text(encoding="utf-8"), skill, binding)
            out.append((f"{prefix}{skill}-{rel.stem}.md", text))
    return [(p, t.encode("utf-8")) for p, t in out]


def skill_path(binding: dict, skill: str) -> str:
    if binding.get("layout", "dir") == "dir":
        return f"{binding['project_dir']}/{skill}/{binding.get('entry', 'SKILL.md')}"
    return (f"{binding['project_dir']}/{binding.get('prefix', '')}{skill}"
            f"{binding.get('extension', '.md')}")


def render_index(bindings: list) -> str:
    """One pointer block per index file, covering every binding that shares that file."""
    purposes = {}
    for skill in skill_names():
        fields, _ = split_frontmatter(
            (toolkit_root() / "skills" / skill / "SKILL.md").read_text(encoding="utf-8"))
        desc = fields.get("description", "").split(". ")[0].rstrip(".")
        if len(desc) > 84:
            desc = desc[:81].rsplit(" ", 1)[0] + "..."
        purposes[skill] = desc

    multi = len(bindings) > 1
    if multi:
        # One row per skill; the per-harness paths follow as a short pattern list.
        header = "| Skill | Purpose |\n|-------|---------|"
        rows = [f"| `{s}` | {purposes[s]} |" for s in skill_names()]
        locations = ["", "Where they live:"] + [
            f"- {b['label']}: `{skill_path(b, '<skill>')}`" for b in bindings]
    else:
        header = "| Skill | File | Purpose |\n|-------|------|---------|"
        rows = [f"| `{s}` | `{skill_path(bindings[0], s)}` | {purposes[s]} |"
                for s in skill_names()]
        locations = []

    invocations = []
    for binding in bindings:
        inv = binding.get("invocation", "read the file and follow it").replace("{skill}", "<skill>")
        invocations.append(f"`{inv}`" + (f" ({binding['label']})" if multi else ""))

    return "\n".join([
        INDEX_BEGIN,
        "## Vince — implementer and reviewer (not optional)",
        "",
        'Any feature, bugfix, refactor or "make X work" request in this repo goes through Vince.',
        "",
        "1. Read and follow `vince-implement` **before writing code**. It extracts the contract,",
        "   forbids implementation before a failing test, and records reproducible evidence.",
        "2. It hands off to `vince-review` before anything may be called done. The reviewer is",
        "   adversarial and defaults to FAIL. Reporting a task complete without a PASS verdict,",
        "   or arguing a verdict down instead of fixing it, is a protocol violation.",
        "",
        'No unproven claim in any report: "should work", "verified", "tests pass" do not count',
        "without the command and its output.",
        "",
        header,
        *rows,
        *locations,
        "",
        "Invoke: " + ", ".join(invocations) + ".",
        "Project specifics live in `.vince/profile.md` — run `vince-setup` first if it is missing.",
        INDEX_END,
    ]) + "\n"


def write_index(path: Path, block: str, dry_run: bool) -> str:
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    if INDEX_BEGIN in existing and INDEX_END in existing:
        start = existing.index(INDEX_BEGIN)
        end = existing.index(INDEX_END) + len(INDEX_END)
        updated = existing[:start] + block.rstrip("\n") + existing[end:]
    elif existing.strip():
        updated = existing.rstrip("\n") + "\n\n" + block
    else:
        updated = block
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(updated, encoding="utf-8")
    return "updated" if existing else "created"


def strip_index(path: Path, dry_run: bool) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    if INDEX_BEGIN not in text or INDEX_END not in text:
        return False
    start = text.index(INDEX_BEGIN)
    end = text.index(INDEX_END) + len(INDEX_END)
    updated = (text[:start].rstrip("\n") + "\n" + text[end:].lstrip("\n")).strip("\n")
    if not dry_run:
        if updated:
            path.write_text(updated + "\n", encoding="utf-8")
        else:
            path.unlink()
    return True


# --------------------------------------------------------------------------- targets

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def resolve_root(args) -> Path:
    """The project root (project scope) or the home directory (user scope)."""
    if getattr(args, "scope", "project") == "user":
        return Path.home()
    if getattr(args, "target", None):
        base = Path(args.target).expanduser().resolve()
        # tolerate being handed a harness dir rather than the project root
        for marker in (".claude/skills", ".cursor/rules", ".windsurf/rules", ".agents/vince"):
            suffix = Path(marker)
            if base.as_posix().endswith(suffix.as_posix()):
                return base.parents[len(suffix.parts) - 1]
        if base.name in {".claude", ".cursor", ".windsurf", ".agents", ".codex", ".gemini"}:
            return base.parent
        return base
    return Path.cwd()


def binding_dir(binding: dict, root: Path, scope: str) -> Path:
    if scope == "user":
        ud = binding.get("user_dir")
        if not ud:
            return None
        return Path(os.path.expanduser(ud)).resolve()
    return (root / binding["project_dir"]).resolve()


def manifest_path(root: Path, scope: str) -> Path:
    return (Path.home() if scope == "user" else root) / MANIFEST_REL


def migrate_v1(data: dict, base: Path, scope: str) -> dict:
    """A v1 manifest recorded one Claude-only install, with files relative to .claude/skills."""
    return {
        "manifest_version": MANIFEST_VERSION,
        "installs": {
            "claude": {
                "version": data.get("version", "unknown"),
                "source": data.get("source", ""),
                "scope": scope,
                "root": str(base / ".claude" / "skills"),
                "skills": data.get("skills", []),
                "files": data.get("files", {}),
            }
        },
    }


def load_manifest(root: Path, scope: str) -> dict:
    base = Path.home() if scope == "user" else root
    mf = manifest_path(root, scope)
    if mf.is_file():
        try:
            data = json.loads(mf.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"manifest_version": MANIFEST_VERSION, "installs": {}}
        if data.get("manifest_version") == MANIFEST_VERSION:
            return data
        migrated = migrate_v1(data, base, scope)
        migrated["_legacy"] = str(mf)
        return migrated
    legacy = base / LEGACY_MANIFEST_REL
    if legacy.is_file():
        try:
            data = json.loads(legacy.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
        migrated = migrate_v1(data, base, scope)
        migrated["_legacy"] = str(legacy)
        return migrated
    return {"manifest_version": MANIFEST_VERSION, "installs": {}}


def save_manifest(root: Path, scope: str, data: dict) -> Path:
    mf = manifest_path(root, scope)
    mf.parent.mkdir(parents=True, exist_ok=True)
    payload = {k: v for k, v in data.items() if not k.startswith("_")}
    payload["manifest_version"] = MANIFEST_VERSION
    payload["toolkit"] = "vince"
    mf.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return mf


def choose_bindings(args, root: Path, scope: str, manifest: dict) -> list:
    all_bindings = load_bindings()
    spec = (getattr(args, "binding", None) or "auto").strip()

    if spec == "all":
        chosen = list(all_bindings)
    elif spec == "auto":
        installed = list(manifest.get("installs", {}))
        if installed:
            chosen = [b for b in installed if b in all_bindings]
        else:
            chosen = []
            for bid, b in all_bindings.items():
                if scope == "user":
                    if bid == "generic":
                        continue      # no home-level AGENTS.md convention worth detecting
                    ud = b.get("user_dir")
                    if ud and Path(os.path.expanduser(ud)).parent.is_dir():
                        chosen.append(bid)
                else:
                    # `generic` detects on AGENTS.md, which most harnesses now read, so a
                    # project that has one gets it alongside its native binding rather than
                    # only as a fallback - it is the widest-reach binding there is.
                    if any((root / d).exists() for d in b.get("detect", [])):
                        chosen.append(bid)
            if not chosen:
                chosen = ["generic"]
    else:
        chosen = [s.strip() for s in spec.split(",") if s.strip()]
        unknown = [c for c in chosen if c not in all_bindings]
        if unknown:
            print(f"error: unknown binding(s): {', '.join(unknown)}", file=sys.stderr)
            print(f"       available: {', '.join(sorted(all_bindings))}", file=sys.stderr)
            return []

    if scope == "user":
        dropped = [b for b in chosen if not all_bindings[b].get("user_dir")]
        for b in dropped:
            print(f"  note: binding '{b}' has no user-scope location; skipping")
        chosen = [b for b in chosen if b not in dropped]
    return chosen


# --------------------------------------------------------------------------- commands

def cmd_bindings(_args) -> int:
    bindings = load_bindings()
    print(f"vince {version()} bindings ({toolkit_root() / 'bindings'})\n")
    for bid, b in sorted(bindings.items()):
        user = b.get("user_dir") or "-"
        print(f"  {bid:<9} {b['label']:<24} [{b['status']}]")
        print(f"            project: {b['project_dir']}   user: {user}")
        print(f"            layout: {b.get('layout')}/{b.get('frontmatter')}"
              f"   invoke: {b.get('invocation')}")
        if b.get("index"):
            print(f"            index: {b['index']}")
        print()
    print("status 'unverified' means the paths follow the runtime's documented convention but")
    print("were not confirmed against a live install. Run with --dry-run and check the paths.")
    return 0


def cmd_list(_args) -> int:
    names = skill_names()
    if not names:
        print(f"no skills found under {toolkit_root() / 'skills'}", file=sys.stderr)
        return 1
    print(f"vince {version()}  ({toolkit_root()})")
    for name in names:
        fields, _ = split_frontmatter(
            (toolkit_root() / "skills" / name / "SKILL.md").read_text(encoding="utf-8"))
        desc = fields.get("description", "")
        first = desc.split(". ")[0].rstrip(".")
        refs = len(reference_files(name))
        extra = f" (+{refs} reference)" if refs else ""
        print(f"  {name:<16}{extra}")
        print(f"      {first[:96]}")
    return 0


def cmd_install(args) -> int:
    root = resolve_root(args)
    scope = args.scope
    manifest = load_manifest(root, scope)
    bindings = load_bindings()
    chosen = choose_bindings(args, root, scope, manifest)
    if not chosen:
        return 1
    names = skill_names()
    if not names:
        print(f"error: no skills under {toolkit_root() / 'skills'}", file=sys.stderr)
        return 1

    print(f"vince {version()} -> {root}  (scope: {scope})")
    print(f"bindings: {', '.join(chosen)}")

    for bid in chosen:
        binding = bindings[bid]
        bdir = binding_dir(binding, root, scope)
        prior = manifest.get("installs", {}).get(bid, {})
        prior_files = prior.get("files", {})

        rendered = {}
        for skill in names:
            for rel, data in render_skill(binding, skill):
                rendered[rel] = data

        conflicts = []
        for rel, data in rendered.items():
            dst = bdir / rel
            if dst.is_file():
                current = sha256_file(dst)
                if current == sha256_bytes(data):
                    continue
                if prior_files.get(rel) != current:
                    conflicts.append(rel)
        if conflicts and not args.force:
            print(f"\n  [{bid}] refused: {len(conflicts)} file(s) differ from both the toolkit and")
            print("      the recorded install; they were edited in place or come from elsewhere:")
            for rel in conflicts:
                print(f"        {rel}")
            print("      Copy the edits back into the toolkit, or re-run with --force.")
            return 2

        print(f"\n  [{bid}] {binding['label']} -> {bdir}"
              f"{'  (dry run)' if args.dry_run else ''}")
        written = {}
        for rel, data in sorted(rendered.items()):
            dst = bdir / rel
            if not args.dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(data)
            written[rel] = sha256_bytes(data)
            print(f"      {rel}")

        for rel in [r for r in prior_files if r not in written]:
            stale = bdir / rel
            if stale.is_file():
                print(f"      removing stale {rel}")
                if not args.dry_run:
                    stale.unlink()

        manifest.setdefault("installs", {})[bid] = {
            "version": version(),
            "source": str(toolkit_root()),
            "scope": scope,
            "root": str(bdir),
            "skills": names,
            "files": written,
        }

    # One merged pointer block per index file, covering every binding installed here that
    # declares it - several harnesses commonly share AGENTS.md.
    if scope == "project":
        manifest["indexes"] = write_indexes(root, manifest, args.dry_run)
    elif any(bindings[b].get("index") for b in chosen):
        print("\n  note: index blocks are project-scope only, skipped for user scope")

    if not args.dry_run:
        mf = save_manifest(root, scope, manifest)
        print(f"\nmanifest: {mf}")
        legacy = manifest.get("_legacy")
        if legacy and Path(legacy).is_file():
            Path(legacy).unlink()
            print(f"removed legacy manifest: {legacy}")
    print(f"{'would install' if args.dry_run else 'installed'} {len(names)} skills "
          f"across {len(chosen)} binding(s)")
    return 0


def index_groups(manifest: dict) -> dict:
    """index file -> [binding descriptors], for every binding recorded in the manifest."""
    bindings = load_bindings()
    groups = {}
    for bid in manifest.get("installs", {}):
        binding = bindings.get(bid)
        if binding and binding.get("index"):
            groups.setdefault(binding["index"], []).append(binding)
    for name in groups:
        groups[name].sort(key=lambda b: b["id"])
    return groups


def write_indexes(root: Path, manifest: dict, dry_run: bool) -> dict:
    recorded = {}
    for name, group in index_groups(manifest).items():
        block = render_index(group)
        action = write_index(root / name, block, dry_run)
        recorded[name] = {
            "hash": sha256_bytes(block.encode("utf-8")),
            "bindings": [b["id"] for b in group],
        }
        print(f"\n  {name}: pointer block {action} "
              f"({', '.join(b['id'] for b in group)})")
    return recorded


def inspect(root: Path, scope: str, manifest: dict) -> dict:
    """Per-binding health: missing, drifted, foreign, stale, outdated."""
    bindings = load_bindings()
    report = {}
    for bid, record in manifest.get("installs", {}).items():
        binding = bindings.get(bid)
        entry = {"missing": [], "drifted": [], "foreign": [], "stale": [], "new": [],
                 "version": record.get("version"), "root": record.get("root"),
                 "unknown_binding": binding is None, "index": None}
        if binding is None:
            report[bid] = entry
            continue
        bdir = Path(record.get("root") or binding_dir(binding, root, scope))
        rendered = {}
        for skill in skill_names():
            for rel, data in render_skill(binding, skill):
                rendered[rel] = sha256_bytes(data)

        for rel, recorded in record.get("files", {}).items():
            p = bdir / rel
            if not p.is_file():
                entry["missing"].append(rel)
            else:
                current = sha256_file(p)
                if rel not in rendered:
                    entry["stale"].append(rel)
                elif current != rendered[rel]:
                    entry["foreign"].append(rel) if current != recorded else \
                        entry["drifted"].append(rel)
        for rel in rendered:
            if rel not in record.get("files", {}):
                entry["new"].append(rel)

        report[bid] = entry
    return report


def inspect_indexes(root: Path, scope: str, manifest: dict) -> dict:
    """index file -> None (healthy) | 'missing' | 'outdated' | 'duplicated'."""
    if scope != "project":
        return {}
    out = {}
    for name, group in index_groups(manifest).items():
        path = root / name
        want = render_index(group)
        if not path.is_file():
            out[name] = "missing"
            continue
        text = path.read_text(encoding="utf-8")
        if INDEX_BEGIN not in text or INDEX_END not in text:
            out[name] = "missing"
        elif text.count(INDEX_BEGIN) > 1:
            out[name] = "duplicated"
        else:
            start = text.index(INDEX_BEGIN)
            end = text.index(INDEX_END) + len(INDEX_END)
            out[name] = None if text[start:end] == want.rstrip("\n") else "outdated"
    return out


def _print_report(root: Path, scope: str, manifest: dict) -> int:
    print(f"toolkit  : vince {version()}  ({toolkit_root()})")
    print(f"target   : {root}  (scope: {scope})")
    if not manifest.get("installs"):
        hint = " - legacy manifest found, re-run install to migrate" if manifest.get("_legacy") else ""
        print(f"status   : not installed{hint}")
        return 1

    report = inspect(root, scope, manifest)
    problems = 0
    for bid, entry in sorted(report.items()):
        if entry["unknown_binding"]:
            print(f"\n  [{bid}] installed, but this toolkit has no such binding - orphaned")
            problems += 1
            continue
        counts = {k: len(entry[k]) for k in ("missing", "drifted", "foreign", "stale", "new")}
        outdated = entry["version"] != version()
        healthy = not any(counts.values()) and not outdated and not entry["index"]
        print(f"\n  [{bid}] {entry['root']}")
        print(f"      version {entry['version']}"
              f"{'  ! toolkit is ' + version() if outdated else ''}")
        summary = ", ".join(f"{n} {k}" for k, n in counts.items() if n)
        print(f"      files: {summary or 'all current'}")
        for kind in ("missing", "drifted", "stale", "new", "foreign"):
            for rel in entry[kind]:
                print(f"        {kind:<8} {rel}")
        if not healthy:
            problems += 1
        else:
            print("      healthy")

    indexes = inspect_indexes(root, scope, manifest)
    if indexes:
        print("")
        for name, state in sorted(indexes.items()):
            print(f"  {name}: {state or 'current'}")
            if state:
                problems += 1
    return 1 if problems else 0


def cmd_status(args) -> int:
    root = resolve_root(args)
    return _print_report(root, args.scope, load_manifest(root, args.scope))


def cmd_doctor(args) -> int:
    root = resolve_root(args)
    scope = args.scope
    manifest = load_manifest(root, scope)
    rc = _print_report(root, scope, manifest)

    if not manifest.get("installs"):
        print("\ndiagnosis: nothing installed here. Run:")
        print(f"  python {Path(__file__).name} install --target {root}")
        return 1

    report = inspect(root, scope, manifest)
    foreign = {b: e["foreign"] for b, e in report.items() if e.get("foreign")}
    if rc == 0:
        print("\ndiagnosis: healthy - every installed file matches the toolkit.")
        return 0

    print("\ndiagnosis:")
    for bid, entry in sorted(report.items()):
        if entry.get("unknown_binding"):
            print(f"  [{bid}] orphaned install; uninstall it or restore the binding file")
        if entry.get("missing"):
            print(f"  [{bid}] {len(entry['missing'])} file(s) deleted since install; reinstall restores them")
        if entry.get("drifted") or entry.get("new") or entry["version"] != version():
            print(f"  [{bid}] behind the toolkit; reinstall brings it current")
        if entry.get("stale"):
            print(f"  [{bid}] {len(entry['stale'])} file(s) the toolkit no longer ships; reinstall removes them")
        if entry.get("foreign"):
            print(f"  [{bid}] {len(entry['foreign'])} file(s) edited in place; copy the edits into "
                  f"{toolkit_root() / 'skills'} first, or --fix --force to discard them")
    for name, state in sorted(inspect_indexes(root, scope, manifest).items()):
        if state:
            print(f"  {name} pointer block {state}; reinstall rewrites it")

    if not args.fix:
        print("\nrun with --fix to repair everything except in-place edits.")
        return rc

    if foreign and not args.force:
        print("\nnot repairing: in-place edits would be lost. Copy them into the toolkit, or "
              "add --force.")
        return 2

    print("\nrepairing...")
    fix_args = argparse.Namespace(
        target=str(root) if scope == "project" else None, scope=scope,
        binding=",".join(sorted(b for b, e in report.items() if not e["unknown_binding"])) or "auto",
        dry_run=False, force=True,
    )
    if not fix_args.binding:
        return rc
    rc2 = cmd_install(fix_args)
    if rc2 != 0:
        return rc2
    print("\nre-checking...")
    return _print_report(root, scope, load_manifest(root, scope))


def cmd_uninstall(args) -> int:
    root = resolve_root(args)
    scope = args.scope
    manifest = load_manifest(root, scope)
    if not manifest.get("installs"):
        print(f"nothing to uninstall at {root} (no manifest)")
        return 1

    spec = (args.binding or "all").strip()
    targets = list(manifest["installs"]) if spec in ("all", "auto") else \
        [s.strip() for s in spec.split(",") if s.strip()]
    targets = [t for t in targets if t in manifest["installs"]]
    if not targets:
        print("nothing matching to uninstall")
        return 1

    for bid in targets:
        record = manifest["installs"][bid]
        bdir = Path(record["root"])
        modified = [rel for rel, digest in record.get("files", {}).items()
                    if (bdir / rel).is_file() and sha256_file(bdir / rel) != digest]
        if modified and not args.force:
            print(f"  [{bid}] refused: these installed files were modified in place:")
            for rel in modified:
                print(f"      {rel}")
            print("      Re-run with --force to remove them anyway.")
            return 2

        verb = "would remove" if args.dry_run else "removing"
        print(f"  [{bid}] {bdir}")
        for rel in sorted(record.get("files", {})):
            p = bdir / rel
            if p.is_file():
                print(f"      {verb} {rel}")
                if not args.dry_run:
                    p.unlink()
        if not args.dry_run:
            for sub in sorted(bdir.rglob("*"), reverse=True):
                if sub.is_dir() and not any(sub.iterdir()):
                    sub.rmdir()
            if bdir.is_dir() and not any(bdir.iterdir()):
                bdir.rmdir()
        if not args.dry_run:
            del manifest["installs"][bid]

    # Index files are shared: rewrite for whatever remains, strip only when nothing is left.
    if scope == "project":
        before = set(manifest.get("indexes", {}))
        remaining = index_groups(manifest)
        for name in sorted(before - set(remaining)):
            if strip_index(root / name, args.dry_run):
                print(f"  {name}: {verb} pointer block")
        if remaining and not args.dry_run:
            manifest["indexes"] = write_indexes(root, manifest, args.dry_run)
        elif not remaining:
            manifest.pop("indexes", None)

    if not args.dry_run:
        if manifest["installs"]:
            save_manifest(root, scope, manifest)
        else:
            mf = manifest_path(root, scope)
            mf.unlink(missing_ok=True)
            if mf.parent.is_dir() and not any(mf.parent.iterdir()):
                mf.parent.rmdir()
    print(f"{'would uninstall' if args.dry_run else 'uninstalled'} {len(targets)} binding(s)")
    return 0


# --------------------------------------------------------------------------- cli

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="install.py",
        description="Install the Vince skills into any agent harness.")
    sub = parser.add_subparsers(dest="command", required=True)

    def target_args(p, with_binding=True):
        p.add_argument("--target", help="project root (default: the current directory)")
        p.add_argument("--scope", choices=("project", "user"), default="project",
                       help="project = this repo (default), user = your home harness dirs")
        if with_binding:
            p.add_argument("--binding", default="auto",
                           help="auto (detect, default), all, or a comma-separated list")

    p = sub.add_parser("install", help="render and copy the skills into a harness")
    target_args(p)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true", help="overwrite files edited in place")
    p.set_defaults(func=cmd_install)

    p = sub.add_parser("status", help="report installed versions and drift")
    target_args(p, with_binding=False)
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("doctor", help="diagnose, and with --fix repair, an install")
    target_args(p, with_binding=False)
    p.add_argument("--fix", action="store_true", help="repair what can be repaired")
    p.add_argument("--force", action="store_true", help="repair even over in-place edits")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("uninstall", help="remove installed skills and index blocks")
    target_args(p)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_uninstall)

    p = sub.add_parser("list", help="list the skills this toolkit ships")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("bindings", help="list the harness bindings this toolkit knows")
    p.set_defaults(func=cmd_bindings)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
