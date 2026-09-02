# Changelog

Versions are git tags. `VERSION` in the working tree names the release; `install.py status`
prints both that and the actual checkout, so a mid-line or modified clone is visible rather than
silently claiming to be a release.

See [INSTALL.md](INSTALL.md#versions) for upgrading, pinning and rolling back.

## v0.12.0 — 2026-08-31

Vince adopts progressive disclosure across its primary workflows and adds native Agent Skills
bindings for current Gemini CLI and GitHub Copilot layouts.

**Changed**

- Every Vince skill ends user-facing work with concise `Result`, optional `Problem`, and `Next`
  lines; detailed proof remains in task artifacts.
- Review Pass 0 freezes a validated exhaustive coverage manifest, and discovery continues across
  all material claims and A0–A7 attacks even after FAIL is certain.
- `vince-implement` and `vince-review` keep their proof floor in compact primary instructions;
  phase-specific contract, TDD, wire-proof, attack, verdict, and handoff details now load from
  focused references only when needed.
- Shared voice and token-discipline references are conditional instead of mandatory on every skill
  activation, while their essential safety and efficiency rules remain inline.
- Discovery descriptions are distinct and capped by regression tests, and both primary workflows
  stay below a conservative approximate 5,000-token activation budget.

**Harnesses**

- Gemini CLI now renders native skills to `.gemini/skills/` and `~/.gemini/skills/` instead of
  legacy TOML custom commands.
- GitHub Copilot gains native `.github/skills/` and `~/.copilot/skills/` bindings without sharing
  Codex's install directories.
- Both new/changed bindings remain explicitly unverified until live discovery and invocation probes
  pass in their runtimes.

**Verified**

- Token, reference, description, binding, documentation, and disposable-install regression tests
  cover the progressive-disclosure contract.
- Existing routing, intake, Codex compatibility, external security boundary, and Stop-hook tests
  remain in the full suite.

## v0.11.2 — 2026-08-31

Vince adds bounded operational helpers and hardens shipped skill instructions while preserving
its existing gate architecture.

**Added**

- **Health reporting.** The operations CLI reports binding, task, route, and next-action health.
- **Route refresh.** Exact model inventories can refresh routing profiles without guessed IDs.
- **Release checks.** Version, changelog, tag, and disposable-install consistency can be checked
  before publishing.
- **Codex discovery probe and task archiving.** Maintainers can verify live skill discovery and
  archive only tasks whose current verdict is PASS and whose workspace is clean.

**Security**

- Shipped skill examples use project-local executables instead of unpinned package runners.
- Regression coverage prevents external audit tooling from becoming an embedded Vince command,
  installer gate, baseline, or shipped-skill dependency.
- Shipped skill Markdown rejects package-runner tokens across platform suffixes, paths, wrappers,
  prose, and Markdown fence styles.

**Verified**

- The full suite passes with 34 tests and no skips.
- Independent adversarial review passed after mutation-testing CLI boundaries, shipped-skill
  coverage, Windows executable variants, and alternate Markdown representations.

## v0.11.1 — 2026-08-23

Vince now routes implementation work to the least expensive capable model class and the narrowest
useful agent role, while keeping the proof floor intact.

**Added**

- **Model routing gate.** `vince-route` classifies work as `economy`, `balanced`, `frontier`, or
  `reviewer`, then resolves exact harness-specific model identifiers from the project profile.
- **Agent role routing.** Profiles can map exact `explorer`, `worker`, and `reviewer` roles per
  harness, with no provider-name fallback.
- **Switch recommendations.** Vince can recommend an exact model switch with the token/quality
  tradeoff, while making clear that the harness or user performs the actual switch.

**Verified**

- Codex live routing passed a nine-case matrix covering trivial, standard, explorer, complex,
  security, reviewer, switch, ask, and proof-floor behavior.
- Stale, unavailable, unchecked, missing, or unverified mappings return `ASK` instead of silently
  substituting another model.
- Claude, Gemini, Cursor, Windsurf, and generic bindings render the routing skill and profile
  fields, but remain marked as render-verified rather than live-verified.

## v0.11.0 — 2026-08-17

Codex support is now based on live runtime behavior rather than configuration shape alone.

**Fixed**

- **Native reviewer role.** The supplied TOML now uses Codex's required
  `developer_instructions`; the prior description-only role was rejected by the runtime.
- **External verdict persistence.** Reviewer sessions whose Vince task directory is outside the
  repository now document the required parent `--add-dir <resolved task-root>` grant.
- **Stop-hook task lookup.** The hook finds both repository-local and external Vince task stores,
  including repositories without an origin remote.

**Verified**

- Project-scoped Vince skills were installed, discovered and invoked by Codex CLI
  `0.148.0-alpha.9`.
- A persistent Codex parent delegated to the named reviewer role, which ran the installed
  `vince-review` skill and persisted a genuine verdict in an external task directory.
- Project `.codex/hooks.json` did not load, and user-scope Stop blocking was not exercised. The
  binding and documentation state that limitation instead of claiming hard enforcement.

**Upgrade notes**

Copy the updated reviewer template into `.codex/agents/vince-review.toml`. Use a persistent Codex
parent session, and when `install.py where --repo <repo>` resolves outside the repository, launch
Codex with `--add-dir <resolved task-root>`.

## v0.10.0 — 2026-08-14

Two bindings were wrong, found by checking them against current documentation instead of trusting
what they were written from.

**Fixed**

- **Codex.** Was installing to `.codex/vince/` with no frontmatter and an AGENTS.md pointer block.
  Codex has had native skill loading since December 2025: `.agents/skills/` for a project,
  `~/.agents/skills/` or `~/.codex/skills/` for a user, most specific first, with the **same
  `name` + `description` frontmatter Claude Code uses**. The canonical skills now install
  unchanged and auto-activate, and the pointer block is no longer needed.
- **Cursor.** Reference docs were being written as plain `.md` into `.cursor/rules/`, which Cursor
  **ignores** - no frontmatter means it is not a rule, so they sat in the rules directory looking
  registered while doing nothing. Bindings gained a `reference_dir`, so references now install to
  `.cursor/vince/` and links inside each rule are rewritten to `../vince/…`. The rules directory
  contains only real rules. Same fix applied to Windsurf.

**Added**

- **A per-harness capability table** in `docs/harnesses.md`. The compatibility question is not
  whether files install, it is whether the harness can give the reviewer a fresh context. Claude
  Code and Codex can, natively. Cursor, Windsurf and Gemini CLI cannot, so the review is a second
  chat you open and paste the handoff into - the same rigour with one manual step, and arguably
  cleaner isolation, but easier to skip. Stated plainly rather than implied.
- **`templates/codex-reviewer-agent.toml`** - a Codex subagent definition for the review. Codex
  subagents are TOML in `.codex/agents/` and **can pin the model**, which is the one place the
  reviewer's model can actually be chosen rather than merely recommended.

**Upgrade notes**

Anyone with a previous Codex install should uninstall the `codex` binding before reinstalling;
the old `.codex/vince/` location and its AGENTS.md block are no longer written, and `uninstall`
only removes what its manifest recorded.

## v0.9.0 — 2026-08-13

Makes "you can clear context mid-task" a checked claim instead of a hopeful one, and stops the
docs implying Vince can do things it cannot.

**Added**

- **`scripts/resume.py`** - rebuilds a task's state from its ledger alone, reading no
  conversation. Prints what a fresh session needs (phase, next action, open criteria with their
  proof commands, live resources still to tear down) and returns `SAFE TO CLEAR` / `NOT SAFE TO
  CLEAR` with the specific gaps. A ledger missing a Resume block, a proof command on an open
  criterion, or a baseline is not self-sufficient, and it says so rather than letting you find out
  after clearing.
- **Checkpoint protocol.** At every phase boundary: bring the ledger current, update its new
  **Resume** block, run `resume.py --check`. Never suggest clearing without that check passing -
  a reset on an incomplete ledger destroys work, which is worse than the context it saves.
- **Pressure signals** - proxies an agent can actually observe, since it cannot see its own token
  count: ~15 files read or ~5 suite runs since the last checkpoint, a large diff or build log
  captured, the same file read more than twice, entering remediation. Documented as
  approximations.
- **`checkpoints` profile setting**: `off` (default), `suggest`, `insist`. At `suggest`, Vince
  offers a `/compact` at checkpoints that pass the safety check. **It cannot run compaction
  itself** - that is the user's keystroke - and the skills say so explicitly rather than implying
  otherwise.
- **Model honesty.** A skill cannot select its own model. Vince now states which model it is
  running as in the verdict and handoff, passes `reviewer_model`/`mechanical_model` through so
  whoever spawns the subagent can honour them, and recommends the split - strongest model for the
  judgement passes, cheaper for search and mechanical sweeps. It does not claim to have chosen.

**Upgrade notes**

`checkpoints` defaults to `off`, so nothing changes until you set it. Existing ledgers gain a
Resume block the next time a task touches them; `resume.py --check` will flag its absence.

## v0.8.0 — 2026-08-13

Token discipline. Vince was directly implicated in its own users' cost profile: it mandates a
subagent per task, its handoff recommended `general-purpose` by name, and `vince-implement` alone
was ~10k tokens of context on every task. Rigour is not negotiable; what it costs is.

**Added**

- **`scripts/check.py`** - the deterministic half of a review as a script instead of model turns.
  One command reports stray artifacts, AI/bot attribution trailers, over-long commit subjects,
  newly added skipped tests, debug statements in non-test code, possible hardcoded secrets,
  whole-file rewrites (the line-ending-flip shape), a branch behind its base, an uncommitted tree,
  and whether any test files were touched. Replaces roughly ten commands and their raw output.
  Explicitly **input, not verdict** - it proves nothing about behaviour, isolation or blast radius.
- **`skills/_shared/token-discipline.md`** - read narrowly, bound long commands, spend the model
  where judgement is needed, and treat the ledger as memory so context can be reset. Ends with
  what never gets cut to save money.
- Profile settings `reviewer_agent_type` and `mechanical_model`, and `tokens` on the metrics line
  so `vince-learn` can report cost per task against rounds-to-PASS.

**Changed**

- `vince-implement` **10,098 -> ~7,400 tokens**. Remediation, self-healing, commit hygiene and
  workspace hygiene moved to `reference/remediation.md` and `reference/hygiene.md`, which load at
  the step that needs them; the inline ledger example is replaced by a pointer to the template.
  What stayed inline is everything that changes behaviour every task.
- The reviewer handoff no longer names `general-purpose` as the default. Use the narrowest agent
  type with `Write`/`Edit`; `general-purpose` is the fallback, because a broad type carries a
  bigger prompt for capabilities a review never uses.
- `vince-review` A1 now starts with the script and falls back to hand commands.
- `voice.md` trimmed - it is copied into all eight skills, so its examples were paying eight times.

**Upgrade notes**

No required config. `reviewer_agent_type` and `mechanical_model` are optional. `check.py` needs
nothing installed - it is in the toolkit clone.

## v0.7.0 — 2026-08-12

**Added**

- **A voice.** Vince is now dry and a little sarcastic, and it explains its own jargon instead of
  assuming you speak it - the precise term stays, with the plain-English translation beside it,
  including a glossary of the toolkit's own vocabulary (surviving mutant, wire proof, blast
  radius, isolation key, first-touch promotion...).

  Three rules stop the personality costing anything. A joke never carries information - strip
  every one out and the message is still complete. Comedy is in the delivery, never the verdict;
  severity and PASS/FAIL are always flat. And it is never aimed at the user: fair targets are the
  situation, the tooling and itself. It goes completely straight for security findings, anything
  destructive, and any time it was wrong - a joke there reads as dodging, because it usually is.

  **Artifacts stay professional.** Ledgers, verdicts, commit messages and completion docs are
  written plainly whatever the voice setting, because someone reads them later without the
  conversation around them.
