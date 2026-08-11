# vince-gate

A **portable implementer-and-reviewer toolkit** for AI coding agents. Vince is not a knowledge
base and not a linter — it is a pair of opposed roles that together make "done" mean something:

- **`vince-implement`** drives a task end to end: contract first, test-first TDD, an evidence
  ledger, an end-to-end wire proof, definition-of-done gates, and a self-attack pass before it
  will hand off.
- **`vince-review`** is the adversary. It runs in a fresh context, assumes the work is broken,
  re-derives the contract from the original source, re-runs every claimed proof, mutation-tests
  the new tests to find dead ones, and defaults to **FAIL**.

The two rules that make the rest work: **nothing is done without a PASS verdict**, and **no claim
counts without the command and its output behind it**.

Spec-driven frameworks — OpenSpec, Spec Kit, Superpowers, BMAD, GSD — enforce *process*: phases,
gates, personas, the order you do things in. None of them verify that the work is what it claims
to be. vince-gate enforces *evidence*: a contract copied verbatim, tests proven able to fail,
mutants that must die, a wire proof over real transport, and a reviewer that starts from the diff
rather than from your summary. It composes with those frameworks rather than replacing them.

New here? **[INSTALL.md](INSTALL.md)** gets it running (paste one block into your agent), then
the **[user guide](USER-GUIDE.md)** covers using it.

## The skills

| Skill | Role |
|-------|------|
| `vince-setup` | Inspects a repo and writes `.vince/profile.md` — the one file that makes the rest project-specific. Run once per project. |
| `vince-implement` | The execution gate: tier the task → contract → recon → plan → RED/GREEN/TAMPER → wire proof → DoD gates → self-attack → mandatory review → bounded remediation. |
| `vince-review` | The adversarial reviewer: contract re-derivation, evidence forensics, mutation testing, behaviour and isolation attacks, live-browser verification, blast radius, verdict persisted with append-only history. |
| `vince-document` | Completion documentation in the task dir, validated against what actually shipped, published only after PASS. |
| `vince-doctor` | Self-healing: repairs a drifted install, validates the profile by *running* it, finds unreviewed work and leaked worktrees. |
| `vince-learn` | Self-improving: turns review findings into `known_traps`, `dod_extras` gates and lessons, so the next task is stopped at the gate rather than caught at review. |
| `vince-cleanup` | Recovers a workspace after a session ended without tearing down: leaked worktrees, processes holding directories open, stray output. Attributes before it touches anything. |
| `vince-update` | Moves an install to another release safely — reads the changelog between versions, refuses to trample in-place edits, and migrates `.vince` config so a new version's fields exist instead of silently defaulting. |

## Works with any harness

The skills are plain markdown; a **binding** renders them into the shape a runtime wants — a
directory per skill with YAML frontmatter for Claude Code, flat `.mdc` files for Cursor, TOML
commands for Gemini CLI, plain markdown plus an `AGENTS.md` pointer block for anything else.

```bash
python scripts/install.py bindings          # claude, cursor, windsurf, codex, gemini, generic
```

`claude` and `generic` are verified; the rest follow each runtime's documented convention and are
marked `unverified` until someone confirms them. Adding a runtime is a 12-line JSON file — see
[docs/harnesses.md](docs/harnesses.md).

## Project-agnostic by construction

Vince ships no assumptions about your stack. Everything project-specific — test commands,
integration branch, tracker, versioning rule, data isolation key, locales, wire-proof rigs, extra
DoD gates, known traps, tier overrides — lives in **`.vince/profile.md`**, written by
`vince-setup` and read by every other skill. Swap the profile and the same discipline applies to
a Go service, a React app, or a Python pipeline.

