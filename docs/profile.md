# The project profile

`.vince/profile.md` at a project root is the only per-project configuration Vince has. The four
skills are written to be project-agnostic; the profile is where a project's reality goes.

Written by `vince-setup`, repaired by `vince-implement`'s self-healing step and `vince-doctor`,
extended by `vince-learn`. Read by `vince-implement` (Phase 0, before anything else),
`vince-review` (as inputs, and for its trap sweep) and `vince-document` (for memory targets and
the publishing destination).

It has two companions in the same directory: `.vince/lessons.md` (what reviews have caught here,
read before designing) and `.vince/metrics.jsonl` (one line per completed task). Both are written
by `vince-learn`.

Start from [`templates/profile.template.md`](../templates/profile.template.md), or
[`templates/workspace-profile.template.md`](../templates/workspace-profile.template.md) for a
hub.

## Where config lives

**Per-repo config is kept outside the repo by default.** Vince describes your work repos; it does
not need to live in them, and putting it there means an untracked directory in every repo, a
gitignore line you may not control, and something to commit by accident.

```
~/.vince/                                   the store (override with $VINCE_STORE)
  repos/
    github.com__acme__billing-api/
      profile.md      lessons.md      metrics.jsonl      tasks/
    bitbucket.org__acme__web/
      ...
```

The key is derived from the repo's **origin remote**, which makes it stable across re-cloning and
moving the checkout, readable enough to find and hand-edit, and — usefully — shared by task
worktrees, so a `-wt` worktree resolves to its parent repo's config rather than a fresh empty one.
Repos with no remote fall back to `local__<name>__<short path hash>`.

**Never derive these paths yourself.** Ask:

```bash
python <toolkit>/scripts/install.py where --repo <repo>      # add --json for machine output
```

It prints the key, the mode, and the resolved profile / lessons / metrics / task root. One
deterministic answer means every session agrees; hand-derived paths are how one repo ends up with
config in two places.

### Opting a repo *into* carrying its own config

If `<repo>/.vince/profile.md` exists, it wins and everything for that repo stays in the repo.
That is the right choice when you own the repo and want the profile committed so a team shares
it — an open-source project, your own service. It is the wrong default for a work repo you do not
control, which is why it is opt-in.

To switch a repo to in-repo config, move its store directory into `<repo>/.vince/` and add
`.vince/tasks/` to that repo's `.gitignore`. To switch back, move it out.

## Resolution order

1. `<repo>/.vince/profile.md` — only if that repo has opted in.
2. `<store>/repos/<key>/profile.md` — the default location for per-repo config.
3. `<workspace>/.vince/profile.md` — the **hub profile**, when repos live under a workspace.
4. None of them → run `vince-setup` first. Skills must not guess at a test command or a branch
   model; a wrong guess produces a confident, wrong baseline.

In store mode there is nothing to gitignore, because nothing lands in the repo. In in-repo mode
the profile is usually worth committing — it is project knowledge — while `.vince/tasks/` usually
is not.

## Two levels: hub and repo

A workspace with many repos cannot have one profile, and it cannot have only per-repo profiles
either — the branch model, tracker, isolation key and estate-wide traps are the same everywhere,
and re-deriving them per repo is both wasteful and a source of drift.

So there are two files, with one invariant between them:

> **A hub profile cannot verify a command.** Nobody runs a hundred suites from the hub, and a
> value nobody ran is not evidence. Every command in a hub profile is `(inferred, unverified)`
> by construction. Verified commands and observed baselines exist **only** in a repo profile.

That is not a caveat, it is the design. It means a hub profile is honest about being a set of
defaults, and it means the first task in a repo has a defined job: verify what it inherited.

Note that "repo profile" means *the profile describing that repo*, wherever it is stored — by
default in the store, not in the repo.

| Lives in the **hub** profile | Lives in the **repo** profile |
|------------------------------|-------------------------------|
| Repo map, stack definitions, repo count | Verified commands, actually run |
| Per-stack *default* commands (unverified) | Observed suite baseline + the commit it was taken on |
| Integration branch, branch naming, PR host | Repo-specific overrides of any hub default |
| Commit convention, versioning rule, `reviewer_model` | This repo's mutation tool and its diff-scoped command |
| Tracker and how to read a ticket | This repo's wire-proof rigs |
| Isolation key and auth model | This repo's locales |
| Environments, memory targets | Repo-specific traps and gates |
| `task_root` (usually the workspace, since work spans repos) | |

