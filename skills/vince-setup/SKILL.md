---
name: vince-setup
description: Create or refresh a verified Vince project/workspace profile containing real commands, branch and version rules, security boundaries, wire rigs, traps, and exact model mappings. Use for Vince onboarding, missing profiles, or repository convention drift.
---

# Vince — Setup

End user-facing updates with three short lines: `Result:`, `Problem:` (omit when none), and `Next:`. Keep detailed evidence in task artifacts, not chat.

`vince-implement` and `vince-review` are deliberately project-agnostic. Everything specific to
a codebase lives in one file: **`.vince/profile.md`** at the project root. This skill writes it.

A profile is only useful if it is **true**. Every command you record must be one you actually
ran and watched succeed in this repo. A profile full of plausible-looking commands is worse than
no profile, because the next session will trust it.


## Communication and efficiency

Profiles are plain facts. Load `reference/voice.md` only for the user-facing findings report. Load
`reference/token-discipline.md` only for a large workspace inventory; group by stack, bound output,
and write only verified differences.

## Which mode are you in?

Decide this first, because it changes what you are allowed to claim.

| You are onboarding | Mode | Writes | Template |
|--------------------|------|--------|----------|
| A single repo | **repo** | the resolved repo profile | `profile.template.md` |
| A hub with many repos under it | **workspace** | `<workspace>/.vince/profile.md` | `workspace-profile.template.md` |
| A repo inside a hub that already has a profile | **repo (inheriting)** | the resolved repo profile, verified values only | `profile.template.md` |

**Resolve the repo path first — never assume `.vince/` is in the repo:**

```bash
python <toolkit>/scripts/install.py where --repo <repo>
```

By default per-repo config lives in a store outside the repo (`~/.vince/repos/<key>/`), keyed by
the origin remote. Work repos stay clean: nothing untracked, nothing to gitignore, nothing to
commit by accident. A repo that already has its own `.vince/profile.md` keeps using it — that is
the opt-in for repos you own and want the config committed for a team.

Signs you are in a hub: repos live in a sibling directory (`../repos/`, `packages/`, `services/`),
there is a repo manifest, or the user says so. If both a hub and a repo need doing, do the hub
first — the repo profile is then only what differs.

**The invariant for workspace mode: a hub profile cannot verify a command.** You are not going to
run a hundred suites from the hub, and a value nobody ran is not evidence. So in workspace mode
every command you record is `(inferred, unverified)` by construction, and you say so in the file.
Verified commands and observed baselines live in repo profiles, written on first touch. Do not
run one repo's suite and generalise it to a stack — that is one data point wearing a uniform.

In **store mode** there is nothing to gitignore, because nothing lands in the repo. Only when the
user has deliberately chosen in-repo config does `.vince/tasks/` need ignoring, and the profile
itself is then worth committing — it is project knowledge, not scratch.

## Discovery pass — workspace mode

Skip to the next section for a single repo.

1. **Map the estate.** Where the repos live, how many, and how to find the owning repo for a
   piece of work (a manifest file, a naming convention, a domain map). This is the section that
   saves the most time later, and it is one you *can* verify.
2. **Identify the stacks**, not the repos. Group by marker — `*.csproj`, `package.json` with
   React, `pyproject.toml`, `go.mod`. For each stack record the *default* commands, read out of
   manifests and CI config. Mark the block `inferred, unverified` and mean it.
3. **Estate-wide facts you genuinely can verify**: integration branch, branch naming, PR host,
   commit convention (`git log` across a few repos), tracker, isolation key, environments,
   memory targets. These are legitimately `verified`.
4. **Dependency order** between repo classes: shared lib → service → consumer → frontend.
5. **`task_root`**: usually the workspace, because work spans repos.
6. **Estate-wide gates and traps** — the additive sections. Ask the user what breaks repeatedly;
   it is usually known and unwritten.
