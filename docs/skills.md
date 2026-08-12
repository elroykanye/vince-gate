# Skill catalog

Eight skills, rendered into whatever shape your harness wants by `scripts/install.py` (see
[harnesses.md](harnesses.md)). They are designed to be invoked by name (`/vince-implement`) or to
auto-activate on their description triggers.

| Skill | When |
|-------|------|
| `vince-setup` | once per project, and after the build or conventions change |
| `vince-implement` | every implementation task, before code |
| `vince-review` | spawned by the implementer; usable standalone on any branch |
| `vince-document` | at completion, before publishing |
| `vince-doctor` | when anything about the setup smells wrong |
| `vince-learn` | after a PASS, and once over the history when adopting Vince |
| `vince-cleanup` | when a session left worktrees, processes or output behind |
| `vince-update` | when a new release lands, or to roll back to an older one |

## `vince-setup`

**Run once per project**, and again when the build or conventions change.

Inspects the repo and writes `.vince/profile.md`: commands (each one actually run), branch model,
tracker, versioning, isolation key, auth model, locales, wire-proof rigs, environments, memory
targets and known traps. Verifies its own output before finishing — re-runs the suite, resolves
the integration branch, checks every path it recorded.

Output: `.vince/profile.md`. See [profile.md](profile.md).

## `vince-implement`

**The gate.** Invoked *before* code is written, for any implementation task.

It classifies the task first — **T1** trivial (nothing user-observable: stub ledger, self-review),
**T2** standard (the full sequence), **T3** complex (2+ repos, contract/auth/migration/concurrency:
plus mandatory plan confirmation and a second reviewer pass). The tier changes how much evidence,
never whether there is evidence; the agent may move up on its own but only the user moves it down.

| Phase | What it does | Artifact |
|-------|--------------|----------|
| 0 | Contract extraction — profile loaded, task dir resolved, every AC/DoD item copied verbatim, proof level chosen per row | `verification-ledger.md` |
| 1 | Recon — owning repo, dependency order, dedicated worktree, **test baseline recorded** | ledger header |
| 2 | Plan — `AC → test → files → proof level`, confirmed by the user | plan |
| 3 | TDD loop — RED, GREEN, TAMPER, full SUITE, per AC | evidence log |
| 4 | Wire proof — the real path with real transport, per change type | ledger |
| 5 | DoD gates — the catalog plus the profile's `dod_extras` | ledger |
| 6 | Self-attack — the three most likely production failures, actually tested | ledger |
| 7 | Doc, then hand off to `vince-review` in a fresh context; PASS or go to 8 | `completion-documentation.md` |
| 8 | Remediation — root cause first, bounded rounds, convergence guard | `implementation-status.md` |
| close | `vince-learn` + one metrics line | `.vince/lessons.md`, `.vince/metrics.jsonl` |

Hard rules: no implementation before a failing test; no "done" without a PASS verdict; no
unproven claim in any report.

Reference: [`dod-gates.md`](../skills/vince-implement/reference/dod-gates.md).

## `vince-review`

**The adversary.** Runs in a **fresh, write-capable context** — never inline in the implementer's,
and on a **different model** where the profile's `reviewer_model` or the harness allows it. It
reads `.vince/lessons.md` first and attacks the recorded traps hardest, because a repeat is the
highest-probability finding there is.

Pass 0 comes before everything: the reviewer writes its findings from the diff and the original
contract alone, and only then opens the ledger. Reviewers handed a document asserting the work is
proven miss most of what they would otherwise catch, and the ledger is exactly such a document.
The verdict records how many findings came blind versus only after reading it — a review that
found nothing blind is a review that read the answer sheet.

