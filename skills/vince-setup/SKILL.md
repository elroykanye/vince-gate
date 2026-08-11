---
name: vince-setup
description: Bootstrap or refresh a project's Vince profile - inspects the repo to discover its test commands, integration branch, tracker, versioning rule, locales, data isolation key, wire-proof rigs and known traps, verifies each discovered command actually runs, and writes .vince/profile.md. Run once per project before vince-implement, and again whenever the build or conventions change. Triggers on "set up vince", "vince profile", "onboard this repo", "no profile found".
---

# Vince — Setup

`vince-implement` and `vince-review` are deliberately project-agnostic. Everything specific to
a codebase lives in one file: **`.vince/profile.md`** at the project root. This skill writes it.

A profile is only useful if it is **true**. Every command you record must be one you actually
ran and watched succeed in this repo. A profile full of plausible-looking commands is worse than
no profile, because the next session will trust it.

## Where the profile goes

`<project root>/.vince/profile.md`, where the project root is the repo you are onboarding. In a
polyrepo workspace, each repo gets its own profile; a workspace-level profile at the workspace
root supplies defaults for repos that have none.

Add `.vince/tasks/` to the repo's `.gitignore` unless the user wants ledgers committed. The
profile itself is usually worth committing — it is project knowledge, not scratch.

## Discovery pass

Work through these, running things rather than assuming. Anything you cannot determine is
recorded as `unknown` with a note — never as a guess.

1. **Stack and layout.** Manifests (`package.json`, `*.csproj`, `pyproject.toml`, `go.mod`,
   `Cargo.toml`, `pom.xml`, `build.gradle`), the directory layout, whether it is one service or
   several, and where tests live.
2. **Commands, each one verified by running it.** Install/restore, build, unit suite, integration
   suite, E2E suite, lint, format check, type check. Record the exact invocation and, for the
   suite, the baseline counts you observed (`N passed / M failed / K skipped`). If a command
   fails on a clean checkout, that is a finding to report to the user, not something to paper
   over — record it as `broken: <output>`.
3. **Branch model.** The integration branch work merges into (`main`, `master`, `dev`,
   `develop`), the branch naming convention, and whether PRs go to a forge (GitHub, GitLab,
   Bitbucket) or elsewhere. `git remote -v` and `git branch -r` tell you most of it.
4. **Tracker and commit convention.** Is there a ticket key pattern in
   `git log --format='%s' -50`? Conventional commits? Nothing at all? Record what the history
   actually does, not what a CONTRIBUTING file wishes it did — and note the difference if they
   disagree.
5. **Versioning.** Does a version live in a manifest, and does CI require it bumped per change?
   Check recent merge commits for a bumped version file.
6. **Data isolation key.** Is this multi-tenant or multi-account? Find the field every query
   filters on (`tenantId`, `orgId`, `workspaceId`, `userId`) — or record `none (single-tenant)`.
   This is what the reviewer's A4 attacks; getting it wrong makes the review weaker.
7. **Auth model.** How entry points are protected (attribute, middleware, decorator, guard),
   and where permission or role keys are defined and provisioned.
8. **Locales.** Which locales ship, where the files live, and the command that checks key parity
   across them. If there is no such command, say so — the gate then falls back to a diff of key
   sets.
9. **Wire-proof rigs.** For each change type in `vince-implement`'s Phase 4 table that this
   project has, the concrete rig that already exists: how to hit the API locally, how to publish
   and observe a message, how to drive the UI, how to run a migration against a copy. This
   section is the highest-value part of the profile — it is what stops the next session from
   inventing a harness.
10. **Environments.** What exists (local, dev, staging, prod), how to read from them, and which
    are shared (i.e. read-only under the live-infrastructure rule).
11. **Memory targets.** Where durable project knowledge lives: `docs/decisions/`, `CLAUDE.md`,
    Serena memories, a brain vault, ADRs, prior task dirs.
12. **Known traps.** Ask the user, and mine the repo: recurring review comments, `HACK`/`FIXME`
    clusters, past incidents, gotchas in `CLAUDE.md`. These become the reviewer's A5 sweep.

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

## Verify before you finish

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
