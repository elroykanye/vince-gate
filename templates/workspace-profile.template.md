# Vince workspace profile — <workspace name>

Written by `vince-setup` on <YYYY-MM-DD>. This is a **hub profile**: it covers what is true
across the estate, and supplies *defaults* to repos that have no profile of their own.

**The invariant that shapes this whole file: a hub profile cannot verify a command.** Nobody
runs 100 suites from the hub, and a value nobody ran is not evidence. So every command here is
`(inferred, unverified)` by construction. Verified commands and observed baselines live in
`<repo>/.vince/profile.md`, written on the first task that touches that repo. Anything in this
file that claims to be verified is a bug in this file.

## Section status

Every section carries one of these. An honest gap outranks a plausible guess, because the next
session trusts whatever is here.

| Marker | Means |
|--------|-------|
| `verified` | someone ran it and watched it work — only legitimate for hub-level things (branch model, tracker, repo map) |
| `inferred, unverified` | derived from the code/CI without running it. The default state of every per-stack command here |
| `unknown — <what was tried>` | could not determine |
| `blocked — <what is needed>` | cannot be determined without access/infra/credentials somebody else holds. Says what would unblock it |

## Workspace

- Root: `<path>`
- Repos live in: `<path, e.g. ../repos/>`
- Repo count: `<n>`
- Repo map: `<manifest file, naming convention, or how to find the owning repo>`
- Status: `verified`

## Stacks

One block per stack in the estate. A repo is matched to a stack by the marker below, and
inherits that stack's commands until its own profile supersedes them.

### Stack: `<name, e.g. dotnet-api>`

- Matches: `<marker — e.g. *.csproj present, package.json with react, pyproject.toml>`
- Repos: `<count or list>`
- Status: `inferred, unverified` — these are defaults, verified per repo on first touch

| Purpose | Command | |
|---------|---------|---|
| Install / restore | `` | |
| Build | `` | |
| Unit suite | `` | baseline observed per repo, not here |
| Integration suite | `` | |
| Lint / format / types | `` | |
| Mutation testing | `` | tool + diff-scoped invocation |
| Run locally | `` | |

### Stack: `<name>`

<repeat>

## Delivery (applies to every repo unless a repo profile says otherwise)

- Integration branch: `<main | dev | ...>`
- Branch naming: `<pattern>`
- PR host: `<GitHub | GitLab | Bitbucket>`
- Commit convention: `<ticket prefix pattern | conventional commits | none>`
- AI attribution trailers: **not allowed** (default) | allowed
- Versioning rule: `<per-repo file + rule>`
- `reviewer_model`: `<model, or blank>`
- Status: `verified`

## Tracker

- System / key pattern / how to read a ticket: ``
- Status: `verified`

## Task ledgers

In a hub, work often spans repos, so ledgers usually live at the workspace, not in each repo.

- `task_root`: `<workspace>/.vince/tasks/` (`active/<task-id>/`, `archive/<task-id>/`)
- Multi-repo tasks: record every repo, its branch, and the **dependency order** on the ledger
  header (shared lib → service → consumer → frontend).
- Status: `verified`

## Data and security

- Isolation key: `<tenantId | orgId | none>` — and whether it holds estate-wide
- Where enforced / auth model / permission keys: ``
- Status: `<verified | inferred, unverified>`

## Environments

| Environment | How to reach it | Shared? (read-only) |
|-------------|-----------------|---------------------|
| | | |

Status: `<...>`

## Wire-proof rigs (estate-wide)

Rigs that work across repos. Per-repo rigs belong in the repo profile.

| Change type | Rig |
|-------------|-----|
| | |

Status: `<verified | blocked — e.g. needs cluster credentials / VPN>`

## Mutation testing

Per-stack tools are listed with their stack above. Anything estate-wide (a shared config, a CI
job) goes here.

Status: `<verified | inferred, unverified | blocked — ... | unknown — ...>`

## Memory targets

- Decisions / runbooks / conventions: ``
- Per-repo: each repo's own `CLAUDE.md`/`AGENTS.md` and prior task dirs
- Status: `verified`

## Extra definition-of-done gates (`dod_extras`)

**Additive.** These apply to every repo; a repo profile can add to them but cannot remove them.

| Gate | Verify | PASS condition |
|------|--------|----------------|
| | | |

## Known traps

**Additive**, same rule. Traps that have bitten across the estate.

- 

## Corrections

Repairs made to this file while tasks were running. Newest first: what was wrong, what it is
now, what proved it.

- 
