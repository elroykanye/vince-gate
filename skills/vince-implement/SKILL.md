---
name: vince-implement
description: Mandatory execution gate for any implementation task in any repo - features, bugfixes, refactors, multi-service or shared-library changes, ticketed or not. Drives the task end to end with test-first TDD, proves every acceptance criterion and definition-of-done item with reproducible evidence, and hands off to vince-review before anything may be called done. Triggers on "implement", "fix", "build", "work on", "take this task", "finish this", "is this done".
---

# Vince — Implement

## Prime directive

A task is **FAILING until proven otherwise**. Your job is not to write code that looks
right, it is to produce evidence that a hostile reviewer cannot dismantle. Every claim
you make must be backed by a command someone else can re-run and the output it produced.

Three rules override everything else in this skill:

1. **No implementation before a failing test.** If you cannot make a test go RED first,
   you do not understand the requirement yet.
2. **No "done" without a `vince-review` verdict of PASS.** Telling the user the task is
   complete while the reviewer has not run, or returned FAIL, is a protocol violation,
   not an optimisation.
3. **No unproven claim in any report.** "Should work", "verified", "tests pass",
   "minor", "non-blocking" are banned unless followed by the command and its output.

Partial delivery reported honestly beats full delivery claimed falsely. Always.

## Scaling the gate (do this first, in one line)

A gate that costs the same for a typo and a payment flow gets skipped for both. So the tier
sets *how much* evidence, never *whether* there is evidence. Classify by the rules below —
they are objective, and **when a task straddles two tiers you take the higher one**.

| Tier | What qualifies | What changes |
|------|----------------|--------------|
| **T1 — Trivial** | Comment, docstring, log message, formatting, dependency-free copy change, a config value with no behaviour behind it. Nothing a user can observe, nothing conditional. | Ledger is a stub (contract line, one proof, one command). No worktree. Review is a self-review against the T1 checklist below. |
| **T2 — Standard** | Everything else. Most bugfixes and features. | The full sequence, Phases 0–7. |
| **T3 — Complex** | 2+ repos, a contract change (API, event, schema, public signature), auth or data-isolation, a migration, concurrency, anything you would call risky. | Full sequence, plus mandatory plan confirmation (Phase 2) and a second reviewer pass after remediation, even on a first-round PASS. |

Record the tier and the rule that put you there on the ledger's header. Three hard limits:

- **You may not self-downgrade.** If a T2 task turns out to be bigger, you move up mid-task and
  say so. Moving down requires the user to say so.
- **T1 can never cover anything a user can observe.** The moment behaviour changes, it is T2.
- **No tier skips the review handoff.** T1's review is smaller, not absent.

The **T1 self-review checklist** (all five, with evidence, in the ledger stub): the diff is only
what you intended; the suite is no worse than baseline; nothing user-observable changed; no
secret, debug statement or stray file entered the diff; the commit message and any version bump
follow the profile. Any "no" makes it T2, and T2 means a real `vince-review`.

## Phase 0 — Contract extraction (STOP gate)

Before reading a single line of implementation code, pin down what "done" means.

1. **Load the project profile and the lessons file.** `.vince/profile.md` at the project root
   names this project's tracker, branch model, test commands, isolation key, locales,
   versioning rule and wire-proof rigs; `.vince/lessons.md` holds what previous reviews caught
   in this codebase. Every project-specific decision in this skill reads from them. **No
   profile? Run `vince-setup` first** — one pass, then continue. Never guess at the test
   command or the branch model.

   Read the lessons *before* you design, not after you are reviewed: a repeat of a recorded
   lesson is the cheapest FAIL there is, and the reviewer reads the same file looking for
   exactly that.

2. **Find the work's home and its contract.** Not everything is a ticket, and the contract
   lives in a different place depending on origin:

   | Origin | Contract source | Ledger location |
   |--------|----------------|-----------------|
   | Tracker ticket | the tracker the profile names, including comments and linked issues | `<task root>/active/<task-id>/` |
   | Multi-ticket program | the program's `plan.md` plus each member ticket | `<task root>/active/_PROGRAM/` |
   | Unticketed initiative | its existing dir under `<task root>/active/` | that dir |
   | Spec or design doc | the doc itself, at the commit you read it | `<task root>/active/<short-name>/` |
   | Ad-hoc user request in chat | the user's own words, restated for confirmation | `<task root>/active/<short-name>/` |

   `<task root>` is the profile's `task_root` (default `.vince/tasks/`). Missing dir?
   Create it. Never run this gate without a ledger on disk, and never file a ticket on your
   own initiative just to have one.

