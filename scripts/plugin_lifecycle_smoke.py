#!/usr/bin/env python3
"""Prove Git-backed install/upgrade/rollback in one isolated Codex marketplace.

Uses a disposable local bare Git remote and two fixture versions, not production branches.
No model/API turn, credentials or normal Codex configuration required.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from plugin_smoke import native_probe, run

ROOT = Path(__file__).resolve().parent.parent


def smoke(codex):
    with tempfile.TemporaryDirectory(prefix="vince-git-lifecycle-") as raw:
        base = Path(raw)
        source, remote, project = base / "source", base / "remote.git", base / "project"
        shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns(".git", "__pycache__", "dist"))
        run(["git", "init", "--bare", "-q", str(remote)])
        run(["git", "--git-dir", str(remote), "symbolic-ref", "HEAD", "refs/heads/main"])
        remote_url = "https://vince-fixture.invalid/remote.git"
        run(["git", "init", "-q", "-b", "main", str(source)])
        run(["git", "-C", str(source), "remote", "add", "origin", remote.as_uri()])
        project.mkdir()
        run(["git", "init", "-q", str(project)])
        marker = project / "user-data.txt"
        marker.write_bytes(b"project data must survive every lifecycle step\n")
        original = marker.read_bytes()
        env = dict(os.environ, CODEX_HOME=str(base / "isolated-codex"), VINCE_ALLOWED_ROOTS=str(project))
        # Codex accepts HTTPS Git sources, not file: URLs. Rewrite only this exact synthetic
        # URL inside child Git processes to a real local bare remote; no server/network needed.
        env.update(GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0=f"url.{remote.as_uri()}.insteadOf",
                   GIT_CONFIG_VALUE_0=remote_url, GIT_ALLOW_PROTOCOL="file")
        Path(env["CODEX_HOME"]).mkdir()
        initial = (source / "VERSION").read_text().strip()
        parts = initial.split(".")
        newer = ".".join([*parts[:-1], str(int(parts[-1]) + 1)])
        skills = sorted(p.parent.name for p in (source / "skills").glob("vince-*/SKILL.md"))

        def git(*args):
            return run(["git", "-C", str(source), "-c", "user.name=Vince fixture",
                        "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false", *args])

        def commit(version):
            (source / "VERSION").write_text(version + "\n")
            for name in ("plugin.json", ".codex-plugin/plugin.json", ".claude-plugin/plugin.json"):
                path = source / name
                data = json.loads(path.read_text())
                data["version"] = version
                path.write_text(json.dumps(data, indent=2) + "\n")
            git("add", *[p.name for p in sorted(source.iterdir()) if p.name != ".git"])
            git("commit", "-q", "-m", "Fixture version " + version)
            git("push", "-q", "origin", "main")
            run(["git", "--git-dir", str(remote), "update-server-info"])

        def cli(*args):
            return run([codex, "plugin", *args], env=env)

        def verify(version):
            native_probe(codex, env, project, version, skills)
            candidates = list(Path(env["CODEX_HOME"]).rglob(f"{version}/skills/vince-review/SKILL.md"))
            if not candidates:
                raise ValueError("Installed version cache missing: " + version)
            for shared in (source / "skills/_shared").glob("*.md"):
                if (candidates[0].parent / "reference" / shared.name).read_bytes() != shared.read_bytes():
                    raise ValueError("Git installation omitted canonical shared resources")
            if marker.read_bytes() != original:
                raise ValueError("Lifecycle changed project data")
            listing = json.loads(cli("marketplace", "list", "--json"))
            matching = [item for item in listing.get("marketplaces", []) if item.get("name") == "vince-gate"]
            if len(matching) != 1 or matching[0].get("marketplaceSource", {}).get("sourceType") != "git":
                raise ValueError("Expected exactly one Vince marketplace: " + json.dumps(listing)[:2000])

        commit(initial)
        git("tag", "known-good")
        git("push", "-q", "origin", "refs/tags/known-good")
        run(["git", "--git-dir", str(remote), "update-server-info"])
        cli("marketplace", "add", remote_url, "--ref", "main", "--json")
        cli("add", "vince-gate@vince-gate", "--json")
        verify(initial)
        commit(newer)
        cli("marketplace", "upgrade", "vince-gate", "--json")
        cli("add", "vince-gate@vince-gate", "--json")
        verify(newer)
        # Rollback changes the ref of the same named marketplace, never a new identity.
        cli("marketplace", "remove", "vince-gate")
        cli("marketplace", "add", remote_url, "--ref", "known-good", "--json")
        cli("add", "vince-gate@vince-gate", "--json")
        verify(initial)
        return {"marketplace": "vince-gate", "plugin": "vince-gate@vince-gate",
                "fixture_versions": [initial, newer, initial], "install": "PASS",
                "upgrade": "PASS", "rollback": "PASS", "project_data": "PRESERVED",
                "marketplace_count": 1}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", required=True)
    args = parser.parse_args()
    try:
        report = smoke(args.codex)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        sys.stderr.write(str(error) + "\n")
        return 1
    sys.stdout.write(json.dumps(report, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
