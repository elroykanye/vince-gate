---
name: vince-implement
description: Mandatory execution gate for any implementation task in any repo - features, bugfixes, refactors, multi-service or shared-library changes, ticketed or not. Drives the task end to end with test-first TDD, proves every acceptance criterion and definition-of-done item with reproducible evidence, and hands off to vince-review before anything may be called done. Triggers on "implement", "fix", "build", "work on", "take this task", "finish this", "is this done".
---

# Vince — Implement


## Voice

Read `reference/voice.md` and talk that way: friendly and dry, brutally honest about facts, and
never assuming the reader knows the jargon — keep the precise term, add the plain-English
translation. Jokes never carry information, and they switch off entirely for anything
destructive, any security or data finding, and any time you were wrong.
Progress notes and explanations are the conversation; the ledger is an artifact. Ledgers, commit messages and completion docs stay plain and professional — someone reads those later without the context.


Also read `reference/token-discipline.md`. Rigour is not negotiable; what it costs is. Read
narrowly, bound long commands, run `scripts/check.py` instead of ten shell commands, spawn a
subagent only when a fresh context is the point, and lean on the ledger so you can reset context
rather than carrying it.

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

## Intake gate (before Phase 0)

Invoke `vince-intake` on the incoming implementation request before extracting a contract. Continue
only when its result is `READY` and, for an ad-hoc chat request, the user has confirmed the restated
contract. Do not continue on `CLARIFY` or `BOUNCE`: clarification remains a conversation, and a
bounced request starts no implementation task or ledger.

## Routing gate (before planning and at phase boundaries)

Invoke `vince-route` after intake is `READY`, before implementation planning, and again when moving
between mechanical work, implementation, high-risk judgement, and review. Record its compact route
decision in the ledger. If it returns `SWITCH`, recommend the exact model switch to the user and
continue only within the current harness's authority; never claim the switch happened unless the
harness confirms it. If it returns `ASK`, stop until the profile mapping is repaired or the user
chooses. Routing may reduce model or agent cost, but it may not weaken any proof gate.

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

1. **Load the profile(s) and the lessons.** `.vince/profile.md` names this project's tracker,
   branch model, test commands, isolation key, locales, versioning rule and wire-proof rigs;
   `.vince/lessons.md` holds what previous reviews caught. Every project-specific decision in
   this skill reads from them. **Neither exists? Run `vince-setup` first** — one pass, then
   continue. Never guess at the test command or the branch model.

   **Resolve the paths, do not assume them.** Vince keeps per-repo config *outside* work repos
   by default, so `.vince/` may not be in the repo at all:

   ```bash
   python <toolkit>/scripts/install.py where --repo <repo>
   ```

   It prints the repo key, the config mode, and the resolved profile / lessons / metrics / task
   root. Use exactly those paths. Deriving your own is how one repo ends up with config in two
   places — and the key is remote-derived, so a task worktree resolves to its parent repo's
   config rather than a fresh empty one.

   **In a workspace with many repos there are two profiles**, and both apply:

   - `<workspace>/.vince/profile.md` — the hub: branch model, tracker, isolation key, estate
     gates and traps, and *unverified per-stack defaults*.
   - the resolved repo profile — this repo: verified commands and its observed baseline. It
     lives in the store (`~/.vince/repos/<key>/profile.md`) unless the repo carries its own
     `.vince/`.

   Merge them: scalars in the repo profile override the hub; `dod_extras` and `known_traps` are
   **additive and the hub's are not removable**; lessons from both levels are read. And the rule
   that matters most:

   > **A value inherited from the hub is `(inferred, unverified)` no matter how confident it
   > looks.** A hub cannot run a hundred suites, so nothing in it was ever executed. Treat every
   > inherited command as a hypothesis you are about to test, not as a fact.

   Read the lessons *before* you design, not after you are reviewed: a repeat of a recorded
   lesson is the cheapest FAIL there is, and the reviewer reads the same files looking for
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

1. Identify the owning repo — in a hub, via the profile's repo map rather than by guessing at
   names. In a polyrepo, write down the dependency order: shared lib, then service, then
   consumer, then frontend. **A multi-repo task needs a baseline per repo**, not one for the
   task; a suite you never ran in repo B cannot tell you whether you broke repo B.