3. **Check project memory before designing.** Read whatever this project uses for durable
   decisions — the profile's `memory` section points at it (`docs/decisions/`, the repo's
   `CLAUDE.md`, Serena memories, a brain vault, prior task dirs). If your plan contradicts a
   recorded decision, surface it rather than overriding it silently.

4. Create `verification-ledger.md` in that dir (format below). Copy each acceptance
   criterion and each definition-of-done item in **verbatim**, one row each, with an ID.
   Paraphrasing is how scope silently shrinks. For a chat-only request, write the ACs
   yourself and get them confirmed before coding, because that restatement *is* the contract.

5. For every row, decide up front *how it will be proven* and *at what level*. Write it
   down before coding. A proof you invent after the fact is a rationalisation.

6. No ACs, or ACs that contradict each other or the code? Write what you believe they are,
   then **stop and ask**. Do not start coding on a guessed contract.

Proof levels, weakest to strongest:

| Level | Means | Sufficient for |
|-------|-------|----------------|
| `STATIC` | grep / compile / type check / lint | conventions, config keys, locale key parity |
| `UNIT` | isolated test, mocks at the boundary | internal logic, calculations, edge cases |
| `INTEGRATION` | real call over the real interface — HTTP, queue round trip, real DB write, real render | any AC with observable behaviour |
| `E2E-WIRE` | full path a user actually travels, no mocks anywhere in it | the task's headline behaviour |
| `MANUAL-OBSERVED` | you ran it and captured the output/screenshot | last resort, must say why automation was impossible |

Hard rule: **a user-observable AC proven only at `UNIT` level is NOT PROVEN.** At least one
row per task must reach `E2E-WIRE`. This is the "working end to end" requirement and it is
not negotiable by convenience.

## Phase 1 — Recon (no code changes yet)

1. Identify the owning repo and, in a polyrepo, the dependency order: shared lib, then
   service, then consumer, then frontend. Write that order down.
