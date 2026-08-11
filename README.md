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

## Install

**Fastest:** open [INSTALL.md](INSTALL.md) and paste the block into your coding agent — it
clones, detects your harness, installs, verifies and reports back.

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
  skills/                             the six skills (+ reference/ docs)
  bindings/*.json                     one per harness; no per-harness code
  templates/                          profile, ledger, verdict, lessons, completion doc
  scripts/install.py                  install / status / doctor / uninstall / list / bindings
  docs/                               methodology, skills, profile, harnesses, install
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
- [USER-GUIDE.md](USER-GUIDE.md) — first project, reading a verdict, troubleshooting, FAQ.
- [docs/methodology.md](docs/methodology.md) — why each rule exists and the failure mode it stops.
- [docs/skills.md](docs/skills.md) — every phase and attack pass.
- [docs/profile.md](docs/profile.md) — every profile field and who reads it.
- [docs/harnesses.md](docs/harnesses.md) — the binding model; adding a runtime.
- [docs/install.md](docs/install.md) — the installer CLI in full: every flag, the drift states, exit codes.

## License

MIT — see [LICENSE](LICENSE). Contributions welcome; if you verify a binding against a real
runtime, promote its `status` and say what you confirmed.
