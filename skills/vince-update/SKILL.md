---
name: vince-update
description: Move a vince-gate install to a newer (or older) release safely - finds the toolkit, compares the installed version against available tags, reads the changelog between them, refuses to trample skills edited in place, reinstalls at the recorded scope and bindings, and then migrates the project's .vince config so the new version's fields actually exist rather than being silently absent. Triggers on "update vince", "upgrade vince-gate", "is vince up to date", "roll back vince", "what version of vince am I on".
---

# Vince — Update

Upgrading the files is the easy half and `install.py` already does it. The half that gets
missed: **a new release reads config fields that an older profile does not have.** Nothing errors
— the skills just quietly fall back, and the capability the user upgraded for never switches on.
Closing that gap is the point of this skill.

Two rules throughout. **Never force past an in-place edit** — that is someone's improvement that
never made it home, and discarding it is the one unrecoverable thing here. And **never invent a
config value while migrating**; a new field arrives `unknown` or `blocked` until something is
actually run.

## 1. Locate and orient

```bash
python <toolkit>/scripts/install.py status --scope user     # or --target <project>
```

The toolkit path is the `source` field in `~/.vince/install.json` or `<project>/.vince/install.json`.
Note three things: the **installed** version, the **toolkit** version and git ref, and the
**scope and bindings** recorded in the manifest — the reinstall has to match those, not your
guess at them.

```bash
cd <toolkit> && git fetch --tags && git tag -l && git describe --tags --always --dirty
```

If installed, toolkit and latest tag all agree, say so and stop. "Already current" is a complete
answer and takes ten seconds to establish.

## 2. Decide the target, and say what changes

Default target is the newest tag, not `main` — `main` is wherever development happens to be.
The user may name an older tag; rolling back is the same procedure with a different target.

Read `CHANGELOG.md` **between the installed version and the target** and report, before touching
anything:

- what the user actually gains, in a sentence or two per release;
- anything that breaks, and what it costs;
- the **Upgrade notes** of every intervening release — those name the config that needs to exist,
  and they are the input to step 5.

Skipping several versions means every intervening release's upgrade notes apply, not just the
newest one's.

## 3. Pre-flight, and stop if any of these are true

```bash
git -C <toolkit> status --porcelain                       # uncommitted work in the clone
python <toolkit>/scripts/install.py doctor --scope user   # in-place edits at the target
```

| Finding | Why it stops the update |
|---------|------------------------|
| Uncommitted changes in the toolkit clone | `git checkout <tag>` may not be clean, and unpushed improvements are easy to lose. Show them; let the user commit, stash or discard. |
| Files edited in place at the target (`foreign`) | Someone improved a skill and it never went home. Show the diff. The fix is to copy the change into `<toolkit>/skills/` and reinstall — **not** `--force`. |
| A task in flight with an open ledger | Changing the skills mid-task changes the rules mid-task. Finish or park it first. |

Each of these is a stop with a recommendation, not a prompt to improvise.

## 4. Move and reinstall

```bash
git -C <toolkit> checkout <tag>
git -C <toolkit> describe --tags                                   # confirm you are on it
python <toolkit>/scripts/install.py install <recorded scope/bindings>
python <toolkit>/scripts/install.py status  <same flags>           # must be healthy, exit 0
```

Reinstall at the **manifest's** scope and bindings. Silently switching a project-scoped install
to user scope, or dropping a binding a teammate relies on, is a change nobody asked for.

Installed as a Claude Code plugin instead? Then the toolkit is managed by the plugin system:
`/plugin marketplace update` and reinstall, or pin a tag via `extraKnownMarketplaces` with a
`ref`. Steps 5 and 6 still apply — the plugin updates files, not config.

## 5. Migrate the config — the part only this skill does

For each project that has a `.vince/` directory, walk the intervening releases' upgrade notes and
make the fields exist. Add the **section with an honest status**, never a fabricated value:

| Situation | What to write |
|-----------|---------------|
| New field, cheap to determine and safe to run | run it, record the verified value |
| New field needing infra, credentials or a running environment | `blocked — <what is needed>` |
| New field you cannot determine | `unknown — <what you tried>` |
| New *section* the release added | add it with its status marker, even if empty |
| A field the release renamed | move the value, keep the old one out |

Concretely, at time of writing: 0.2.0 added `mutation` (tool + diff-scoped command) and
`reviewer_model`; 0.3.0 added the section-status vocabulary, the `Inherits from` header, and the
hub/repo split for workspaces. A profile written before those has none of them, and the skills
that read them fall back silently.

Also check the artifacts around the profile: does `.vince/lessons.md` exist, is `.vince/tasks/`
still gitignored, does a hub-based workspace have both levels. Then **tell the user which fields
you left `unknown` or `blocked` and what would resolve each** — an upgrade that quietly parks
three fields as unknown has not finished, it has just stopped.

## 6. Verify and report

```bash
python <toolkit>/scripts/install.py doctor <scope flags>    # expect healthy, exit 0
```

Then, in the harness you are running in, confirm the skills are still discoverable — files being
in the right place is not the same as the harness finding them, especially if the release changed
a binding.

Report: version moved from → to, scope and bindings, what the user gains in practice, which
config fields were added and their status, anything still needing their input, and anything you
stopped on. If you stopped in pre-flight, that is the report — say what blocked it and what
clears it.

## Rolling back

Same procedure, older tag. Two things worth knowing, both of which make it safer than it sounds:

- Reinstall **removes files the older version does not ship**, so you land on that version's
  skill set rather than a mixture.
- Project artifacts — profiles, ledgers, verdicts, lessons — are untouched. They are the user's,
  not the toolkit's, and older skills read newer profiles fine: an unknown section is ignored,
  not an error. So a rollback does not need a config migration, and you should not strip fields
  to "match" the older version.

## Boundaries

- **Never `--force`** past an in-place edit or a modified installed file without the user
  explicitly deciding, having seen the diff.
- **Never invent a config value** to make a migration look complete.
- Do not upgrade a project mid-task. Finish the ledger first.
- Do not switch scope, bindings or install method as a side effect. If the current setup is
  wrong, say so and let the user choose.
- Related: [`vince-doctor`](../vince-doctor/SKILL.md) is for "something is broken, repair it";
  this skill is for "something newer exists, move to it". Update calls doctor's checks; doctor
  never changes version.