- **`voice` profile setting**: `playful` (default), `plain` (same honesty, no jokes), `terse`
  (facts only). Asking in conversation is also a standing instruction.
- **`skills/_shared/`** - reference content copied into every skill at install time. One source of
  truth in the repo, present next to each skill at runtime; a file eight skills each kept a copy
  of would drift within a release. `_shared` has no `SKILL.md` so it is never listed as a skill,
  and flat layouts render it as `<skill>-voice.md` with links rewritten.

**Upgrade notes**

No config fields are required. Add `voice:` to a profile only if you want something other than
the default. Existing installs pick the voice file up on the next `install`.

## v0.6.1 — 2026-08-12

Fixes the discovery gap that 0.6.0 shipped with, found by the incident that prompted the skill:
two `python -m http.server` processes, started a week earlier, holding a `dist/` directory open.
0.6.0's primary sweep filtered `Win32_Process` on `CommandLine` and `ExecutablePath` containing
the directory - and **neither field contains it**. The association is in the working directory and
open handles. The sweep returned nothing and the directory looked unheld.

**Changed**

- `vince-cleanup` now sweeps on **three axes** instead of a path filter: **listening ports** (a
  preview server exists to serve, so it is bound to something), **age + image name** (dev tooling
  up for days is nobody's active work), and **open handles**. Per-candidate resolution then answers
  what the command line cannot - `handle.exe -p`, `lsof -p ... cwd`, `readlink /proc/<pid>/cwd`.
- Added a table of shapes that hide from a path grep: `python -m http.server`, `npx serve`,
  `php -S`, `ruby -run -e httpd`, bare `node` dev servers, `dotnet watch`, `kubectl port-forward`.
- **Post-stop verification**: process gone, port released, directory writable. "Killed it" is not
  "the directory is free" - the incident had two servers on the same port, so killing one changed
  nothing observable.
- "Nothing is holding it" now sends you back through the three-axis sweep before concluding the
  directory is unheld, rather than straight to Explorer windows and antivirus.
- New attack-playbook entry (A5 sweep): a stale server on the wire-proof's port answers instead of
  the build under review, with week-old output. A process older than the branch cannot be serving
  the branch.

**Upgrade notes**

No config changes.

## v0.6.0 — 2026-08-12

**Added**

- **`vince-cleanup`.** Recovers a workspace after a session ended without tearing down: leaked
  git worktrees, processes still holding directories open, background jobs nobody stopped, stray
  build and scratch output. `vince-implement` already told a session to sweep up after itself and
  `vince-doctor` reported orphaned worktrees, but neither handles processes and neither helps once
  the session that made the mess is gone.

  It is the only skill that kills processes and deletes directories, so it is built to refuse:
  inventory first, attribute every item as yours / unknown / someone else's and act only on the
  first, never kill by process name, never `--force` past a dirty or unpushed worktree, never
  `rm -rf` a worktree at all. It also owns the diagnosis nothing else had - which process holds a
  directory open when a remove fails (`handle.exe` / `Win32_Process`, `lsof` / `fuser`), worked in
  escalation order instead of reaching for force.
- **A *Session resources* block in the ledger.** One row per worktree and long-running process,
  written *as it is created* rather than at the end, where a crashed session never reaches it.
  This is the attribution that lets cleanup act confidently instead of asking about everything.
- **The Stop hook catches leaked worktrees**: a ledger reading `PASS` whose recorded worktree is
  still on disk means teardown was skipped. Only `PASS` ledgers are checked, and a path that is
  gone or still a template placeholder is never a leak.

**Upgrade notes**

No new profile fields. Existing ledgers keep working; the *Session resources* block is additive
and only affects tasks started after the upgrade. If you use the Stop hook, it now blocks on
leaked worktrees as well as unproven rows - `VINCE_STOP_DISABLE=1` still turns it off entirely.

## v0.5.0 — 2026-08-11

**Vince no longer writes into the repos it works on.** 0.3.0 made per-repo profiles effectively
mandatory - the reviewer FAILs a baseline taken from an unverified inherited command - and then
put them in `<repo>/.vince/`, which meant an untracked directory in every work repo. Verification
is per-repo by nature and that does not change; where the record is *stored* is independent of
what it describes, and that is what was wrong.

**Added**

- **A config store outside the repos.** Per-repo profile, lessons, metrics and task ledgers live
  at `<store>/repos/<key>/`, defaulting to `~/.vince/` and overridable with `$VINCE_STORE` (point
  it at `<workspace>/.vince` to keep an estate's config with its hub profile).
- **Remote-derived repo keys.** `github.com__acme__billing-api`, from the origin remote - stable
  across re-cloning and moving a checkout, readable enough to find and hand-edit, and shared by
  task worktrees, so a `-wt` worktree resolves to its parent repo's config instead of a blank
  one. Repos with no remote fall back to `local__<name>__<short path hash>`.
- **`install.py where [--repo DIR] [--json]`** - prints the key, mode and every resolved path.
  Path resolution is code, not model judgement, so every session agrees and the store cannot
  fragment. The skills now call it instead of deriving paths.

**Changed**

- Per-repo config is in the store by default. A repo that carries its own `.vince/profile.md`
  still wins, which is the opt-in for repos you own and want the profile committed for a team.
- Nothing to gitignore in store mode, because nothing lands in the repo.

**Upgrade notes**

Existing in-repo `.vince/` directories keep working untouched - they are the opt-in path now. To
move a repo's config out, move `<repo>/.vince/` to the path `install.py where --repo <repo>`
prints once the in-repo `profile.md` is gone, then drop the gitignore entry. No config fields
were added or renamed.

## v0.4.0 — 2026-08-11

**Added**

- **`vince-update`.** Moves an install between releases, and owns the half `install.py` cannot:
  reading the changelog *between* the installed and target versions, stopping on uncommitted
  toolkit work / in-place edits / a task in flight rather than forcing past them, reinstalling at
  the scope and bindings the manifest recorded, and then **migrating `.vince` config** so a new
  release's fields exist instead of being silently absent. New fields arrive `unknown` or
  `blocked` with what would resolve them - never invented. Rollback is the same flow with an
  older tag, and deliberately does not strip config, since older skills read newer profiles fine.

**Changed**

- The release checklist now requires **actionable upgrade notes** naming every config field or
  section a release adds, because `vince-update` reads them to migrate existing projects.

**Upgrade notes**

No new config fields. `vince-update` itself installs like any other skill; after upgrading, use
it instead of `git pull` + reinstall so config migration happens too.

Workspace profiles, for estates with many repos under one hub. Driven by a real limitation: a
hub cannot run a hundred suites, so a hub-level profile that claims verified commands is lying.

**Added**

- **Two-level profiles.** `<workspace>/.vince/profile.md` carries the repo map, stack
  definitions, branch model, tracker, isolation key, environments and estate-wide gates;
  `<repo>/.vince/profile.md` carries verified commands and the observed baseline.
- **The invariant, stated everywhere it is read: a hub profile cannot verify a command.** Every
  per-stack command in a hub profile is `(inferred, unverified)` by construction, and confidence
  does not survive inheritance.
- **First-touch promotion.** The first task in a repo runs what it inherited, writes that repo's
  profile with the commands that actually worked and the baseline actually observed, and records
  any hub default that was wrong. It costs nothing extra - the task was running them anyway.
- **Merge semantics.** Scalars override; `dod_extras` and `known_traps` are additive and the
  hub's cannot be removed by a repo; lessons are read at both levels and routed by scope.
- **Section status vocabulary**: `verified`, `inferred, unverified`, `unknown - <tried>`,
  `blocked - <what is needed>`. Wire-proof rigs and mutation tooling are usually legitimately
  blocked at onboarding; a blank section reads as nobody thought about it, `blocked` reads as a
  gap with an unblock.
- `vince-setup` gains workspace mode; `vince-doctor` validates both levels and reports hub
  profiles claiming impossible verification, plus repos worked in that never got a profile;
  `vince-learn` routes lessons by scope.
- **Per-repo baselines on multi-repo tasks.** The ledger carries one row per repo in dependency
  order. A suite never run in repo B cannot tell you whether you broke repo B - and a baseline
  taken with an unverified inherited command is now a reviewer FAIL condition.
- `templates/workspace-profile.template.md`.

**Upgrade notes**

Nothing breaks. A single-repo profile keeps working unchanged and needs no `Inherits from`
header. Adopt the hub model by running `vince-setup` at the workspace root; existing repo
profiles are already in the right shape.

## v0.2.1 — 2026-08-11

Version selection. v0.1.0 and v0.2.0 shipped without git tags, so there was no way to install or
roll back to a specific release - only "whatever `main` happens to be". Both are now tagged
retroactively at the commits that were those releases.

**Added**

- Annotated tags `v0.1.0` and `v0.2.0`.
- `install.py` prints the toolkit's git ref beside `VERSION`, so `0.2.1 (v0.2.0-4-gabc-dirty)`
  shows a mid-line or modified clone instead of letting it claim to be a clean release.
- This changelog, and a [Versions](INSTALL.md#versions) section covering what-am-I-running,
  upgrade, pin, roll back, agent-instruction pinning, and holding the Claude Code plugin at a
  tag via `extraKnownMarketplaces` with a `ref`.

## v0.2.0 — 2026-08-11

Makes the review measure rather than judge. Three changes aimed at the same weakness: a review
resting on the model's opinion of work the model just did.

**Added**

- **Blind first pass (`vince-review` Pass 0).** The reviewer derives findings from the diff and
  the original contract *before* opening the ledger, completion doc, commit messages or any prior
  verdict — all of which it now treats as claims, not evidence. The verdict records how many
  findings came blind versus only after. Skipping Pass 0 is a hard FAIL condition.
- **Tool-backed mutation testing.** The profile gains a `mutation` section naming the stack's
  tool and its diff-scoped invocation (StrykerJS/.NET, mutmut, PIT, go-mutesting, cargo-mutants).
  TAMPER and the reviewer's A2 both run it; a mutant surviving on a changed line is a missing
  assertion to kill or waive, and a hard FAIL if neither. Hand mutation remains the fallback.
- **`reviewer_model`.** The profile can name a different model to review with. Fresh context
  breaks the correlation introduced while generating, not the correlation in a model's
  parameters.
- **Claude Code plugin packaging.** `/plugin marketplace add elroykanye/vince-gate`, then
  `/plugin install vince-gate@vince-gate`. Skills arrive namespaced: `/vince-gate:vince-implement`.
- **Opt-in Stop hook** (`hooks/vince_gate_stop.py`) that blocks a session from ending while the
  active ledger has unproven rows or no PASS verdict. Fails open in every ambiguous case.
- **New DoD gate:** new code survives mutation.
- `install.py` reports the toolkit's git ref alongside `VERSION`.

**Changed**

- `--binding auto` now includes `generic` whenever the project has an `AGENTS.md`, rather than
  using it only as a last-resort fallback. Most coding agents read `AGENTS.md`, so it is the
  widest-reach binding available.
- README states the positioning directly: spec-driven frameworks enforce process; this enforces
  evidence.
- The docs are more explicit about limits — independent review still finds a minority of defects
  and barely improves on contextual errors, which is why the wire proof and mutation gate carry
  as much weight as the reviewer.

**Upgrade notes**

Nothing breaks. Existing `.vince/profile.md` files keep working; the new `mutation` and
`reviewer_model` fields are optional and both skills degrade to the previous behaviour without
them. To adopt them, re-run `vince-setup` or add the sections by hand. Reinstall with
`install.py install` against the same scope — the manifest records what that was.

## v0.1.0 — 2026-08-11

First release.

- Six skills: `vince-setup`, `vince-implement`, `vince-review`, `vince-document`,
  `vince-doctor`, `vince-learn`.
- Harness bindings for Claude Code, Cursor, Windsurf, Codex, Gemini CLI and any AGENTS.md
  runtime, rendered from one canonical markdown source. Claude and generic verified.
- `install.py` with install / status / doctor / uninstall / list / bindings, a checksummed
  manifest, drift detection, and refusal to clobber in-place edits.
- Templates for the profile, verification ledger, review verdict, lessons and completion doc.
- Paste-to-your-agent install guide.

Rewritten to be stack-agnostic from a set of skills originally built for one platform.

---

## Releasing

1. Land the work on `main`.
2. Bump `VERSION` **in the same commit as the last change of the line** — in 0.2.0 the bump
   landed last, so three commits carried 0.2.0 features while claiming 0.1.0. `install.py` now
   prints the git ref for exactly this reason, but the bump still belongs with the work.
3. Update this file. **Upgrade notes are not optional and must be actionable**: name every
   config field or section the release adds, because `vince-update` reads them to migrate
   existing projects. "Nothing breaks" is a complete note only when nothing was added.
4. Bump `version` in `.claude-plugin/plugin.json` — plugin users only receive updates when that
   string changes.
5. Tag annotated and push: `git tag -a vX.Y.Z -m "…" && git push origin vX.Y.Z`.