7. **Sections you cannot start** — wire-proof rigs and mutation tooling are the usual two, since
   they need infra, credentials or a running environment. Mark them
   `blocked — <what is needed>`, not blank. A blank section reads as "nobody thought about it";
   `blocked — needs cluster credentials for the dev namespace` reads as a gap with an unblock.

Then stop. Do not attempt per-repo verification from the hub; that is first-touch work, and
claiming it here is exactly the failure this mode is designed to avoid.

## Discovery pass — repo mode

Work through these, running things rather than assuming. Anything you cannot determine is
recorded as `unknown` with a note — never as a guess.

**Inheriting from a hub?** Read the hub profile first, then record **only what differs or what
you verified**. A repo profile that copies the hub file wholesale creates two places to update
and guarantees drift. Run the inherited commands, write down the ones that worked and the
baseline you observed, and leave everything else to inheritance.

1. **Stack and layout.** Manifests (`package.json`, `*.csproj`, `pyproject.toml`, `go.mod`,
   `Cargo.toml`, `pom.xml`, `build.gradle`), the directory layout, whether it is one service or
   several, and where tests live.
2. **Commands, each one verified by running it.** Install/restore, build, unit suite, integration
   suite, E2E suite, lint, format check, type check. Record the exact invocation and, for the
   suite, the baseline counts you observed (`N passed / M failed / K skipped`). If a command
   fails on a clean checkout, that is a finding to report to the user, not something to paper
   over — record it as `broken: <output>`.
3. **Mutation testing.** Does the stack have a tool (StrykerJS/.NET, mutmut, PIT, go-mutesting,
   cargo-mutants), and is it already configured here? Record the **diff-scoped** invocation, not
   the full-suite one - per-task runs are only affordable incrementally. If nothing is
   configured, say whether one exists for the stack and what it would take, then record `none`;
   both skills fall back to hand mutation. Do not install one uninvited.
4. **Branch model.** The integration branch work merges into (`main`, `master`, `dev`,
   `develop`), the branch naming convention, and whether PRs go to a forge (GitHub, GitLab,
   Bitbucket) or elsewhere. `git remote -v` and `git branch -r` tell you most of it.
5. **Tracker and commit convention.** Is there a ticket key pattern in
   `git log --format='%s' -50`? Conventional commits? Nothing at all? Record what the history
   actually does, not what a CONTRIBUTING file wishes it did — and note the difference if they
   disagree.
6. **Versioning.** Does a version live in a manifest, and does CI require it bumped per change?
   Check recent merge commits for a bumped version file.
7. **Data isolation key.** Is this multi-tenant or multi-account? Find the field every query
   filters on (`tenantId`, `orgId`, `workspaceId`, `userId`) — or record `none (single-tenant)`.
   This is what the reviewer's A4 attacks; getting it wrong makes the review weaker.
8. **Auth model.** How entry points are protected (attribute, middleware, decorator, guard),
   and where permission or role keys are defined and provisioned.
9. **Locales.** Which locales ship, where the files live, and the command that checks key parity
   across them. If there is no such command, say so — the gate then falls back to a diff of key
   sets.
10. **Wire-proof rigs.** For each change type in `vince-implement`'s Phase 4 table that this
   project has, the concrete rig that already exists: how to hit the API locally, how to publish
   and observe a message, how to drive the UI, how to run a migration against a copy. This
   section is the highest-value part of the profile — it is what stops the next session from
   inventing a harness.
11. **Environments.** What exists (local, dev, staging, prod), how to read from them, and which
    are shared (i.e. read-only under the live-infrastructure rule).
12. **Memory targets.** Where durable project knowledge lives: `docs/decisions/`, `CLAUDE.md`,
    Serena memories, a brain vault, ADRs, prior task dirs.
13. **Known traps.** Ask the user, and mine the repo: recurring review comments, `HACK`/`FIXME`
    clusters, past incidents, gotchas in `CLAUDE.md`. These become the reviewer's A5 sweep.
