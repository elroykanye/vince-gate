# vince-gate — user guide

Vince makes an AI coding agent prove its work instead of asserting it. It is six markdown
skills and one install script; there is no service, no daemon and no account.

This guide takes you from nothing to a working gate, then explains what to expect once it is
running. If you only read one section, read [What Vince actually changes](#what-vince-actually-changes).

---

## Contents

1. [Who this is for](#who-this-is-for)
2. [What Vince actually changes](#what-vince-actually-changes)
3. [Install](#install)
4. [First project](#first-project)
5. [Running a task](#running-a-task)
6. [Reading a verdict](#reading-a-verdict)
7. [When it says FAIL](#when-it-says-fail)
8. [The files Vince creates](#the-files-vince-creates)
9. [Tiers: not everything is a payment flow](#tiers-not-everything-is-a-payment-flow)
10. [Working across harnesses and with a team](#working-across-harnesses-and-with-a-team)
11. [Keeping it healthy](#keeping-it-healthy)
12. [Making it smarter over time](#making-it-smarter-over-time)
13. [Customising](#customising)
14. [Troubleshooting](#troubleshooting)
15. [FAQ](#faq)

---

## Who this is for

You are using an AI coding agent to make real changes to a real codebase, and you have noticed
the failure mode: the agent says it is done, the tests are green, and the thing does not work.
Or it works, and you cannot tell why you should believe it does.

Vince is for that. It is heavier than a linter and lighter than a process. It costs you tokens
and minutes on every task and buys you evidence you can check.

**It is not for you if** you are prototyping, exploring, or writing throwaway code. A gate that
demands a failing test first is exactly wrong when you do not yet know what you are building.
Use it when you are building something you intend to keep.

---

## What Vince actually changes

Without Vince, a task ends when the agent believes it is done. With Vince, it ends when a
**second agent, running in a fresh context and trying to fail it**, cannot.

Four rules do most of the work:

1. **The contract is copied verbatim before any code is written.** Every acceptance criterion
   goes into a ledger word for word. Paraphrasing is how scope quietly shrinks.
2. **A test must be seen failing before it counts.** RED, then GREEN, then TAMPER — break the
   implementation on purpose and confirm the test notices. Tests that assert nothing are the
   single most common reason a task passes a review it should not have.
3. **At least one criterion is proven end to end**, over real transport, with no mocks in the
   path. Unit green is not working software.
4. **A reviewer that defaults to FAIL** starts from the diff — not from your ledger — re-derives
   the contract itself, re-runs every claimed proof, and mutation-tests the new tests. It never
   sees your implementer's reasoning, and where you can arrange it, it runs on a different model.

Before reading the ledger, that reviewer freezes `review-coverage.json`.
It does not stop discovery after finding enough evidence to FAIL: every criterion, definition-of-done item, material claim,
changed entry point, dependent, and applicable A0–A7 attack ends as proven, finding, blocked, or
explicitly unreviewed. Unreviewed work prevents PASS. Later passes also cover prior findings,
adjacent variants, and previously untouched surfaces instead of narrowing to the last patch.

What you get on your side: a ledger with the exact commands and their output, and a verdict file
with an append-only history. Both are readable in a minute, and both are checkable.

What it costs: real time and tokens per task. A standard task runs meaningfully longer than an
ungated one. That is the trade — and [tiers](#tiers-not-everything-is-a-payment-flow) exist so
you do not pay it for a typo.

---

## Install

Requirements: Python 3.8+, git, and an agent harness. Nothing else.

**On Claude Code:** `/plugin marketplace add elroykanye/vince-gate` then
`/plugin install vince-gate@vince-gate`. Skills are namespaced: `/vince-gate:vince-implement`.

**Any harness:** [INSTALL.md](INSTALL.md) has a block you paste straight into your agent; it
clones, detects the harness, installs, verifies and reports back. The rest of this section is
the same thing done by hand. Pick one route — the plugin and `install.py` install the same
skills, and running both leaves you two copies to keep in sync.

```bash
git clone https://github.com/elroykanye/vince-gate.git
cd vince-gate
python scripts/install.py bindings      # which harnesses this toolkit knows
```

Then install. **User scope** is the usual choice — Vince becomes available in every project and
never appears in any repo's working tree, so it cannot be committed by accident:

```bash
python scripts/install.py install --scope user
```

**Project scope** installs into one repo, which is what you want if the whole team should get the
gate from a checkout, or if different projects need different versions:

```bash
cd /path/to/project
python /path/to/vince-gate/scripts/install.py install --target .
```

By default the installer **detects** which harnesses the target uses and installs for each of
them. Force the choice with `--binding claude,cursor` or `--binding all`, and preview with
`--dry-run`.

Verify:

```bash
python scripts/install.py status --scope user
```

Then start a session in your harness and confirm the skills are listed.

---

## First project

Once per project, before the first task:

```
/vince-setup
```

It inspects the repo and writes **`.vince/profile.md`** — the one file that makes the generic
skills specific to your codebase. It records the test commands (each one actually run), the
integration branch, the tracker, the versioning rule, the data isolation key, the locales, and
the rigs that prove things end to end.

Two things matter here:

- **Check the profile afterwards.** Five minutes reading it is the highest-value five minutes
  you will spend on Vince. Everything downstream trusts it, and a wrong isolation key means the
  reviewer's sharpest attack is aimed at the wrong field.
- **Anything unverified must say so.** `vince-setup` marks fields it could not confirm as
  `unknown — <what it tried>` or `(inferred, unverified)`. Leave those honest; do not tidy them
  into confident-looking guesses.

Add `.vince/tasks/` to `.gitignore` unless you want ledgers in history. The profile itself is
usually worth committing — it is project knowledge.

---

## Running a task

```
/vince-implement
```

then describe the task, or point at a ticket. Invoke it **before** any code is written. Invoking
it afterwards produces a ledger reverse-engineered from the implementation, which is precisely
the rationalisation the method exists to prevent.

Before Phase 0, `vince-intake` classifies the request as `READY`, `CLARIFY`, or `BOUNCE`.
`READY` becomes a proposed contract. `CLARIFY` asks only the questions whose answers materially
change the result. `BOUNCE` stops contradictory, impossible, unsafe, unauthorized, or unbounded
work and says what minimum change would make a new request actionable. Neither `CLARIFY` nor
`BOUNCE` starts implementation.

After `READY`, `vince-route` reads the active harness's exact model mappings from the project
profile. It selects the lowest capable class — `economy`, `balanced`, `frontier`, or `reviewer` —
and the narrowest useful agent role. When the current model is wasteful or insufficient it can
recommend an exact switch and explain the token/quality tradeoff; it cannot pretend the switch
happened. Missing, stale, unavailable, or unverified mappings stop with a question rather than a
silent fallback. Claude Code, Codex, Gemini, Cursor, Windsurf, and generic mappings are independent:
verification in one harness leaves the others unverified.

Where a harness exposes both a low-latency coding model and a full reasoning model, Vince uses the
first as an `economy` fast lane for precise micro-tasks and hands architecture, security, ambiguous
debugging, and multi-file reasoning back to `frontier`. It explicitly runs the required tests after
fast-model edits; model thrift never lowers the Vince proof floor. Setup verifies account access and
preview constraints before enabling this pair.

What happens, in order:

| Phase | What it does | What you see |
|-------|--------------|--------------|
| 0 | Reads the profile and lessons, extracts the contract verbatim | `verification-ledger.md` created |
| 1 | Owning repo, dedicated worktree, **test baseline recorded** | baseline counts in the ledger |
| 2 | Plan: criterion → test → files → proof level | asks you to confirm (T3 always) |
| 3 | RED → GREEN → TAMPER → full suite, per criterion | pasted command output; surviving mutants killed |
| 4 | End-to-end wire proof over real transport | the real request/message/browser run |
| 5 | Definition-of-done gates | PASS/FAIL/N-A per gate, with commands |
| 6 | Self-attack: the three likeliest production failures, tested | findings or risks in the ledger |
| 7 | Completion doc, then hands off to `vince-review` | a verdict |
| 8 | Remediation if FAIL — root cause first, bounded rounds | round-by-round progress notes |

**Where you are expected to answer:** an ambiguous or contradictory contract (Phase 0 stops),
the plan confirmation (Phase 2), any write to shared infrastructure (always refused, always
escalated), and a disagreement with a reviewer finding.

---

## Reading a verdict

The verdict lands in the task dir as `review-verdict.md` and looks like this:

```markdown
# Review verdict: FAIL — add-export-endpoint
Reviewed: api@feature/export at a1b2c3d. Baseline suite: 142/0/3. Suite now: 145/0/3.
Blind pass: 3 findings before reading the ledger, 1 only after. Reviewer model: <model>.
Mutation: stryker --incremental on the diff - 41 mutants, 4 survived on changed lines.

## Per-AC verdict
| ID | Requirement | Claimed | My verdict | Why |
|----|-------------|---------|------------|-----|
| AC-1 | Export returns all rows for the account | PROVEN | BROKEN | mutation `return []` kept 3/3 tests green |
| AC-2 | Non-members get 403 | PROVEN | PROVEN | re-ran, RED reproduced, mutation killed the test |

## Findings
### CRITICAL-1: export tests assert on the mock, not the response [CONFIRMED] [caught: mutation]
...
## Attacks that did not break it
- Second-account token returned 403.
- 10k-row export stayed under the response size cap.
```

Read it in this order:

0. **The blind-pass line.** How many findings came from the diff alone, before the reviewer read
   your ledger? Findings that only appeared afterwards are the weaker ones — the reviewer had
   already been told what to believe. A review that found *nothing* blind is a review that read
   the answer sheet, and its PASS is worth correspondingly less.
1. **The per-AC table.** `PROVEN` means the reviewer reproduced it. `UNPROVEN` means the
   evidence did not survive. `BROKEN` means it actively found the defect.
2. **Attacks that did not break it.** This is the part that tells you how hard it actually
   tried. A PASS with a thin attack log is a weak PASS — say so and send it back.
3. **The findings**, worst first.

The `[caught: …]` tag on each finding records which attack found it. That is what
[`vince-learn`](#making-it-smarter-over-time) reads later to work out which attacks earn their
time in your codebase.

**A PASS is not a guarantee.** It means a determined adversary with your test suite and your
environment could not break it in one pass. That is a genuinely useful signal and it is not the
same as correct.

Be concrete about the size of it: independent, fresh-context review beats same-session review by
a meaningful margin, and the margin is widest on critical errors — but it still surfaces a
minority of defects, and it barely improves on *contextual* errors (does this actually work in
its real environment?). Which is exactly why the wire proof and the mutation gate exist. They do
not depend on a model's judgement at all, and on the categories review is worst at, they are
doing most of the work.

---

## When it says FAIL

FAIL is the normal first outcome, and it is the system working. The implementer takes over:
reproduces each finding, builds a fix ledger mapping finding → **root cause** → the single change
that fixes it, fixes worst-first, re-proves with RED/GREEN/TAMPER, and re-spawns a fresh reviewer.

The guard rails you should know about, because they are where you get pulled in:

- **Thrash** — the same root cause fails again, or the CRITICAL count does not drop between
  rounds — is an immediate stop and escalation. It means the root-cause model is wrong, and
  another round of the same patch shape will not help.
- **Three re-reviews without a PASS**, even while converging, is a check-in. Usually the task is
  bigger than its contract, a criterion is wrong, or something is blocked.
- **You can overrule a finding**, but not silently. If you think the reviewer is wrong, say so;
  the disagreement is surfaced to you with both arguments rather than resolved by the implementer
  quietly deciding it knows better.

---

## The files Vince creates

All inside the project, none in the toolkit:

```
<project>/.vince/
  profile.md              what makes the skills specific to this repo (commit this)
  lessons.md              what reviews have caught here (commit this)
  metrics.jsonl           one line per completed task (commit this, it is tiny)
  install.json            which bindings are installed here (machine state, gitignore it)
  tasks/
    active/<task-id>/
      verification-ledger.md        the gate: contract, proof levels, command output
      implementation-status.md      the narrative: phase, blockers, fix ledger
      review-verdict.md             current verdict + append-only history
      completion-documentation.md   what shipped, validated against the branch
    archive/<task-id>/
```

The ledger is the gate; the status file is the story; the verdict is the reviewer's artifact and
is **append-only** — a FAIL is never deleted to make a later PASS look cleaner.

---

## Tiers: not everything is a payment flow

A gate that costs the same for a typo and a payment flow gets skipped for both. So
`vince-implement` classifies each task first:

- **T1 Trivial** — comments, log messages, formatting, a config value with no behaviour behind
  it. Stub ledger, one proof, a five-point self-review. **Never** anything a user can observe.
- **T2 Standard** — everything else. The full sequence.
- **T3 Complex** — 2+ repos, a contract change, auth or data isolation, a migration,
  concurrency. Full sequence plus mandatory plan confirmation and a second reviewer pass.

The tier changes *how much* evidence, never *whether* there is evidence. The agent may move a
task **up** a tier on its own; moving one **down** requires you. You can narrow or widen the
rules per project in the profile's *Tiering overrides* — for example, "anything under
`migrations/` is always T3".

---

## What it costs, and how to spend less

Vince is thorough and thorough is expensive — a fresh-context reviewer per task is a whole second
context. Most of the avoidable cost is not the review though; it is waste around it. Four levers,
in order of payoff:

1. **Run the mechanical checks as a script, not as model turns.**
   `python <toolkit>/scripts/check.py --repo . --base origin/main` does the boring half of a
   review — stray files, bot trailers, newly skipped tests, debug statements, possible secrets,
   line-ending rewrites, branch behind base — in one command instead of ten, with a compact report
   instead of ten raw outputs. Run it before handing off *and* at the start of the review.
2. **Reset context between phases.** The ledger holds the contract, the evidence and the verdict,
   so **you do not need the conversation history to continue** — and there is now a tool that
   proves it rather than assuming it:

   ```bash
   python <toolkit>/scripts/resume.py --task <task dir> --check
   ```

   `SAFE TO CLEAR` means a fresh session can carry on from the ledger. `NOT SAFE TO CLEAR` lists
   exactly what would be lost. Vince runs this at every phase boundary, and with
   `checkpoints: suggest` in the profile it will offer you a `/compact` at the safe ones. It
   cannot run the compaction itself — that stays your keystroke — and it will never offer one
   when the check has not passed.
3. **Match the subagent to the job.** T1 tasks spawn no reviewer at all. One reviewer per task,
   not per criterion. Prefer the narrowest agent type your harness offers over a general-purpose
   one, and set `mechanical_model` in the profile so search-shaped subagents use something cheaper
   than your review model.
4. **Queue instead of parallelising.** Sessions share one limit; four at once spends it in bursts.

What never gets cut to save money: the RED step, an observed baseline, the fresh-context review,
or re-running a proof. If a task will not fit the budget properly, the honest move is to split it
and say so — not to quietly weaken the gate.

## What it sounds like

Dry, a bit sarcastic, and it explains its own vocabulary instead of assuming you share it — you
get the real term *and* the plain-English translation, so you can search for it later and
understand it now.

The humour never costs you anything, by design: a joke never carries information, severity and
verdicts are always stated flat, and it is aimed at the situation or itself, never at you. It
switches off completely for security findings, destructive operations, and its own mistakes.
Files it writes — ledgers, verdicts, commit messages — stay plain, because someone will read
those without the conversation around them.

Want it straighter? Set `voice: plain` (same honesty, no jokes) or `voice: terse` (facts only) in
the profile. Asking it in conversation works too, and sticks.

## Vince does not write into your repos

By default, **nothing Vince produces lands in a repo you are working on**. Profiles, ledgers,
verdicts, lessons and metrics live in a store keyed by the repo's origin remote:

```
~/.vince/repos/github.com__acme__billing-api/
    profile.md   lessons.md   metrics.jsonl   tasks/
```

No untracked directory in a work repo, nothing to gitignore, nothing to commit by accident. Ask
where anything is:

```bash
python <toolkit>/scripts/install.py where --repo .
```

Set `VINCE_STORE` to move the store — for a hub, pointing it at `<workspace>/.vince` keeps the
estate's config together with the hub profile.

**Want a repo to carry its own config instead?** Create `<repo>/.vince/profile.md` and it wins
for that repo. Right for a repo you own where the team should share the profile; wrong as a
default for work repos you do not control.

Since the key comes from the remote, a task worktree (`repo-TASK-123-wt`) resolves to the same
config as its parent — you do not get a blank profile every time Vince creates a worktree.

## Many repos: workspace profiles

If your repos live under a hub — `../repos/`, `services/`, a polyrepo workspace — you get two
profiles, not one, and the split is deliberate:

```
workspace/.vince/profile.md      the estate: repo map, stacks, branch model, tracker,
                                 isolation key, estate-wide gates and traps
workspace/.vince/tasks/          ledgers live here, because work spans repos
repos/service-a/.vince/profile.md   verified commands + observed baseline for that repo
repos/service-b/.vince/profile.md
```

Run `/vince-setup` at the workspace first; it detects hub mode and writes the estate profile.
Repo profiles then only carry what differs.

**The rule that makes this honest:** a hub profile *cannot verify a command*. Nobody runs a
hundred suites from the hub, so every per-stack command there is `(inferred, unverified)` by
construction, and the file says so. Which means:

- The hub gives you **defaults per stack** — matched by marker (`*.csproj`, `package.json` with
  React, `pyproject.toml`), not per repo.
- The **first task in a repo verifies what it inherited** and writes that repo's profile with the
  commands that actually ran and the baseline actually observed. It costs nothing extra, because
  the task was going to run them anyway.
- After that, the repo is self-describing and the hub is back to being defaults.

Estate-wide `dod_extras` and `known_traps` are **additive**: a repo can add gates and traps but
cannot drop one the hub imposes. Removing an estate gate is a decision at the hub, with a reason.

Multi-repo tasks carry **one baseline per repo** on the ledger, in dependency order (shared lib →
service → consumer → frontend). A suite you never ran in repo B cannot tell you whether you broke
repo B.

### Say "blocked", not nothing

Wire-proof rigs and mutation tooling usually cannot be set up at onboarding — they need running
infrastructure or credentials. Mark them `blocked — needs dev cluster credentials` rather than
leaving them blank. A blank section reads as "nobody thought about it"; a blocked one reads as a
known gap with an unblock, and `vince-doctor` will keep surfacing it until it clears.

## Working across harnesses and with a team

Vince uses the open Agent Skills format: a compact `SKILL.md` plus references loaded only at the
phase that needs them. Claude Code, Codex, Gemini CLI, and GitHub Copilot receive native skills with
progressive disclosure. Cursor and Windsurf receive conditional rules; the generic binding writes
plain markdown plus an `AGENTS.md` pointer block.

```bash
python scripts/install.py bindings                      # what is available, and its status
python scripts/install.py install --target . --binding claude,cursor
python scripts/install.py install --target . --binding all
```

The `claude`, `codex`, and `generic` bindings are verified. The others follow each runtime's
documented convention and are marked `unverified` — preview with `--dry-run`, check the paths
against your runtime's docs, and correct the JSON in `bindings/` if they differ. Adding a
binding is a 12-line JSON file; see [`bindings/README.md`](bindings/README.md).

**Using Cursor or Codex instead of Claude Code?** Both work. Codex loads the skills natively from
`.agents/skills/` and has real subagents, so the review runs the same way — and its subagent TOML
can pin the reviewer's model, which is one thing Claude Code cannot do. Copy
`templates/codex-reviewer-agent.toml` to `.codex/agents/vince-review.toml`, use a persistent
parent session (not `codex exec --ephemeral`), and start Codex with
`--add-dir <resolved task-root>` when `install.py where --repo .` returns an external directory.
This named-agent path was live-verified through a persisted Vince verdict. Cursor loads them as
`.mdc` rules, but has no subagent mechanism, so the fresh-context review becomes a second chat you
open and paste the handoff into. That is the same rigour with one manual step, and the isolation
is if anything cleaner — but it is easier to skip, so the discipline has to come from you.

Gemini installs to `.gemini/skills/<skill>/SKILL.md`; GitHub Copilot installs to
`.github/skills/<skill>/SKILL.md`. Their user paths are `~/.gemini/skills` and
`~/.copilot/skills`. Both bindings follow current vendor documentation and are render-tested, but
remain `unverified` until Vince completes a live discovery and invocation probe in each runtime.

`check.py` and `resume.py` are plain Python and the ledger is a file, so those work identically
everywhere. See [docs/harnesses.md](docs/harnesses.md) for the per-harness table.

**For a team:** install project-scoped and commit `.claude/skills/` (or your harness's
equivalent) plus `.vince/profile.md` and `.vince/lessons.md`. Everyone gets the same gate and
the same accumulated knowledge. If teammates use different harnesses, install every binding they
use — a teammate on an uninstalled harness gets no gate at all, silently.

The `generic` binding writes a delimited block into `AGENTS.md` that states the gate in plain
language. Several harnesses read `AGENTS.md`, so that block alone is often enough.

---

## Keeping it healthy

Three jobs, three skills: **`/vince-doctor`** when something is broken, **`/vince-cleanup`** when
a session left resources behind, **`/vince-update`** when a newer release exists.

The repository also ships `scripts/vince.py` for compact operational checks:

```bash
python scripts/vince.py health --profile <profile> --manifest <install.json> --task-root <tasks>
python scripts/vince.py route-refresh --profile <profile> --harness codex --economy <model> --balanced <model> --frontier <model> --reviewer <model> --explorer-agent <agent> --worker-agent <agent> --reviewer-agent <agent>
python scripts/vince.py release-check --repo . --expected-version <version> --expected-tag v<version>
python scripts/vince.py codex-discovery --codex codex
python scripts/vince.py archive-task --task-root <tasks> --task <task-id> --repo <repo>
```

`health` is the dashboard-style report: install versions per harness, live-verified versus
render-only status, open or failed tasks, stale route mappings, and the exact next action. Route
refresh writes only explicit model and agent identifiers supplied by the user or harness; it never
guesses provider names. The release check verifies `VERSION`, changelog, tag and installed-version
readiness. `codex-discovery` is the stronger post-install proof for Codex: in live mode it starts
Codex and confirms the Vince skills are actually discoverable. `archive-task` moves only PASS
tasks from `active/` to `archive/`; FAIL or open tasks stay put.

```
/vince-cleanup     # leaked worktrees, processes holding directories open, stray output
```

Sessions end badly — crashes, interrupts, a window closed. What survives is a git worktree full
of throwaway state, a dev server or watcher still holding a directory (so it will not delete),
and build output nobody needs. Cleanup inventories all of it, works out what belongs to a
finished task, and removes only that. Anything it cannot attribute it reports rather than
touching — a `node` process it did not start might be your editor's language server.

If a directory will not delete, that skill is where the diagnosis lives: it finds the process
holding the handle instead of escalating to force. Update runs doctor's checks; doctor never changes version.

```
/vince-update      # compares versions, reads the changelog between them, reinstalls,
                   # and migrates your .vince config so the new fields actually exist
```

That last part is the one worth knowing about. A release that adds a profile field does not add
it to *your* profile — the new skills read it, find nothing, and fall back silently. Upgrading
by hand with `git pull` leaves that gap; the skill closes it, and tells you which fields it had
to leave `unknown` or `blocked`.

Vince also degrades quietly on its own: a renamed test script, a retired branch, a harness update
that moves the skills directory. Nothing announces itself, and each one makes the next task's
evidence a little more fictional.

```bash
python scripts/install.py doctor --scope user          # or --target <project>
python scripts/install.py doctor --target . --fix      # repair everything except in-place edits
```

```
/vince-doctor
```

The skill goes further than the script: it validates the **profile against the repo** by running
the recorded commands, resolving the branch, and checking every path; then it looks for orphaned
task dirs, work that merged without a review, and leaked worktrees.

**In-place edits are not drift to discard.** If a skill was improved inside `.claude/skills/`,
that improvement never made it home — copy it into the toolkit's `skills/` and reinstall. The
installer refuses to overwrite such files without `--force` precisely so you get the chance.

There is also self-healing during a task: when a profile command fails, `vince-implement`
re-derives it once, verifies the replacement, repairs the profile and records the correction —
and stops if a second field turns out wrong, because that means the profile needs a full refresh
rather than patching mid-task.

---

## Making it smarter over time

Run after a PASS (`vince-implement` does this itself), or once over the history when adopting
Vince on an existing project:

```
/vince-learn
```

It converts findings into configuration:

| Signal | Becomes |
|--------|---------|
| A finding class seen **twice** | a `known_traps` line the reviewer sweeps every time |
| A finding class a command can detect | a `dod_extras` gate the implementer must pass |
| A correction you made | a lesson in `.vince/lessons.md` |
| A hard-won wire proof | a `wire_proofs` entry nobody has to rebuild |
| A one-off with no pattern | **nothing** — noise is what makes these files stop being read |

The point is that the next task is stopped *at the gate* rather than caught at review. It also
reads `.vince/metrics.jsonl` and tells you which attacks actually earn their time here, whether
rounds-to-PASS is trending down, and whether a tier is being abused. Under about five tasks it
will say so rather than invent a trend.

Adopting on an existing project: it mines PR review comments, `HACK`/`FIXME` clusters and revert
chains, and asks you directly what breaks that shouldn't. Five real entries on day one beats
thirty generic ones.

---

## Customising

Almost everything project-specific belongs in `.vince/profile.md`, not in a skill:

- **Add a gate everyone must pass** → `dod_extras`, in the same `Gate | Verify | PASS condition`
  shape as the catalog. The verify command must actually run.
- **Wire in mutation testing** → the `mutation` section: the tool and its **diff-scoped**
  invocation. This is the highest-leverage single field in the profile after the isolation key.
- **Have a different model review** → `reviewer_model`.
- **Record a trap** → `known_traps`. The reviewer sweeps these in its A5 pass.
- **Change tier rules** → *Tiering overrides*.
- **Share config across many repos** → a workspace profile; see [Many repos](#many-repos-workspace-profiles).
- **Point at your decisions/runbooks** → the `memory` section. Both skills read it, and an
  implementation contradicting a recorded decision is a finding even when tests pass.
- **Name your wire-proof rigs** → `wire_proofs`. The highest-value section in the file.

Edit the **skills** only for changes true of every project. Edit them in the toolkit's `skills/`
directory and reinstall — never in the installed copy, which the toolkit overwrites. To add a
skill: create `skills/<name>/SKILL.md` with `name` and `description` frontmatter (the description
drives auto-activation, so put the trigger phrases in it), bump `VERSION`, reinstall.

---

## Troubleshooting

**The skills do not appear in my harness.** Check the binding's paths against your runtime's
docs (`install.py bindings`); `unverified` bindings are the usual suspect. Confirm the install
landed where you think (`install.py status --target .`). Project-scoped skills usually take
precedence over user-scoped ones of the same name.

**The agent skipped the gate.** Skills auto-activate on their description; a terse "fix the
login bug" may not trigger it. Invoke it explicitly (`/vince-implement`), and add the gate to
your project's `CLAUDE.md`/`AGENTS.md` — the `generic` binding writes exactly that block.

**Everything is failing review.** Look at *what* is failing. Dead tests on mutation is the
system working. If the same finding survives two rounds, that is thrash and it should have
stopped itself — check whether the reviewer is getting a persuasive spawn prompt, which defeats
it entirely.

**Review passes things I later find broken.** Almost always a profile gap: a wrong isolation
key, a missing wire-proof rig, or a locale/permission model the profile does not describe. Fix
the profile, then add the class as a `dod_extras` gate via `vince-learn`.

**It is too slow for small changes.** Tiering is the answer — check that T1 rules match your
reality and use *Tiering overrides*. If T2 tasks are slow because the suite is slow, record a
faster targeted command in the profile alongside the full one.

**The reviewer will not write its verdict.** It needs write access and the task directory in its
prompt. Without either, it reviews and silently skips persisting — check the spawn prompt.

**I edited a skill and now install refuses.** That is the guard working. Copy your edit into the
toolkit's `skills/`, reinstall, and the refusal goes away. `--force` discards your edit.

---

## FAQ

**Does this work without Claude Code?** Yes. Six markdown files and a Python script; the
bindings render them for other harnesses, and the `generic` binding works anywhere an agent can
read a file. The `claude`, `codex`, and `generic` bindings are verified; the rest are documented
conventions you should check.

**Does Vince send anything anywhere?** No. It has no network access, no telemetry, no account.
Every file it writes is inside your project or your home directory.

**Will Vince end up in my repo's git history?** Only if you install project-scoped and commit it.
User scope (`--scope user`) never touches a project's working tree. If you do install into a
project, gitignore `.vince/install.json` and `.vince/tasks/`.

**Can the agent just... not follow it?** By default, yes — these are instructions. What makes them
stick is the artifacts: a missing ledger, a missing verdict, or a ledger with no command output
is immediately visible to you. Vince makes skipping the process *legible*.

If you want it actually enforced, [hooks/README.md](hooks/README.md) ships an opt-in Claude Code/Codex
**Stop hook** that blocks the session from ending while the active ledger has unproven rows or no
PASS verdict. It is experimental and has a known upstream caveat, which is why it is not part of
a normal install.

**Why does the reviewer have to run in a fresh context?** Because an agent cannot un-see its own
reasoning. A reviewer that read the implementation's justification inherits its blind spots and
its confidence. Reviewing twice in one session measures *worse* than reviewing once — the second
pass anchors on the first. This is the single most important structural rule in the toolkit, and
the most tempting one to skip.

**Then why does it also start blind, if the context is already fresh?** Because the ledger crosses
that boundary. A fresh reviewer handed a document whose every row says PROVEN has been framed just
as effectively as one that sat in the implementer's context — and agents are more susceptible to
that framing than people are. Fresh context and the blind pass fix two different leaks.

**Is a PASS a guarantee?** No. See [Reading a verdict](#reading-a-verdict).

**Can I use just the reviewer?** Yes. `vince-review` works on any branch — give it the task, the
repo and branch, and a task dir to write to. It is weaker without a ledger to attack (there are
no claimed proofs to re-run), but the mutation, isolation and behaviour attacks all still apply.

---

## Where to go next

- [`INSTALL.md`](INSTALL.md) — paste-to-your-agent blocks for install, update, repair, uninstall.
- [`docs/methodology.md`](docs/methodology.md) — why each rule exists, and the failure mode it
  stops. Read this before deciding whether to adopt.
- [`docs/skills.md`](docs/skills.md) — every phase and attack pass in detail.
- [`docs/profile.md`](docs/profile.md) — every profile field and who reads it.
- [`docs/harnesses.md`](docs/harnesses.md) — the binding model, and how to add a runtime.
- [`docs/install.md`](docs/install.md) — install, update, drift, uninstall.