| Pass | Attack |
|------|--------|
| **0** | **Blind** — findings derived from the diff and the original contract *before* the ledger, completion doc, commit messages or prior verdict are opened |
| A0 | Contract re-derivation from the original source; diff against the ledger |
| A1 | Evidence forensics — re-run every proof; git/commit/version/branch forensics |
| A2 | Test-quality — mutation (the project's tool, diff-scoped, where one exists), assertion audit, RED history, skip hunt, determinism, coverage of the real path |
| A3 | Behaviour — empty/huge/null/boundary/unicode/timezone/concurrency inputs |
| A4 | Isolation, auth and data boundaries |
| A5 | Trap sweep — generic playbook plus the profile's `known_traps` and `.vince/lessons.md` |
| A5b | Drive the real UI in a real browser — mandatory for frontend changes |
| A6 | Blast radius — references to every changed public symbol, contract compatibility |
| A7 | Completion documentation present, current and true |

Default verdict **FAIL**, with hard FAIL conditions listed in the skill. Output goes back to the
caller *and* is persisted to `<task dir>/review-verdict.md` with an append-only history, so the
FAIL → FAIL → PASS trail stays visible and the open-CRITICAL trend is readable. Each finding
carries a `[caught: …]` tag naming the attack that found it — that is what `vince-learn` reads.

Reference: [`attack-playbook.md`](../skills/vince-review/reference/attack-playbook.md).

## `vince-doctor`

Diagnoses and repairs a decayed setup. Three layers: the **install** (via
`install.py doctor --fix` — missing, drifted, stale and in-place-edited files, plus index
blocks), the **profile** (validated by running its commands, resolving its branch and checking
its paths, with every repair recorded under *Corrections*), and the **work in flight** (ledgers
never reviewed, stale `active/` dirs, leaked worktrees).

Two failing profile fields means a full `vince-setup` refresh rather than row-by-row patching.
In-place edits to installed skills are never discarded silently — they are an improvement that
did not make it home.

## `vince-learn`

The feedback loop. Converts a finished task's findings into configuration: a finding class seen
twice becomes a `known_traps` line, one a command can detect becomes a `dod_extras` gate, a user
correction becomes a lesson in `.vince/lessons.md`, a hard-won rig becomes a `wire_proofs` entry.
One-offs are deliberately *not* promoted — noise is what makes these files stop being read.

It also reads `.vince/metrics.jsonl` (one line per task, written at close) to report which
attacks earn their time in this codebase, whether rounds-to-PASS is trending down, and whether a
tier is being abused. Under about five tasks it says so rather than inventing a trend.

## `vince-cleanup`

Post-hoc recovery. `vince-implement` tells a session to sweep up after itself and `vince-doctor`
reports orphaned worktrees; this is for when the session that made the mess is gone — it crashed,
was interrupted, or predates the rule.

It is the only skill here that kills processes and deletes directories, so it is built to refuse:
inventory everything first, **attribute** each item (yours / unknown / someone else's) and act
only on the first bucket, never kill by process name, never `--force` past a dirty or unpushed
worktree, never `rm -rf` a worktree at all, and delete only output you can name the regenerating
command for. Unknown items are reported, not resolved.

It also owns the diagnosis nothing else did: **which process is holding a directory open** when a
remove fails — `handle.exe` / `Win32_Process` on Windows, `lsof`/`fuser` elsewhere — worked in
escalation order rather than reaching for force.

Attribution comes from the ledger's *Session resources* block, which `vince-implement` now writes
as it creates each worktree and background job. Without it, cleanup can only ask.

## `vince-update`

Moves an install between releases. The file half is `install.py`'s job; this skill owns the parts
that need judgement.

It compares installed / toolkit / available tags, reads `CHANGELOG.md` **between** the versions
and reports what actually changes, then runs a pre-flight that **stops** on three things rather
than working around them: uncommitted work in the toolkit clone, files edited in place at the
target (someone's improvement that never went home — copy it into the toolkit, do not `--force`
over it), and a task in flight (changing the skills mid-task changes the rules mid-task).

Then the part nothing else does: **config migration.** A release that adds a profile field does
not add it to existing profiles, so the new skills read a field that is not there and fall back
silently. This walks each intervening release's *Upgrade notes* and makes the sections exist —
running what is cheap and safe to run, and marking the rest `unknown — <tried>` or
`blocked — <what is needed>` rather than inventing values. It then names every field it left
open and what would resolve it.

Rollback is the same procedure with an older tag. Project artifacts are never touched: older
skills read newer profiles fine, so a rollback needs no migration and must not strip fields.

## `vince-document`

Writes `completion-documentation.md` in the task dir from the files it actually read, validates
every path and snippet against the branch, and publishes to the profile's `docs_destination` —
only after a PASS, and only with the user's confirmation.

## The handoff contract

The reviewer runs in a **fresh context that can write files**. In order of preference: a subagent
if the harness spawns them; otherwise a separate session; otherwise a context reset, noted in the
verdict as weaker isolation. Never "switching hats" in the same context — you cannot un-see your
own reasoning.

The prompt carries **only**:

1. an instruction to invoke the `vince-review` skill (the body does not auto-load into a fresh
   context — an agent not told to invoke it reviews blind);
2. the task ID, repo(s) and branch, ledger path, task directory, profile path;
3. the live-infrastructure boundary (read-only on every repo, DB, cache and cluster).

Nothing persuasive: no summary, no severity opinions, no "already verified". The reviewer must be
write-capable and must know the task dir, or it silently skips persisting the verdict.

## Shared reference content

`skills/_shared/*.md` is copied into every skill's `reference/` at install time — one source of
truth in the repo, present next to each skill at runtime. `voice.md` lives there. A file eight
skills each kept their own copy of would drift within a release.

`_shared` is not itself a skill (no `SKILL.md`), so it never appears in listings, and in flat
layouts it renders as `<skill>-voice.md` with links rewritten to match.

## Adding a skill to the toolkit

Create `skills/<name>/SKILL.md` with frontmatter (`name`, `description` — the description is what
drives auto-activation, so write the triggers into it), put anything long in
`skills/<name>/reference/`, bump `VERSION`, and reinstall. `install.py` picks up any directory
under `skills/` that contains a `SKILL.md`, renders it for every installed binding, and removes
files a previous install shipped that the new one does not.

Keep skill bodies harness-neutral: name the *capability* you need (a browser, a subagent, symbol
navigation) with examples, and let the runtime substitute. Anything project-specific belongs in
`.vince/profile.md`, not in a skill.