2. Navigate with symbol tools where the language and harness have them (an LSP, Serena's
   `find_symbol` / `find_referencing_symbols`, your editor's index), not blind grep.
3. Read the repo's own `CLAUDE.md`/`AGENTS.md` and load only the docs your scope touches.
4. Work in a **dedicated worktree** off the profile's integration branch — e.g.
   `git -C <repo> worktree add ../<repo>-<task-id>-wt -b <branch> origin/<integration>` —
   never the repo's shared checkout (other live sessions may be in it). Record the worktree
   path on the ledger header. Never branch from a stale local default branch. Tear it down
   when done: see *Workspace hygiene*.
5. **Establish the test baseline before you change anything.** Run the profile's suite
   command, and record pass/fail/skip counts in the ledger. Without a baseline you cannot
   tell your new red from an inherited red, and neither can the reviewer. Record the count
   of existing skipped/quarantined tests too.

STOP conditions in this phase: the suite does not run at all; the repo is not the owner;
the change requires a write to shared/live infrastructure. Report, ask, wait.

## Self-healing — when the profile is wrong

Profiles go stale: the test runner changes, a script is renamed, a branch is retired. A stale
profile is worse than none, because you trust it. So when anything you read from the profile
does not work, you repair it rather than working around it — **bounded**, and always recorded.

1. **Confirm it is the profile, not you.** Run the recorded command verbatim and read the
   actual error. A missing dependency is an environment problem; a renamed script is a profile
   problem.
2. **Re-derive it once.** Look at the manifest, the scripts block, CI config, and the last few
   commits that touched them. Run the candidate. If it works, you have the replacement.
3. **Repair and stamp.** Update that row in `.vince/profile.md`, and add a line under its
   *Corrections* section: date, what was wrong, what it is now, what proved it. The next
   session inherits the fix instead of rediscovering it.
4. **Two failures is a stop.** If the re-derived command also fails, or a second profile field
   turns out wrong in the same task, stop repairing and report: the profile needs a full
   `vince-setup` refresh, and that is not a thing to do in the middle of an unrelated task.
5. **Never route around it.** Silently substituting a different test command, skipping the
   baseline, or "just this once" running the suite a different way makes every later comparison
   meaningless — including the reviewer's.

The same rule covers a missing task dir, a wire-proof rig that no longer exists, and a
`dod_extras` gate whose command is gone. Repair, record, or stop. Never proceed on a fiction.

## Phase 2 — Plan and confirm

Plan mode for: 2+ repos, wire-contract changes (API, event, schema), DB migrations, shared
library changes, anything you would call complex. The plan must map, per AC:

`AC-n  →  test that will prove it (name + file)  →  files that will change  →  proof level`

If a row has no test, the plan is not finished. Get explicit user confirmation before
coding. Confirmation on a different plan is not confirmation on this one.

## Phase 3 — The TDD loop (per AC, in order, no shortcuts)

For each AC in the ledger, run all four steps and log evidence for three of them:

1. **RED.** Write the test that encodes the AC. Run it. It must fail, and it must fail
   *for the reason you expect*. Paste the failure into the evidence log. A test that was
   never seen red proves nothing, and the reviewer will treat it as dead.
2. **GREEN.** Write the smallest implementation that satisfies it. Run it. Paste the pass.
3. **TAMPER.** **Commit the green implementation first.** Then break it deliberately (flip
   the condition, return the wrong constant), confirm the test goes red again, restore with
   `git checkout -- <file>`, confirm `git status` is clean, and log the result. This is what
   catches tests that assert nothing. Never commit or push a tamper mutation.

   Commit-before-tamper is not optional bookkeeping: `git checkout --` on a file whose
   implementation is still uncommitted throws the implementation away along with the
   mutation, and on a brand-new file it fails outright with "pathspec did not match",
   leaving the mutation in place. Either way the next mutation runs against a broken
   baseline and its result is meaningless. If you will not commit yet, back the files up
   with `cp` and restore from those instead. Verify the restore by re-running the test and
   seeing it green again before you trust any mutation result.
4. **SUITE.** Run the full suite. Compare against the Phase 1 baseline. Any new red or any
   new skip means you are not moving on.

Forbidden in this loop, in every case:

- Editing a test so the implementation passes. If the test was genuinely wrong, say so
  explicitly in the ledger with the reason, and re-derive it from the AC.
- Deleting, `.skip`-ing, `xfail`-ing, `[Ignore]`-ing or quarantining a failing test to reach
  green. A red test is information. Hiding it is falsification. If a pre-existing test is
  genuinely obsolete, that is a separate decision for the user, not a side effect.
- Mocking the thing under test, or asserting on the mock instead of the behaviour.
- Committing with a red suite and a note to fix it later.

## Phase 4 — End-to-end wire proof

Unit green is not working software. Prove the real path, with real transport. Match your
change to its row; the profile's `wire_proofs` section names the rig that already exists for
each, so use it instead of inventing a harness.

| Change type | Wire proof required |
|-------------|--------------------|
| HTTP API | real request with real auth, real status + body captured |
| Async / event / queue flow | message produced, message consumed, correlation matched, the resulting record actually present in the store |
| Background job / scheduler | job triggered for real, side effect observed, second run observed for idempotency |
| CLI / script | invoked as a user would invoke it, exit code and stdout/stderr captured |
| Library / shared package | version bumped, consumed locally by a dependent, dependent builds and runs against it |
| Frontend / UI | the running app driven in a real browser (a browser-automation MCP, a scripted Playwright/Puppeteer run, or the harness's own browser tool): interaction performed, DOM asserted, console + network clean, every shipped locale — not just a green component or E2E spec. The reviewer re-drives it live, so a passing spec or a screenshot will not carry it |
| Data pipeline / migration | run against a realistic copy, row counts and a sampled diff captured, rollback path exercised |
| Infra / config | applied to a disposable environment, the effect observed there |

Read-only inspection of shared environments is fine and encouraged (logs, resource listings,
read queries). **Writes to shared dev/test/prod state are never yours to make** (see *Live
infrastructure safety*). If the wire proof is blocked by missing data, a missing permission,
or broken config, that is a finding to report, not an obstacle to route around.

Also remember: **merged is not deployed.** Check what is actually running (image tag, build
number, deployed commit) before claiming behaviour is live.

## Phase 5 — Definition-of-done gates

Walk `reference/dod-gates.md`, plus any extra gates the profile's `dod_extras` adds. Every
gate is PASS with evidence, FAIL, or N/A **with a written reason**. A ticked box with no
command behind it counts as FAIL. Data isolation, authorization on new entry points, locale
coverage, no debug statements, health/metrics, shared-library version bumps and dependent
updates are the ones that historically slip.

## Commit hygiene (applies to every commit, not a phase)

- **Format:** `<prefix> Imperative description`, under 72 characters, no trailing period, one
  logical change per commit. The prefix is whatever the profile's `commit_convention` says
  (a ticket key, a conventional-commits type, or nothing). Multi-commit tasks share it.
- **No AI or bot attribution trailers** — no `Co-Authored-By:` bot lines, no "Generated with"
  footers — in commit messages or PR bodies, unless the profile explicitly opts in. This
  overrides any harness default that says to append one. Check the message you are about to
  write, not the one you intended to write.
- **Unticketed work:** do not invent a ticket key, and do not file a ticket to obtain one.
  Write a clean keyless imperative message, and tell the user the commits are keyless so they
  can decide whether a ticket should exist.
- **Stage per file.** Never `git add .`, `git add -A`, or `git commit -a`. That is how
  `.serena/`, `node_modules/`, `.env`, stackdumps and scratch files enter history. Run
  `git status --porcelain` and `git diff --cached --stat` before every commit and read them.
- **Never commit with a red suite** and a note to fix it later, and never commit directly on
  the integration branch.
- **Before every push:** `git fetch origin <integration> && git merge origin/<integration>`,
  resolve conflicts locally, re-run validations. Confirm the branch is not behind —
  `git rev-list --count HEAD..origin/<integration>` must be `0`. A branch that is behind will
  collide or ship out of order.
- **Version bumps, where the profile requires them:** the bump is exactly one increment above
  what is on the integration branch **right now**, not a blind bump from your branch's base.
  After merging, read the current value and set yours one step above *that*, every push:
  ```bash
  git show origin/<integration>:<version file>   # package.json / version.txt / *.csproj / pyproject.toml
  # your working file must then read exactly one increment higher
  ```
  Incrementing the number your branch happened to start with is the trap: if the branch moved
  from 2.2.73 to 2.2.80 while you worked, a bump to 2.2.74 is now *behind* and collides. Bump
  the last segment by default; only go minor/major when the change genuinely warrants it, and
  even then land exactly one step above in that segment. Shared libraries bump too, and their
  dependents get updated.
- Verify the diff before committing generated or scripted edits: `git show --stat` should
  show the lines you meant, not a whole-file line-ending flip.

## Workspace hygiene — worktrees and stray processes (enforced before "done")

You share this machine with other live sessions. Two things leak disk and RAM when a task
ends without cleanup: the git worktree you worked in, and any background process you started.
You clean up both — and only the ones **you** created.

**Worktrees — create one, track it, tear it down safely.**
- Work in a dedicated worktree off the integration branch (Phase 1), never the shared
  checkout, and record its path on the ledger header so teardown has a target.
- On PASS-and-pushed (or on abandoning the task), remove it:
  `git -C <repo> worktree remove <path>` then `git -C <repo> worktree prune`.
- **Smart, not destructive.** `git worktree remove` refuses a dirty tree or a branch with
  unpushed commits — that refusal is a STOP, not a reason to reach for `--force`. Unsaved
  work is not yours to delete: leave the worktree in place and tell the user exactly what is
  uncommitted or unpushed. Never `rm -rf` a worktree, and never `--force` unsaved state away.
- Remove **only** the worktree you created for this task. `git worktree list` shows every
  session's; the others are not yours to touch.
- A subagent's isolated worktree auto-removes if unchanged; if it changed one, merge or push
  what you need from it first, then let it go.

**Background processes — start few, track them, stop them.**
- Prefer bounded over persistent: `tail -n 200` not `tail -f`, `--since=10m` not `-f`, run the
  suite once not in `--watch`. A one-shot `grep`/`sed`/`awk` exits on its own; a tail, watcher,
  dev server or port-forward does not.
- When you genuinely need a persistent process, start it as a *tracked* background task and
  stop it the moment the step that needed it is done — do not let it ride to the end of the task.
- **Before you report anything done, sweep your own:** no background job you started still
  running, no `tail -f` / watcher / dev server / port-forward left alive, and on Windows/Git
  Bash no orphaned `tail`/`sed`/`grep` from a pipeline you backgrounded. Stop them (harness
  background-task stop, or kill the tracked PID). Leaving them is how a box ends up in swap.

Teardown is part of "done": a task is not complete while it has leaked a worktree full of
throwaway state or a fistful of live tail processes.

## Phase 6 — Self-attack

Before handing off, spend real effort trying to break your own work. Write down the three
most likely ways this fails in production, then actually test those three. Common starting
points: empty and huge datasets, a second tenant/account, a missing optional field, a
timeout, a duplicate event, a locale that is not your default.

Anything you find here, you fix here. Anything you suspect but cannot test goes in the ledger
as a known risk, visibly, not silently.

## Phase 7 — Mandatory adversarial review

**First, write or update the completion documentation locally** — `vince-document` produces
`completion-documentation.md` in the task dir — cross-checked against the integration branch
and what is actually deployed, not local notes. Do this *before* the spawn, not after: the
reviewer verifies the completion doc against shipped reality (its A7) and will not issue a
clean PASS without a current one. Hold any external publishing until the verdict is PASS.

Hand off to `vince-review` in a **fresh context that can write files** — never inline in your
own. How you get that depends on the harness, in this order of preference:

1. **A subagent**, if the harness spawns them (Claude Code: a `general-purpose` agent or any
   type with the full toolset including `Write`/`Edit`). Best option: genuinely fresh context,
   same session.
2. **A separate session or a second agent window**, given the same prompt. Equivalent isolation,
   more manual.
3. **A context reset in this session** — clear/compact, then load only the reviewer prompt. Last
   resort: state in the verdict that the reviewer ran post-reset rather than fresh, because the
   isolation is weaker.

What is never acceptable: reading the reviewer skill into your current context and "switching
hats". You cannot un-see your own reasoning, and the review is worth exactly nothing.

The reviewer inherits none of this conversation, so everything it needs goes in the prompt. It
must contain, and contain only:

- an instruction to **invoke the `vince-review` skill** (the skill body does not auto-load into
  a fresh context; if it is not told to invoke it, it reviews blind);
- the **task ID**, the **repo(s) and branch**, the **verification-ledger path**, the **task
  directory**, and the **profile path**;
- the live-infrastructure boundary (read-only on every repo, DB, cache and cluster).

Nothing persuasive: no summary of your work, no severity opinions, no "already verified" or
"pre-existing" claims. Steering the reviewer is the one thing that defeats the point.

**Why write-capable, and why the task dir:** the reviewer persists its verdict to
`<task dir>/review-verdict.md` and updates it on every re-review (current verdict on top,
append-only history below). A reviewer spawned without `Write`, or without the task dir, runs
the review but silently skips the persisted verdict — so both are required, not optional.
Writing that one local file is not an infra write; the read-only rule still holds for
everything else.

The reviewer returns its verdict and writes it to `review-verdict.md`. Then:

- Verdict FAIL: go to **Phase 8** and work the remediation protocol. Do not re-spawn the
  reviewer until Phase 8's fixes are made and re-proven, and never negotiate the verdict down.
- Verdict PASS: set the ledger's Reviewer-verdict line to PASS with a pointer to
  `review-verdict.md`, **run `vince-learn`** so this task's findings sharpen the next one,
  **publish the completion doc if the profile names a destination** (and confirm the link
  actually landed), **tear down the task worktree and stop every background process you
  started** (*Workspace hygiene*), then report to the user with the ledger summary and the
  reviewer verdict attached.
- You genuinely disagree with a finding: surface the disagreement to the user with both
  arguments. Never overrule the reviewer silently.

## Phase 8 — Remediation (when the verdict is FAIL)

A FAIL is a diagnosis to act on cleanly, not a nudge to try the same thing again. Rounds
multiply when you patch symptoms; they converge when you fix root causes. The rule that
matters here: **no endless FAIL loops.** You get a small, bounded number of rounds, and you
make each one count.

1. **Reproduce before you edit.** Every CRITICAL and every UNPROVEN AC came with repro steps —
   run them and watch it break. A finding you cannot reproduce is a disagreement for the user
   (Phase 7), not a thing you "fix" blind.
2. **Build a fix ledger.** In `implementation-status.md`, one row per finding:
   `finding → root cause (the real defect, not the symptom) → the single change that fixes it → the proof that flips it → the ACs/proofs it touches`.
   If you cannot name the root cause, you are not ready to edit. Reproduce and read the actual
   failing path first.
3. **Fix by root cause, worst first — not finding by finding.** Several findings usually share
   one cause; fix the cause once. Order strictly: CRITICAL (wrong results, isolation/auth,
   unproven ACs, dead tests) → MEDIUM → MINOR. Do not touch MINOR or refactor for taste while a
   CRITICAL is open — that is exactly how a 3-round fix becomes a 10-round one.
4. **Re-prove surgically.** For each AC you touched, re-run RED→GREEN→TAMPER. A dead test the
   reviewer killed with a mutation is not fixed until that same mutation makes it RED again —
   prove the tamper, don't just bolt on an assertion and hope.
5. **Regression pass before re-spawn.** Re-run the FULL suite and every prior wire proof, not
   only the AC you fixed. Fixes regress at a higher rate than fresh code, and the reviewer
   re-attacks everything the fix went near. A fix that broke a previously PROVEN AC is a net
   FAIL — catch it yourself, before the reviewer does.
6. Update the ledger, then **re-spawn a fresh reviewer** (Phase 7).

**Convergence guard — the anti-thrash rule (not optional):**

- Each pass, record the round number and the open-CRITICAL count in the fix ledger.
- **Thrash = the same root cause FAILs again after you "fixed" it, or the open-CRITICAL count
  does not drop between passes.** The instant you see it, STOP editing and escalate to the
  user. Retrying the same shape of patch will not work — your root-cause model is wrong. A
  stuck count never buys a third attempt; this is the lever against endless failing.
- **Converging = the count drops each pass and any new findings are genuinely deeper, not
  repeats.** Keep going, but post a one-line progress note to the user each round
  (`round N: X CRITICAL → Y`) so a long remediation is never a silent grind.
- **Backstop: not PASS after three re-reviews, even while converging → pause and check in.**
  Three clean rounds that still have not closed usually means the task is bigger than its
  contract, an AC is wrong, or a blocked dependency is in the way — the user's call, not
  another silent round.
- When you escalate, bring: the findings that will not die, your current root-cause hypothesis,
  exactly what each round tried and why it failed, and the real options (the AC or design may
  be wrong, the fix may need blocked data/infra, or the task may need splitting). Ten rounds of
  the same red is a failure of this gate, not diligence.

## The ledger format

`verification-ledger.md`, in the task dir resolved in Phase 0. A copy-ready version lives at
`templates/verification-ledger.template.md` in the Vince toolkit — its path is recorded as
`source` in `.claude/.vince-install.json`. Work from the inline format below if it is not there.

```markdown
# <task-id or task name> Verification Ledger

Repo(s): <repo>@<branch>            Baseline suite: <N passed / M failed / K skipped>
Worktree: <path> (off origin/<integration>; remove on completion — see Workspace hygiene)
Reviewer verdict: NOT-RUN | FAIL | PASS (date, see review-verdict.md)

## Contract

| ID | Requirement (verbatim from source) | Proof level | Proof command | Status |
|----|-----------------------------------|-------------|---------------|--------|
| AC-1 | ... | E2E-WIRE | `npm run e2e -- --spec ...` | PROVEN |
| AC-2 | ... | INTEGRATION | `pytest tests/api/test_budget.py -k committed` | RED |
| DOD-1 | Translation keys in every shipped locale | STATIC | `<locale parity command>` | PROVEN |

Status vocabulary: NOT-PROVEN, RED, GREEN, TAMPER-PASSED, PROVEN, BLOCKED, WAIVED(user, date).
PROVEN requires RED evidence, GREEN evidence and TAMPER evidence, all three.

## Evidence log

### AC-2 RED (YYYY-MM-DD, commit abc1234)
```
$ pytest tests/api/test_budget.py -k committed
FAILED  tests/api/test_budget.py::test_resolves_committed_kind
  assert 0 == 42000
```

### AC-2 GREEN ...
### AC-2 TAMPER (committed impl, forced `return 0`, test failed as expected, restored, git status clean) ...

## Known risks / not covered
- ...
```

Keep `implementation-status.md` for the narrative (current phase, blockers, per-service
progress). The ledger is the gate; the status file is the story.

## Live infrastructure safety

Never write directly to shared dev/test/prod infrastructure: database documents and rows,
cache keys, cluster resources, identity-provider state, broker state, third-party accounts.
This holds even when the fix is one record, carefully verified, trivially reversible, and even
when it is the only thing standing between you and a green verification run.

When verification uncovers a real data or environment gap, stop and report it: what is wrong,
the exact change you would make, and ask. Code goes through branches, PRs and review; live
shared state has no such safety net, so it needs a human every time, not only when you are
unsure.

When briefing any subagent or helper session for testing or debugging, state this boundary in
its prompt. When one reports back, check whether it touched anything beyond git and CI before
you believe the report.

## Escalation (stop and ask, do not improvise)

- Any write to shared dev/test/prod infrastructure.
- ACs missing, ambiguous or mutually contradictory.
- Breaking change to a public API, event contract, DTO or stored schema.
- You cannot get a test to RED, or cannot run the suite at all.
- Scope grows past the task. Do not quietly widen it and do not quietly narrow it.
- Architecture decisions beyond the task's brief.

**When the blocker is external, not yours.** Some blockers only a third party can clear: data
someone else owns, an editorial or brand decision, content another person must write, external
access, or a product choice that is not yours. These are not yours to invent, and they do not
get buried in the ledger as a "known risk". Capture each as a tracked request: a plain-language
brief in the task dir (`<task dir>/external-request-<topic>.md` — what is needed, why, the exact
items, how they action it, how it comes back), plus a row in `<task root>/_EXTERNAL-REQUESTS.md`
tagged with the channel it goes out on. Mark the blocked AC
`BLOCKED (external, see _EXTERNAL-REQUESTS.md)` in the ledger, never `WAIVED`. A task blocked
only on someone else's answer stays open with a visible, routed request — not a silent TODO that
gets rediscovered three sessions later.

## Closing the loop (every task, PASS or abandoned)

A task that taught you nothing reusable was either trivial or unexamined. Before you report,
spend two minutes on the feedback the next task will read:

1. **Run `vince-learn`.** It turns this task's review findings into project config: a recurring
   miss becomes a `known_traps` line, a whole class of miss becomes a `dod_extras` gate, and a
   correction the user made becomes a lesson. That is the mechanism by which reviews here get
   sharper instead of repeating.
2. **Append one metrics line** to `.vince/metrics.jsonl` — one JSON object, no prose:
   ```json
   {"task":"<id>","date":"<YYYY-MM-DD>","tier":"T2","rounds":2,"acs":4,"wire_proofs":1,
    "findings":{"critical":2,"medium":1,"minor":3},"caught_by":["mutation","locale-parity"],
    "verdict":"PASS"}
   ```
   It costs one line and it is what lets `vince-learn` say "mutation testing catches most of the
   CRITICALs in this repo" instead of guessing.
3. **If the profile needed repairing mid-task** (see *Self-healing*), confirm the correction is
   recorded before you close out.

## Reference

- `reference/dod-gates.md` — the definition-of-done gate catalog with a verify command per gate.
- `.vince/profile.md` — this project's commands, conventions, rigs and extra gates.
- `.vince/lessons.md` — what previous reviews caught here. Read before designing.
- `vince-review` — the adversary. It is trying to fail you. Write for that reader.
- `vince-learn` — the feedback loop. Run it at PASS.
- `vince-doctor` — run it when anything about the setup smells wrong.
