# The installer CLI

Every flag, every drift state, every exit code. To *get started*, use
[INSTALL.md](../INSTALL.md) instead — it has a block you paste to your agent and the four-command
manual equivalent.

`scripts/install.py` renders the canonical skills into whatever shape your harness wants and
tracks every byte it wrote. Python 3.8+, no dependencies, no network.

## Location independence

The toolkit resolves its own root from the script's location, or from `$VINCE_HOME` if set.
Clone or copy this directory anywhere — there is no required path, and nothing is written outside
the target's harness directories and `.vince/`.

## Commands

```bash
python scripts/install.py bindings
python scripts/install.py list
python scripts/install.py install   [--target DIR] [--scope project|user]
                                    [--binding auto|all|claude,cursor,...] [--dry-run] [--force]
python scripts/install.py status    [--target DIR] [--scope project|user]
python scripts/install.py doctor    [--target DIR] [--scope project|user] [--fix] [--force]
python scripts/install.py uninstall [--target DIR] [--scope project|user]
                                    [--binding ...] [--dry-run] [--force]
```

Exit codes: **0** healthy or done, **1** problems found (or not installed), **2** refused to
clobber something.

`--target` is the project root; being handed a `.claude`, `.cursor` or skills directory works too
— it walks up. Without `--target`, `--scope project` uses the current directory and `--scope
user` uses your home harness directories.

**Project scope** is right when the skills should travel with the repo, when a team should get
the gate from a checkout, or when different projects need different versions. **User scope** is
right when you want one Vince everywhere and no footprint in any repo.

## Bindings

`--binding auto` (the default) detects which harnesses the target uses, or refreshes exactly what
is already installed there, or falls back to `generic` if it finds nothing. See
[harnesses.md](harnesses.md) for the full model and how to add a runtime.

## What install writes

- The skills, rendered per binding (`.claude/skills/…`, `.cursor/rules/…`, and so on).
- A merged pointer block in each binding's index file (`AGENTS.md`, `GEMINI.md`) — project scope
  only, one block per file covering every binding that shares it.
- `<target>/.vince/install.json` — the manifest: per binding, the version, source path, skill
  list, a SHA-256 per installed file, and the index hashes.

Nothing else. No hooks, no settings edits, no global state. `.vince/install.json` records absolute
paths from your machine, so gitignore it in a shared repo.

## Versions

Releases are git tags; the installer installs whatever is checked out. `status` prints the
release from `VERSION` **and** the git ref actually checked out, so `0.2.0 (v0.2.0-3-gabc-dirty)`
tells you the clone is mid-line or modified rather than on a clean release. Full upgrade, pin
and rollback recipes are in [INSTALL.md](../INSTALL.md#versions).

## Updating

Pull or edit the toolkit, then re-run `install` against the same target. Files a previous install
shipped that the new one does not are removed, index blocks are rewritten, and the manifest is
refreshed. `status` shows what is behind:

```
toolkit  : vince 0.2.0  (…/vince)
target   : …/project  (scope: project)

  [claude] …/project/.claude/skills
      version 0.1.0  ! toolkit is 0.2.0
      files: 1 drifted, 2 new
        drifted  vince-review/SKILL.md
        new      vince-doctor/SKILL.md

  AGENTS.md: outdated
```

## Drift and repair

`doctor` is `status` plus a diagnosis and, with `--fix`, the repair:

```bash
python scripts/install.py doctor --target .
python scripts/install.py doctor --target . --fix
```

It distinguishes four things, and only one of them is dangerous to fix:

| State | Meaning | `--fix` |
|-------|---------|---------|
| `missing` | deleted since install | restored |
| `drifted` | the toolkit moved on | rewritten |
| `stale` | the toolkit no longer ships it | removed |
| `new` | the toolkit added it | installed |
| `foreign` | **edited in place** — differs from both the toolkit and the manifest | refused |

A `foreign` file is not corruption: someone improved a skill at the target and it never made it
home. The intended fix is to copy the change into `<toolkit>/skills/` and reinstall — **the
toolkit is the source of truth**, and an improvement living in one project's skills directory is
an improvement no other project gets. `--fix --force` discards it; use that only when you are
certain the local copy is disposable.

`doctor` also reports index blocks that are missing, outdated or duplicated, and installs whose
binding no longer exists in the toolkit (orphans).

For the layer above this — is the *profile* still true, are there ledgers that never got
reviewed, are there leaked worktrees — use the `vince-doctor` skill, which validates by running
things rather than by hashing them.

## Uninstall

Removes only the files in the manifest, then any directories left empty, then rewrites each
shared index block for whatever bindings remain — stripping the block entirely (and deleting the
file if nothing else was in it) when the last one goes. Files you added or edited are left in
place unless you pass `--force`. Nothing outside the manifest is ever deleted.

```bash
python scripts/install.py uninstall --target . --binding cursor   # one binding
python scripts/install.py uninstall --target .                    # all of them
```

## Verify an install

```bash
python scripts/install.py install --target /tmp/probe --binding all --dry-run
python scripts/install.py install --target /tmp/probe --binding all
python scripts/install.py doctor  --target /tmp/probe          # expect: healthy, exit 0
python scripts/install.py uninstall --target /tmp/probe
```

Then, in a real session at the target, confirm the skills are listed and that `/vince-implement`
resolves. That last step is the only one that proves a binding actually works — everything before
it proves the files are in the right place.
