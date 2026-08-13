---
name: vince-doctor
description: Diagnose and repair a broken or drifted Vince setup - checks the install across every harness binding, validates the project profile against the repo it describes (commands that no longer run, branches that no longer resolve, paths that no longer exist), finds orphaned task dirs and unreviewed work, and fixes what is safely fixable. Run when something about Vince behaves oddly, after a big refactor, or when a skill references something that is not there. Triggers on "vince is broken", "vince doctor", "profile is wrong", "skills not loading", "check the vince setup".
---

# Vince — Doctor

Vince degrades quietly. A renamed test script, a retired branch, a skills directory that a
harness update moved — none of these announce themselves, and each one makes the next task's
evidence a little more fictional. This skill finds that decay and repairs what it safely can.

**Repair, never paper over.** Every fix is either verified by running something, or it is not a
fix. A profile field you "corrected" without running the new command is a new lie replacing an
old one.


## Voice

Read `reference/voice.md` and talk that way: friendly and dry, brutally honest about facts, and
never assuming the reader knows the jargon — keep the precise term, add the plain-English
translation. Jokes never carry information, and they switch off entirely for anything
destructive, any security or data finding, and any time you were wrong.
A health report can be dry and funny. The moment you are about to change or delete something, it goes flat.


Also read `reference/token-discipline.md`. Rigour is not negotiable; what it costs is. Read
narrowly, bound long commands, run `scripts/check.py` instead of ten shell commands, spawn a
subagent only when a fresh context is the point, and lean on the ledger so you can reset context
rather than carrying it.

## 1. The install

```bash
python <toolkit>/scripts/install.py doctor --target <project root>
python <toolkit>/scripts/install.py doctor --scope user
```

The toolkit path is recorded as `source` in `.vince/install.json` (project) or
`~/.vince/install.json` (user). The doctor reports, per binding: files missing since install,
files behind the toolkit, files the toolkit no longer ships, files edited in place, an index
block (`AGENTS.md` and friends) that is missing, stale or duplicated, and an install whose
version is behind.

- Everything except in-place edits: `doctor --fix`.
- In-place edits are **not** drift to discard. Someone improved a skill in the target and it
  never made it home. Copy the change into `<toolkit>/skills/`, reinstall, and only then
  consider `--fix --force`.
- Skills not loading at all? Confirm the harness's own discovery path matches the binding
  (`install.py bindings`), and that the frontmatter dialect is the one that harness expects.
  A binding marked `unverified` is a good first suspect.

## 2. The profile

Resolve it first — `install.py where --repo <repo>` — because per-repo config lives outside the
repo by default. A doctor that validates a path nobody uses reports a healthy fiction.

The profile is the load-bearing file. Validate it **by running it**, not by reading it.

**Two levels?** Check both, and check them differently — a hub profile cannot verify a command,
so running its per-stack defaults is not its job and their being unverified is not a fault:

| Check | Hub profile | Repo profile |
|-------|-------------|--------------|
| Commands | do **not** mark verified; confirm they are labelled `inferred, unverified` | run every one |
| Baseline | must not claim one | run the suite, compare, restamp |
| Repo map | resolve a sample of repos | n/a |
| Integration branch | resolves in a sample of repos | resolves here |
| Paths | exist | exist |
| Sections | none blank — `blocked`/`unknown` instead | same |

Two hub-level findings worth reporting on their own: **a hub profile claiming a verified
command or a baseline** (structurally impossible — someone pasted it), and **repos that have
been worked in but never got a repo profile**, which means first-touch promotion is being
skipped and the estate's values stay unverified indefinitely. List those repos.

Then, for the profile at hand:

| Field | Check | If it fails |
|-------|-------|-------------|
| Suite / build / lint commands | run each one | re-derive from the manifest, scripts, CI config; verify; record under *Corrections* |
| Baseline counts | run the suite, compare | update the baseline and stamp the commit it was taken on |
| Integration branch | `git rev-parse --verify origin/<branch>` | find the real one (`git remote show origin`), update |
| Every path in the profile | does it exist | repair or drop the row; a path that moved usually means a section is stale |
| Isolation key | grep a couple of recent queries for it | if queries no longer carry it, that is a *finding about the codebase*, not a profile error — report it |
| Wire-proof rigs | does the rig still exist and start | repair, or mark `unknown` rather than leaving a fiction |
| Locale files | do they exist, do key sets still match | repair the paths; a parity failure is a codebase finding |
| `dod_extras` gates | run each gate's verify command | repair or remove, and say which |

Rules for repairs:

- **Two failures means a refresh, not a patch.** If more than one field is wrong, the profile
  has drifted as a whole — run `vince-setup` instead of nursing it row by row.
- **Never widen a claim.** If you cannot determine a field, write `unknown — <what you tried>`.
  An honest gap beats a confident guess, because the next session will trust whatever is there.
- **Record every repair** under the profile's *Corrections* section with the date, what was
  wrong, what it is now, and what proved it.

## 3. The work in flight

Scan `<task root>/active/` (default `.vince/tasks/active/`) for state that has gone stale:

- A ledger whose `Reviewer verdict:` is still `NOT-RUN` while the branch is merged — work
  shipped without a review. Report it; do not retro-stamp a verdict.
- A ledger with `RED` or `BLOCKED` rows and no activity for weeks — abandoned, or blocked on
  something nobody chased. List it for the user.
- A task dir with no `completion-documentation.md` whose work is merged.
- A dir under `active/` whose branch is gone or merged — a candidate for `archive/`. Moving it
  is the user's call; propose, do not sweep.
- Orphaned worktrees from tasks that ended without teardown: `git worktree list`, cross-checked
  against the ledgers' *Session resources* blocks. Report them with what is uncommitted in each.
  **Never remove a worktree that is dirty or has unpushed commits**, and never remove one you
  cannot tie to a completed task.
- Leaked processes and undeletable directories are `vince-cleanup`'s job, not this skill's —
  report what you noticed and hand off. Doctor diagnoses the setup; cleanup reclaims resources,
  and it kills things, so it gets its own deliberate invocation.

## 4. The loop itself

- Is the resolved `lessons.md` present and being read? A project with a dozen archived tasks and no
  lessons file means `vince-learn` has never run — say so, and offer to run it over the archive.
- Are metrics being written (`.vince/metrics.jsonl`)? Not fatal, but without them `vince-learn`
  is reasoning from memory rather than from data.
- Do any lessons contradict the current profile? A lesson that says "the suite command is X"
  while the profile says Y means one of them is wrong. Resolve by running both.

## Output

A short report, in this order — problems first, and always concrete:

```markdown
## Vince doctor — <project> — <date>

**Install:** <binding: state>, … | **Profile:** <n> fields checked, <n> repaired | **Tasks:** <n> active, <n> stale

### Repaired
- <what was wrong> -> <what it is now> (verified by `<command>`)

### Needs a decision
- <thing> — <the options, and what you recommend>

### Findings about the codebase (not Vince)
- <e.g. new queries no longer carry the isolation key>

### Healthy
- <the checks that passed, one line each>
```

Anything you repaired must name the command that proved the repair. Anything you could not
repair goes under *Needs a decision* with real options — never silently dropped.
