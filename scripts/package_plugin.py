#!/usr/bin/env python3
"""Build the desktop plugin ZIP and SHA256SUMS reproducibly, without executing project code."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent
FILES = ("plugin.json", "mcp.json", ".mcp.json", ".codex-plugin/plugin.json",
         ".claude-plugin/plugin.json", ".claude-plugin/marketplace.json",
         ".agents/plugins/marketplace.json", "VERSION", "LICENSE", "README.md",
         "INSTALL.md", "USER-GUIDE.md", "CHANGELOG.md")
DIRECTORIES = ("skills", "scripts", "templates", "bindings", "docs", "assets", "policies")


def shared_resources(root, sync=False):
    """Keep native Git installs as complete as ZIP installs; canonical text stays in _shared."""
    stale = []
    for skill in sorted((root / "skills").glob("vince-*/SKILL.md")):
        for source in sorted((root / "skills/_shared").glob("*.md")):
            destination = skill.parent / "reference" / source.name
            if not destination.is_file() or destination.read_bytes() != source.read_bytes():
                if sync:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(source.read_bytes())
                else:
                    stale.append(str(destination.relative_to(root)))
    if stale:
        raise ValueError("Native shared resources are missing/stale; run python3 scripts/package_plugin.py --sync-shared: " + ", ".join(stale))


def validate(root):
    shared_resources(root)
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Invalid release version")
    for name in ("plugin.json", ".codex-plugin/plugin.json", ".claude-plugin/plugin.json"):
        manifest = json.loads((root / name).read_text(encoding="utf-8"))
        if manifest.get("version") != version or manifest.get("name") != "vince-gate":
            raise ValueError("Plugin version/name mismatch in " + name)
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(r"(?ms)^## v" + re.escape(version) + r"\b[^\n]*\n(.*?)(?=^## |\Z)", changelog)
    if not match:
        raise ValueError("Missing version in changelog")
    return version, match.group(0).strip() + "\n"


def entries(root):
    result = {}
    paths = [root / f for f in FILES]
    for directory in DIRECTORIES:
        paths.extend(sorted((root / directory).rglob("*")))
    for path in paths:
        relative = path.relative_to(root)
        if "__pycache__" in relative.parts or path.suffix in (".pyc", ".pyo"):
            continue
        if path.is_symlink():
            raise ValueError("Symlinks are not allowed in plugin packages: " + str(relative))
        if path.is_file():
            result[relative.as_posix()] = path.read_bytes()
        elif str(relative) in FILES:
            raise ValueError("Missing package file: " + str(relative))
    # Native plugins bypass the legacy installer, so materialize its shared references here.
    shared = root / "skills" / "_shared"
    for entry in sorted((root / "skills").glob("vince-*/SKILL.md")):
        for reference in sorted(shared.glob("*.md")):
            destination = f"skills/{entry.parent.name}/reference/{reference.name}"
            result.setdefault(destination, reference.read_bytes())
    return result


def build(root, output):
    version, notes = validate(root)
    content = entries(root)
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"vince-gate-{version}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name, data in sorted(content.items()):
            item = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            bundle.writestr(item, data)
    (output / "release-notes.md").write_text(notes, encoding="utf-8")
    sums = []
    for path in (archive, output / "release-notes.md"):
        sums.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")
    (output / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--sync-shared", action="store_true", help="Regenerate tracked native skill resources from skills/_shared")
    args = parser.parse_args()
    try:
        if args.sync_shared:
            shared_resources(ROOT, sync=True)
            if not args.output:
                sys.stdout.write("Native shared resources synchronized\n")
                return 0
        if not args.output:
            parser.error("--output is required unless --sync-shared is used")
        archive = build(ROOT, args.output.resolve())
    except (ValueError, OSError, json.JSONDecodeError) as error:
        sys.stderr.write(str(error) + "\n")
        return 1
    sys.stdout.write(str(archive) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
