# Vince profile — <project name>

Written by `vince-setup` on <YYYY-MM-DD>. Every command below was run in this repo and observed
to work, unless marked otherwise.

**Repo:** `<repo path>`  ·  **Key:** `<from install.py where>`  ·  **Stored:** `<store | in-repo>`
**Inherits from:** `<path to workspace profile, or "none — standalone repo">`

When inheriting, record **only what you verified or what differs**. Do not copy the hub file:
two copies of one fact is two places to drift. Scalars here override the hub; its `dod_extras`
and `known_traps` are additive and cannot be removed from here.

Mark each field:

| Marker | Means |
|--------|-------|
| (unmarked) | verified — you ran it and watched it work |
| `(inferred, unverified)` | derived without running it, or inherited and not yet run |
| `unknown — <what was tried>` | could not determine |
| `blocked — <what is needed>` | needs access, infra or credentials someone else holds |

`blocked` is the one people skip and the most useful. Wire-proof rigs and mutation tooling are
the two most often legitimately blocked at setup time — say `blocked — needs dev cluster
credentials` rather than leaving the section blank or inventing something plausible.

## Project

- Root: `<abs or repo-relative path>`
- Stack: `<languages, frameworks, runtimes>`
- Shape: `<single service | monorepo | one repo of a polyrepo>`
- Sibling repos (polyrepo only): `<where they live, dependency order>`

## Commands

| Purpose | Command | Notes |
|---------|---------|-------|
| Install / restore | `` | |
| Build | `` | |
| Unit suite | `` | baseline: `N passed / M failed / K skipped` on `<commit>` |
| Integration suite | `` | |
| E2E suite | `` | |
| Lint | `` | |
| Format check | `` | |
| Type check | `` | |
| Locale parity | `` | |
| Run locally | `` | |
| Mutation testing | `` | tool + diff-scoped invocation; see below |

## Mutation testing

The tool that measures whether the tests would notice a bug, and how to run it **scoped to the
diff** (per-task mutation runs are only affordable incrementally). Surviving mutants on changed
lines are missing assertions, not a score to admire.

- Tool: `<Stryker | mutmut | PIT | go-mutesting | cargo-mutants | none for this stack>`
- Diff-scoped command: ``
- Full-suite command (slow, occasional): ``
- Baseline score on the integration branch: `<%>` on `<date>`
- Notes: `<what it cannot cover, known-equivalent mutants>`

No tool for the stack is a valid answer - record `none`, and both skills fall back to
mutating by hand.

## Branch and delivery

- Integration branch: `<main | dev | ...>`
- Branch naming: `<pattern>`
- PR target and host: `<GitHub | GitLab | Bitbucket | none>`
- Commit convention: `<ticket prefix pattern | conventional commits | none>`
- AI attribution trailers: **not allowed** (default) | allowed
- `reviewer_model`: `<model to run vince-review with, ideally a different vendor from the
- `checkpoints`: `off` (default) | `suggest` (offer /compact at safe checkpoints) | `insist`
- `reviewer_agent_type`: `<narrowest agent type with Write/Edit, or blank>`
- `mechanical_model`: `<cheaper model for search/mechanical subagents, or blank>`
- `voice`: `playful` (default) | `plain` (same honesty, no jokes) | `terse` (facts only)
  implementer; blank = same model, fresh context>`
- Versioning: `<file + rule, or "not required">`

## Tracker

- System: `<GitHub Issues | Jira | Linear | none>`
- Key pattern: `<e.g. ABC-1234, or n/a>`
- How to read a ticket: `<MCP tool, CLI command, or URL pattern>`

## Task ledgers

- `task_root`: `.vince/tasks/` (`active/<task-id>/`, `archive/<task-id>/`)
- Committed to git: `no` (default) | `yes`

## Data and security

- Isolation key: `<tenantId | orgId | userId | none (single-tenant)>`
- Where it is enforced: `<repository layer, middleware, RLS, ...>`
- Auth model: `<how entry points are protected>`
- Permission/role keys defined in: `<path>`
- Datastores: `<engine + what owns what>`

## Frontend

- Locales shipped: `<list>` — files at `<path>`
- Breakpoints: `<list>`
- Component/E2E test runner: `<runner>`
- Running app URL for live review: `<url>` — credentials in `<location, never echoed>`

## Wire-proof rigs

The concrete way to prove each change type end to end in this project. One row per change type
that exists here; delete the rest.

| Change type | Rig |
|-------------|-----|
| HTTP API | |
| Async / queue | |
| Background job | |
| CLI | |
| Library / package | |
| Frontend | |
| Data migration | |
| Infra / config | |

## Environments

| Environment | How to reach it | Shared? (read-only) |
|-------------|-----------------|---------------------|
| local | | no |
| dev | | yes |
| prod | | yes |

## Memory targets

Where durable project knowledge lives — read before designing, write after deciding.

- Decisions: `<path>`
- Runbooks / recipes: `<path>`
- Conventions: `<path>`
- Prior task dirs: `<task_root>/archive/`

## Extra definition-of-done gates (`dod_extras`)

Project-specific gates that `vince-implement` Phase 5 must walk in addition to the catalog.

| Gate | Verify | PASS condition |
|------|--------|----------------|
| | | |

## Known traps

Things that have bitten in this codebase before. The reviewer sweeps these in A5, and
`vince-learn` adds a line here whenever a finding class appears for the second time.

- 

## Corrections

Repairs made to this profile while a task was running (`vince-implement` self-healing,
`vince-doctor`). Newest first. Each line: what was wrong, what it is now, what proved it.

- 

## Docs destination

- `docs_destination`: `<wiki space + skill/script that files it | docs-site path | PR body | none>`

## Tiering overrides

Optional. Narrows or widens `vince-implement`'s T1/T2/T3 rules for this project - e.g. "anything
under `migrations/` is always T3", or "translation-only edits are T1". Defaults apply to anything
not listed.

- 