**Many repos under one hub?** Two profiles: an estate-level one for the repo map, stacks, branch
model, tracker and estate-wide gates, and a per-repo one for verified commands and baselines. The
invariant that keeps it honest is that a hub profile *cannot verify a command* — nobody runs a
hundred suites from a hub, so its per-stack values are unverified by construction and the first
task in a repo is what promotes them. See
[Many repos](USER-GUIDE.md#many-repos-workspace-profiles).

## Self-healing and self-improving

- **Healing.** A stale profile is worse than none, because it is trusted. When a recorded command
  fails mid-task, `vince-implement` re-derives it once, verifies the replacement, repairs the
  profile and records the correction — and stops if a second field is wrong, because that means a
  full refresh. `install.py doctor --fix` repairs the install layer; `vince-doctor` covers the
  profile, the work in flight and leaked worktrees.
- **Improving.** Every finding carries a `[caught: …]` tag. At PASS, `vince-learn` promotes
  patterns — not incidents — into project config: seen twice becomes a trap, detectable by command
  becomes a gate, a correction becomes a lesson. It reads `.vince/metrics.jsonl` to report which
  attacks actually earn their time in this codebase and whether rounds-to-PASS is falling.

## Built against the evidence

Three design rules exist because measurement says they matter, and the skills say why in-line:

- **The reviewer reads the diff before it reads your ledger.** Reviewers handed text asserting
  code is sound miss most of what they would otherwise catch, and autonomous agents are far more
  susceptible to that framing than people are. Pass 0 is blind by construction.
- **Mutants, not coverage.** Suites at 100% coverage routinely kill single-digit percentages of
  mutants. TAMPER uses the project's mutation tool diff-scoped where one exists, and surviving
  mutants on changed lines are work, not a score.
- **A different model reviews, where you can arrange it.** Fresh context breaks the correlation
  introduced while generating, but not the correlation baked into the model's parameters — the
  blind spot that wrote the bug is the blind spot that misses it.

And the honest limit: independent review measurably beats same-session review, most clearly on
critical errors, but it still finds a minority of defects. That is why the wire proof and the
mutation gate carry as much weight here as the review does — they do not depend on a model's
judgement at all.

## Install

**As a Claude Code plugin:**

```
/plugin marketplace add elroykanye/vince-gate
/plugin install vince-gate@vince-gate
```

**Any harness:** open [INSTALL.md](INSTALL.md) and paste the block into your coding agent — it
clones, detects your harness, installs, verifies and reports back.

Releases are git tags, so pinning a version is `git checkout v0.1.0` then reinstall — see
[Versions](INSTALL.md#versions).

By hand (location-independent; clone anywhere):

```bash
git clone https://github.com/elroykanye/vince-gate.git && cd vince-gate
python scripts/install.py install --scope user            # every project, no repo footprint
python scripts/install.py install --target /path/to/repo  # auto-detects the harnesses in use
python scripts/install.py status  --scope user
python scripts/install.py doctor  --target . --fix
```

Install checksums every file it writes, so `status`/`doctor` report drift and `install` refuses to
clobber anything edited in place without `--force`. Improved a skill at the target? Copy it back
into `skills/` and reinstall — the toolkit is the source of truth.

## Using it

```
1. /vince-setup          once per project (or when the build changes)
2. /vince-implement      for every task, before touching code
3. …it hands off to vince-review in a fresh context and will not report done without PASS
4. /vince-learn          at PASS — it gets sharper here, not just done
5. /vince-update         when a new release lands; it migrates your config, not just the files
```

`vince-implement` is a **gate, not a reference sheet**. Invoking it after the code is written
gets you a ledger written backwards from the implementation, which is exactly the rationalisation
the whole method exists to prevent.

Tiering keeps it survivable: **T1** trivial (nothing user-observable) gets a stub ledger and a
self-review, **T2** is the full sequence, **T3** (multi-repo, contracts, auth, migrations) adds
plan confirmation and a second review pass. The tier changes how much evidence, never whether
there is evidence.

## Layout

```
vince-gate/
  INSTALL.md                          paste-to-your-agent install guide
  USER-GUIDE.md                       start here
  skills/                             the eight skills (+ reference/ docs)
  bindings/*.json                     one per harness; no per-harness code
  hooks/                              opt-in enforcement (Claude Code Stop hook)
  templates/                          profile, ledger, verdict, lessons, completion doc
  scripts/install.py                  install / status / doctor / uninstall / list / bindings
  docs/                               methodology, skills, profile, harnesses, install
  .claude-plugin/                     plugin + marketplace manifests
  VERSION
```

Artifacts live in the project Vince is working on, never in the toolkit:

```
<project>/.vince/
  profile.md  lessons.md  metrics.jsonl  install.json
  tasks/active/<task-id>/    verification-ledger.md, implementation-status.md,
                             review-verdict.md, completion-documentation.md
  tasks/archive/<task-id>/
```

## Documentation

- [INSTALL.md](INSTALL.md) — getting it installed: blocks you can paste to an agent, and the manual equivalents.
- [CHANGELOG.md](CHANGELOG.md) — what changed per release, and how to upgrade, pin or roll back.
- [USER-GUIDE.md](USER-GUIDE.md) — first project, reading a verdict, troubleshooting, FAQ.
- [docs/methodology.md](docs/methodology.md) — why each rule exists and the failure mode it stops.
- [docs/skills.md](docs/skills.md) — every phase and attack pass.
- [docs/profile.md](docs/profile.md) — every profile field and who reads it.
- [docs/harnesses.md](docs/harnesses.md) — the binding model; adding a runtime.
- [docs/install.md](docs/install.md) — the installer CLI in full: every flag, the drift states, exit codes.

## License

MIT — see [LICENSE](LICENSE). Contributions welcome; if you verify a binding against a real
runtime, promote its `status` and say what you confirmed.