### Merge semantics

Precise, because "the repo one wins" is only half true:

- **Scalars override.** A field present in the repo profile replaces the hub value entirely —
  branch, versioning rule, isolation key, `reviewer_model`, commands.
- **`dod_extras` and `known_traps` are additive, and the hub's are not removable.** A repo adds
  gates and traps; it cannot drop one the estate imposes. Dropping an estate-wide gate is a
  decision for whoever owns the hub profile, recorded there with a reason.
- **Confidence does not survive inheritance.** A value taken from the hub arrives
  `(inferred, unverified)` regardless of how confident it looks. It becomes verified only by
  being run in that repo and written into the repo profile.
- **Lessons stack.** `<workspace>/.vince/lessons.md` and `<repo>/.vince/lessons.md` are both
  read. `vince-learn` routes each new lesson by scope: true of the platform → hub; true of one
  repo → repo.

### First touch: the promotion step

The first task in a repo whose values are inherited has an extra job, and it is small:

1. Run the inherited commands. Watch them work.
2. Record the observed suite baseline (`N passed / M failed / K skipped`) and the commit.
3. Write `<repo>/.vince/profile.md` with the verified values — only what you verified, not a
   copy of the hub file.
4. Anything that fails, re-derive once and record under *Corrections*; anything you cannot
   determine stays `unknown` or `blocked`, never a guess.

After that the repo is self-describing and the hub is back to being defaults. This is the
mechanism that makes a hub profile safe: the unverified values have a defined moment where they
stop being unverified, rather than being trusted forever.

### Section status vocabulary

Both files mark each section. `blocked` is the one people skip, and it is the most useful:

| Marker | Means |
|--------|-------|
| `verified` | someone ran it and watched it work |
| `inferred, unverified` | derived from code or CI without running it |
| `unknown — <what was tried>` | could not determine |
| `blocked — <what is needed>` | needs access, infra or credentials somebody else holds |

A blank section reads as "nobody thought about it". `blocked — needs cluster credentials for the
dev namespace` reads as a known gap with an owner and an unblock. Wire-proof rigs and mutation
tooling are the two that are most often legitimately blocked at setup time — say so rather than
leaving them empty or inventing something plausible.

## Fields

### Project

Root path, stack, whether it is a single service or one repo of a polyrepo, and where sibling
repos live with their dependency order (shared lib → service → consumer → frontend). The
dependency order is what `vince-implement` Phase 1 writes down for a multi-repo task.

### Commands

Install, build, unit suite, integration suite, E2E suite, lint, format check, type check, locale
parity, run locally. **Every one must have been run and observed to work.** The unit suite row
also records the baseline counts (`N passed / M failed / K skipped`) and the commit they were
observed on — Phase 1 compares against it, and the reviewer checks the suite is no worse.

A command that fails on a clean checkout is recorded as `broken: <output>` and reported, not
quietly omitted.

### Mutation testing

The tool that measures whether the tests would notice a bug, and the **diff-scoped** invocation
— per-task mutation runs are only affordable incrementally, and every major tool supports it
(`stryker --incremental`, `dotnet stryker --since`, `mutmut --paths-to-mutate`,
`pitest -DwithHistory`, `cargo mutants --in-diff`).

Read by `vince-implement`'s TAMPER step and the reviewer's A2. Both treat **surviving mutants on
changed lines as missing assertions**, not as a score: the implementer kills them or waives them
with a reason, and the reviewer re-runs the tool rather than trusting the tamper evidence.
`none` is a valid answer for stacks with no tool — both fall back to mutating by hand.

### Branch and delivery

Integration branch (`main`, `dev`, …), branch naming, PR host, commit convention, whether AI
attribution trailers are allowed (default: **not allowed**), and the versioning rule. The
version rule matters more than it looks: the bump must be exactly one increment above the
integration branch's *current* value, so the profile records which file holds it.

### `reviewer_model`

Which model should run `vince-review`. A fresh context breaks the correlation introduced while
generating; it does not break the correlation baked into a model's parameters, so a different
model — ideally a different vendor — is measurably stronger isolation than a fresh context alone.
Blank means "same model, fresh context", which is still far better than same-context review, and
the verdict records which model actually ran.