2. Navigate with symbol tools where the language and harness have them (an LSP, Serena's
   `find_symbol` / `find_referencing_symbols`, your editor's index), not blind grep.
3. Read the repo's own `CLAUDE.md`/`AGENTS.md` and load only the docs your scope touches.
4. Work in a **dedicated worktree** off the profile's integration branch — e.g.
   `git -C <repo> worktree add ../<repo>-<task-id>-wt -b <branch> origin/<integration>` —
   never the repo's shared checkout (other live sessions may be in it). Record the worktree
   path on the ledger header. Never branch from a stale local default branch. Tear it down
   tear it down when done (`reference/hygiene.md`).
5. **Establish the test baseline before you change anything.** Run the profile's suite
   command, and record pass/fail/skip counts in the ledger. Without a baseline you cannot
   tell your new red from an inherited red, and neither can the reviewer. Record the count
   of existing skipped/quarantined tests too.

6. **First touch in this repo? Promote what you inherited.** If the commands came from a hub
   profile and this repo has none of its own, you are the one who turns hypotheses into facts —
   and it costs almost nothing, because you were running them anyway:

   - Run each inherited command you need. Watch it work.
   - Write the **resolved** repo profile (`install.py where`) containing **only what you verified
     plus what differs** — the commands that worked, the baseline you just observed and the
     commit it was taken on, this repo's locales, its mutation tool, its rigs. Do not copy the
     hub file; two copies of the same fact is two places to drift.
   - **This does not write anything into the repo** unless the repo already carries its own
     `.vince/`. Work repos stay clean: no untracked directory, nothing to gitignore, nothing to
     commit by accident. If you believe this repo *should* carry its own config — you own it and
     the team should share the profile — that is the user's call to make, not yours.
   - An inherited command that does not work is not a blocker, it is *Self-healing*: re-derive
     once, verify, record it in the **repo** profile with a *Corrections* line, and tell the user
     the hub default was wrong for this repo — that is a fix the whole estate benefits from.
   - Cannot determine something (no rig, no credentials)? `unknown — <what you tried>` or
     `blocked — <what is needed>`. Never a plausible-looking guess.

   After this, the repo is self-describing and the hub is back to being defaults. Skipping it
   means the next task re-runs the same discovery and the unverified values stay unverified
   forever.

STOP conditions in this phase: the suite does not run at all; the repo is not the owner;
the change requires a write to shared/live infrastructure. Report, ask, wait.

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
3. **TAMPER.** **Commit the green implementation first.** Then break the implementation
   deliberately and confirm the test notices. This is what catches tests that assert nothing,
   and it is not optional: coverage is a near-worthless proxy for fault detection — suites at
   100% coverage routinely kill only single-digit percentages of mutants.

   **Use the project's mutation tool if the profile's `mutation` row names one** (Stryker,
   mutmut, PIT, go-mutesting, cargo-mutants…), scoped to the diff — they all support
   incremental or changed-file runs, which is what makes this affordable per task. Then treat
   the output as work, not as a score: **every mutant that survives on a line you changed is a
   missing assertion.** Kill it with a test, or write down in the ledger why it is not worth
   killing. Feeding surviving mutants back into the tests is the whole difference between a
   suite that looks tested and one that is, and the reviewer re-runs the same tool.

   No tool for this stack? By hand, one mutation at a time per AC: flip the condition, return
   the wrong constant, empty the collection, drop the isolation-key filter.

   Either way: restore with `git checkout -- <file>`, confirm `git status` is clean, and log the
   result. Never commit or push a tamper mutation.

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

## Checkpoints (between every phase)

At each phase boundary — and whenever the pressure signals in `reference/token-discipline.md`
fire — bring the ledger current, update its **Resume** block (current phase, single next action,
anything in flight), and verify it stands on its own:

```bash
python <toolkit>/scripts/resume.py --task <task dir> --check
```

`SAFE TO CLEAR` means a fresh session could continue from the ledger alone. `NOT SAFE TO CLEAR`
names what is missing — fix it now, while you still remember it.

If the profile sets `checkpoints: suggest` or `insist`, offer the user a `/compact` or `/clear`
at the safe ones. **You cannot run it yourself**; it is theirs to type, and a suggestion is not
an action. Never offer it when the check has not passed — a reset on an incomplete ledger loses
work, which is the opposite of the point.

## Phase 5 — Definition-of-done gates

Walk `reference/dod-gates.md`, plus any extra gates the profile's `dod_extras` adds. Every
gate is PASS with evidence, FAIL, or N/A **with a written reason**. A ticked box with no
command behind it counts as FAIL. Data isolation, authorization on new entry points, locale
coverage, no debug statements, health/metrics, shared-library version bumps and dependent
updates are the ones that historically slip.

## Phase 6 — Self-attack

Before handing off, spend real effort trying to break your own work. Write down the three
most likely ways this fails in production, then actually test those three. Common starting
points: empty and huge datasets, a second tenant/account, a missing optional field, a
timeout, a duplicate event, a locale that is not your default.

Anything you find here, you fix here. Anything you suspect but cannot test goes in the ledger
as a known risk, visibly, not silently.

## Commit and workspace hygiene — the short version

Full detail in `reference/hygiene.md`; read it before your first commit and before you report
done. The rules that get violated most, inline because they are cheap to remember:

- **Stage per file.** Never `git add .`/`-A`/`commit -a` — that is how `.serena/`, `.env` and
  scratch files enter history.
- **No AI or bot attribution trailers** in commits or PR bodies, unless the profile opts in.
- **Never commit on the integration branch, never commit with a red suite.**
- **Version bump = exactly one increment above the integration branch's current value**, read
  after merging it, not from your branch's base.
- **Record every worktree and long-running process in the ledger's Session resources block as you
  create it**, and tear them all down before reporting done. A crashed session never reaches the
  end, which is exactly why the record is written at the start.

`python <toolkit>/scripts/check.py --repo <repo>` catches the mechanical half of this — stray
files, trailers, over-long subjects, new skips, debug statements, possible secrets, whole-file
rewrites — in one run. Do that before the handoff rather than making the reviewer find it.

## Phase 7 — Mandatory adversarial review

**First, write or update the completion documentation locally** — `vince-document` produces
`completion-documentation.md` in the task dir — cross-checked against the integration branch
and what is actually deployed, not local notes. Do this *before* the spawn, not after: the
reviewer verifies the completion doc against shipped reality (its A7) and will not issue a
clean PASS without a current one. Hold any external publishing until the verdict is PASS.

**Use a different model for the review if you can.** A fresh context breaks the correlation
introduced while generating — the reasoning trace, the local scaffolding, the sunk-cost pull of
your own plan. It does **not** break the correlation baked into the model's own parameters: the
blind spot that made you write the bug is the blind spot that makes you miss it. Context
separation plus model diversity is measurably stronger than either alone. If the profile names a
`reviewer_model`, use it; otherwise prefer a different model, ideally a different vendor, and
record which model reviewed in the verdict. Same model is acceptable — it is still far better
than same context — but say so.

Hand off to `vince-review` in a **fresh context that can write files** — never inline in your
own. How you get that depends on the harness, in this order of preference:

1. **A subagent**, if the harness spawns them. Pick the **narrowest agent type that still has
   `Write`/`Edit` and can run commands** — a scoped reviewer type if the harness has one, and
   `general-purpose` only as the fallback, because a broad type carries a larger prompt for
   capabilities the review never uses. Best option overall: genuinely fresh context, same session.

   **Run `scripts/check.py` yourself before spawning.** It catches the mechanical findings — stray
   files, attribution trailers, new skips, debug statements, possible secrets, whole-file rewrites
   — in one command. Fixing those first means the reviewer's context goes to judgement instead of
   to a list of things you could have caught for free.
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
  a fresh context; if it is not told to invoke it, it reviews without the method);