14. **Model routing.** For every harness the team uses, discover the exact available model IDs
    and exact agent types for `economy`, `balanced`, `frontier`, and `reviewer`. Prefer the
    harness's own model-list or configuration command and run it. Record that command beside the
    mapping. If the runtime cannot prove availability, mark the row `(inferred, unverified)` or
    `unknown — <what you tried>` and ask the user; never invent an exact model name from memory.
    When a harness offers a specialized low-latency coding model plus a full reasoning model,
    verify that pair explicitly and map it as the `economy` fast lane and `frontier` handoff.
    Record preview eligibility, context/modality constraints, and rate limits when discovery
    exposes them; availability for one account is not universal availability.

## Write the profile

Copy `templates/profile.template.md` from the Vince toolkit (its path is recorded as `source` in
`.claude/.vince-install.json`), fill it in, and drop every section that does not apply to this
project. If the template is not reachable, write the sections listed above from scratch. Keep it short and factual — commands and paths, not prose. Mark
each field's confidence where it is not certain:

- a verified command: record it plainly
- something you inferred but did not run: `(inferred, unverified)`
- something you could not determine: `unknown — <what you tried>`

## Seed the loop

Two more files, both small, both in `.vince/`:

1. **`.vince/lessons.md`** — create it (empty with a header is fine). If the project has any
   history to mine, run `vince-learn`'s adoption pass instead of leaving it blank: recurring PR
   review comments, `HACK`/`FIXME` clusters, revert chains in `git log`, and the user's own
   answer to "what breaks here that shouldn't?" are worth five real entries on day one.
2. **`.vince/metrics.jsonl`** — leave it absent; `vince-implement` creates it on the first
   completed task. Just make sure `.vince/tasks/` is gitignored unless the user wants ledgers
   committed.

## Which harness is this project using?

Check what is already installed so the profile can say how Vince is invoked here:

```bash
python <toolkit>/scripts/install.py status --target .
python <toolkit>/scripts/install.py bindings
```

If Vince is installed at user scope, project files will show nothing — that is fine, note it.
If the project has harness directories the current install does not cover (`.cursor/`,
`.windsurf/`, `.codex/`, an `AGENTS.md` other people rely on), say so: a teammate on a different
harness gets no gate at all unless that binding is installed too.

Populate **Model routing** only for harnesses actually used by the project. Exact model IDs and
agent types are provider-specific: a Codex mapping does not validate Claude Code, Gemini, Cursor,
Windsurf, or a generic harness. Run each harness's supported discovery command where available;
otherwise keep that row explicitly unverified and ask the user for the intended exact mapping.
Stamp verified rows with the verification date (`verified YYYY-MM-DD — <command>`). After writing
each row, execute `scripts/route.py` once per configured class/role with every discovered identifier
passed as `--available-model` / `--available-agent`. Exit 2 means setup leaves the row unverified and
asks the user; it does not publish a mapping that the resolver cannot reproduce.

## Verify before you finish

In **workspace mode**, verification is about the estate, not the suites: confirm the repo map
resolves (pick three repos at random and find them), confirm the integration branch exists in a
couple of repos, and confirm every path you recorded exists. Do **not** claim a verified suite.

In **repo mode**:

1. Re-run the recorded unit-suite command from a clean state and confirm the baseline counts
   match what you wrote.
2. Confirm the integration branch name resolves: `git rev-parse --verify origin/<integration>`.
3. Confirm any file path in the profile exists.
4. Confirm at least one wire-proof rig actually starts — the section is worthless if it is
   aspirational.
5. Report to the user: what you discovered, what you could not, and anything that looked broken
   on a clean checkout.

## Refresh

Re-run this skill when the build, branch model or conventions change, when a suite command
starts failing on a clean checkout, or when `vince-doctor` reports more than one wrong field.
Update the profile in place and note the date at the top. An out-of-date profile silently
degrades every task that reads it — and unlike a missing one, it does so invisibly.