### `voice`

`playful` (default), `plain` or `terse`. Vince is dry and a bit sarcastic by default, and it
explains its own jargon rather than assuming you speak it. The humour is aimed at the situation,
the tooling and itself — never at you — and it switches off entirely for security findings,
destructive operations, and any time it got something wrong.

Set `plain` for the same honesty without jokes, or `terse` for facts only. Shared repos with
mixed audiences usually want `plain`. Whatever the setting, **artifacts** — ledgers, verdicts,
commit messages, completion docs — are always written plainly, because they outlive the
conversation.

### Tracker

System, key pattern, and how to read a ticket (MCP tool, CLI, URL). Drives Phase 0's contract
source and the reviewer's A0 re-derivation. `none` is a valid answer — then the contract is the
user's own words, restated and confirmed.

### Task ledgers

`task_root` (default `.vince/tasks/`) and whether it is committed. Task dirs live at
`<task_root>/active/<task-id>/` and move to `archive/` when closed.

### Data and security

The **isolation key** is the field every query must filter on in a multi-tenant or multi-account
system (`tenantId`, `orgId`, `workspaceId`, `userId`) — or `none (single-tenant)`. The reviewer's
A4 attacks it directly and treats a missing filter as CRITICAL on sight, so a wrong value here
makes reviews weaker in the one place that leaks data.

Also: how entry points are protected, where permission/role keys are defined and provisioned,
and which component owns which datastore.

### Frontend

Locales shipped and where they live, breakpoints, test runner, and the running app URL plus
where credentials live (never echoed). The reviewer needs the URL to drive the app in a real
browser — without it, frontend criteria stay UNPROVEN.

### Wire-proof rigs

The highest-value section. For each change type in `vince-implement`'s Phase 4 table that this
project has, the concrete rig that already exists: how to hit the API locally, how to publish and
observe a message, how to drive the UI, how to run a migration against a copy. Its purpose is to
stop the next session from inventing a harness that already exists.

### Environments

What exists, how to reach it, and which are **shared** — shared means read-only under the
live-infrastructure rule, no exceptions for small careful writes.

### Memory targets

Where durable project knowledge lives: decisions, runbooks, conventions, prior task dirs. Read
before designing (Phase 0.3) and re-checked by the reviewer's A0 — an implementation that
contradicts a recorded decision is a finding even when the tests are green.

### `dod_extras`

Project-specific definition-of-done gates, in the same `Gate | Verify | PASS condition` shape as
[`dod-gates.md`](../skills/vince-implement/reference/dod-gates.md). Phase 5 walks the catalog and
these together, and they are equally mandatory.

### Known traps

Things that have bitten in this codebase before — recurring review comments, past incidents,
gotchas. The reviewer sweeps these in A5, and project-specific traps are worth more than the
generic list. `vince-learn` adds a line here whenever a finding class appears for the second
time; a one-off is deliberately not promoted.

### Corrections

Repairs made to this profile while a task was running, newest first: what was wrong, what it is
now, and what proved it. Written by `vince-implement`'s self-healing step and by `vince-doctor`.
A profile with a long corrections list is a profile due a full `vince-setup` refresh.

### Tiering overrides

Optional. Narrows or widens `vince-implement`'s T1/T2/T3 classification for this project — e.g.
"anything under `migrations/` is always T3", or "translation-only edits are T1". Defaults apply
to anything not listed. Use this rather than letting the agent stretch the generic rules.

### `docs_destination`

Where completion documentation gets published, and by what (a dedicated skill or script, a wiki
space, a docs-site path, a PR body, or `none`). `vince-document` follows it rather than inventing
a destination, and publishes only after a PASS.

## Keeping it true

A profile full of plausible-looking commands is worse than no profile, because the next session
will trust it. Mark anything unverified `(inferred, unverified)` and anything undetermined
`unknown — <what you tried>`.

Three mechanisms keep it true, in increasing order of size:

1. **Self-healing, mid-task.** A recorded command that fails is re-derived once, verified, and
   repaired in place with a line under *Corrections*. Two wrong fields in one task is a stop.
2. **`vince-doctor`**, on demand. Validates every field by running it, and repairs or honestly
   marks each one.
3. **`vince-setup`**, a full refresh. Run it when the build, branch model or conventions change,
   or when the doctor finds more than one wrong field.