- an instruction to **start with the skill's Pass 0 — read the diff and the original contract
  before opening the ledger**;
- the **task ID**, the **repo(s) and branch**, the **verification-ledger path**, the **task
  directory**, and the **profile path**;
- the **model to review with**, if the profile names `reviewer_model` — you cannot set it
  yourself, so say it plainly and let whoever spawns the subagent honour it;
- the live-infrastructure boundary (read-only on every repo, DB, cache and cluster).

Nothing persuasive: no summary of your work, no severity opinions, no "already verified" or
"pre-existing" claims, and **no pasted ledger content** — give the path and let the reviewer
open it when the method says to. Steering the reviewer is the one thing that defeats the point,
and it is not a small effect: reviewers handed text asserting the code is sound miss most of
what they would otherwise catch, and autonomous agents are more susceptible to it than people
are. A prompt that reads like advocacy has already cost you the review you are about to pay for.

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
  started** (`reference/hygiene.md`), then report to the user with the ledger summary and the
  reviewer verdict attached.
- You genuinely disagree with a finding: surface the disagreement to the user with both
  arguments. Never overrule the reviewer silently.

## The ledger

`verification-ledger.md` in the task dir resolved in Phase 0. Copy
`templates/verification-ledger.template.md` from the toolkit (its path is the `source` field in
`.vince/install.json`) rather than reproducing the format from memory — it carries the Session
resources block, the per-repo baseline table and the status vocabulary.

Status vocabulary: `NOT-PROVEN`, `RED`, `GREEN`, `TAMPER-PASSED`, `PROVEN`, `BLOCKED`,
`WAIVED(user, date)`. **`PROVEN` requires RED, GREEN and TAMPER evidence, all three.** Keep
`implementation-status.md` for the narrative; the ledger is the gate.

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

## Phase 8 — Remediation (when the verdict is FAIL)

`reference/remediation.md` has the protocol: reproduce before editing, fix by root cause worst
first, re-prove with RED/GREEN/TAMPER, full regression before re-spawning, and the convergence
guard that stops a thrashing loop. Load it when you get a FAIL.

The two rules you must not need the file for: **fix root causes, not findings** (several findings
usually share one cause), and **thrash — the same cause failing twice, or an open-CRITICAL count
that does not drop — is an immediate stop and escalation**, never a third attempt.

## Self-healing — when the profile is wrong

`reference/remediation.md` also covers this. In short: run the recorded command, and if it fails,
re-derive it **once**, verify the replacement, and record the fix under the profile's
*Corrections*. Two wrong fields in one task means the profile needs a full `vince-setup` refresh,
not more patching. Never silently substitute a different command — every later comparison,
including the reviewer's, depends on it being the one in the profile.

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
    "verdict":"PASS","tokens":185000}
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
