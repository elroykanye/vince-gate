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

Start from [`templates/profile.template.md`](../templates/profile.template.md).

## Resolution order

1. `<repo>/.vince/profile.md` — the repo being worked on.
2. `<workspace>/.vince/profile.md` — a workspace-level profile supplying defaults for repos with
   none (useful in a polyrepo workspace where the repos share a stack).
3. No profile → run `vince-setup` first. Skills must not guess at a test command or a branch
   model; a wrong guess produces a confident, wrong baseline.

The profile is usually worth committing — it is project knowledge. `.vince/tasks/` usually is
not; add it to `.gitignore` unless the user wants ledgers in history.

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

### Branch and delivery

Integration branch (`main`, `dev`, …), branch naming, PR host, commit convention, whether AI
attribution trailers are allowed (default: **not allowed**), and the versioning rule. The
version rule matters more than it looks: the bump must be exactly one increment above the
integration branch's *current* value, so the profile records which file holds it.

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
