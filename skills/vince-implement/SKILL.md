---
name: vince-implement
description: Execute repository features, fixes, and refactors with contract confirmation, test-first RED/GREEN/TAMPER evidence, end-to-end proof, and fresh Vince review. Use for any request that changes code or shipped behavior.
---

# Vince — Implement

End user-facing updates with three short lines: `Result:`, `Problem:` (omit when none), and `Next:`. Keep detailed evidence in task artifacts, not chat.

An implementation is failing until reproducible evidence proves otherwise.

## Core rules

1. No implementation before a test fails for the expected reason.
2. No completion claim before `vince-review` writes a PASS verdict.
3. No claim such as “verified” or “tests pass” without the command and observed result.
4. Never weaken RED, GREEN, TAMPER, regression, wire proof, or independent review to save tokens.
5. Never write to shared dev, test, or production infrastructure without explicit authority.

Conversation is direct and plain. Artifacts remain professional. Load `reference/voice.md` only
when tone needs clarification or a user-facing report is difficult to phrase.
Load `reference/token-discipline.md` only at a checkpoint with context pressure, repeated reads, large
outputs, or a configured compact/clear policy. The compact efficiency rules are: read ranges, not
whole files; bound output; prefer deterministic scripts; use one fresh reviewer; keep the ledger
current.

## Intake and routing

Invoke `vince-intake` first. Continue only on `READY`; for an ad-hoc request, the user must confirm
the restated contract. Do not continue on `CLARIFY` or `BOUNCE`.

Invoke `vince-route` after intake is `READY`, before implementation planning, and at boundaries
between mechanical work, implementation, high-risk judgment, and review. Use the resolver’s exact
profile mapping. `ASK` stops work. A `SWITCH` model switch is a recommendation unless the harness
confirms it.

## Tier

| Tier | Applies to | Evidence shape |
|------|------------|----------------|
| T1 | Non-behavioral copy, formatting, or dependency-free configuration | Ledger stub, baseline, proof, and five-point self-review |
| T2 | Ordinary behavior, fixes, features, and refactors | Full workflow and fresh review |
| T3 | Multiple repos, public contracts, auth/isolation, migrations, or concurrency | Full workflow, confirmed plan, and two review passes after remediation |

Take the highest applicable tier. Never downgrade without the user. Anything user-observable is
at least T2.

For T1, perform and record all five checks explicitly:

1. The diff contains only the intended change.
2. The suite is no worse than baseline.
3. Nothing user-observable changed.
4. No secret, debug artifact, or stray file is present.
5. The commit message and version change follow the profile.

## Phase 0 — Contract extraction

Resolve the profile and task paths; never assume `.vince/` is inside the repository:

```bash
python <toolkit>/scripts/install.py where --repo <repo>
```

If no profile exists, invoke `vince-setup` before continuing. Read the resolved profile and
lessons. Create the task directory and copy `templates/verification-ledger.template.md`. Record
the verbatim contract, one acceptance criterion per row, its proof level, tier, routing decision,
and session resources. No acceptance criteria, contradictory criteria, or missing authority is a
STOP.

Load `reference/contract-and-recon.md` now. It defines contract sources, profile inheritance,
proof levels, memory checks, and the required ledger fields.

## Phase 1 — Recon and baseline

Work in a dedicated worktree from the verified integration branch. Record it immediately. Inspect
only the owning code and relevant project instructions. Run the profile’s exact test command before
editing and record pass/fail/skip counts per repository. A suite that cannot run is a STOP.

Follow the recon and first-touch profile-promotion procedure in
`reference/contract-and-recon.md`.

## Phase 2 — Plan and confirm

Map each criterion to its test, changed files, and proof level. T3 plans require explicit user
confirmation. T2 plans may proceed when the confirmed contract and repository conventions settle
the implementation choices.

## Phase 3 — RED / GREEN / TAMPER / SUITE

For each criterion, in order:

1. **RED:** add the test and observe the expected failure.
2. **GREEN:** make the smallest implementation and observe the pass.
3. **TAMPER:** preserve the green implementation, deliberately break it, prove the test notices,
   restore it, and prove green again.
4. **SUITE:** run the full suite and compare it with baseline; no new failure or skip may pass.

Never edit, skip, quarantine, or delete a test merely to reach green. Never mock the behavior being
proved. Load `reference/tdd-and-wire-proof.md` before the first RED; it contains mutation safety,
restore rules, forbidden shortcuts, and evidence requirements.

## Phase 4 — End-to-end wire proof

Prove the headline behavior through the real user-facing interface. Unit-only evidence cannot
prove observable behavior. Use the profile’s rig and reach `E2E-WIRE` for at least one criterion.
If required infrastructure, credentials, or data is missing, record BLOCKED and stop rather than
inventing a substitute. Follow `reference/tdd-and-wire-proof.md`.

## Checkpoints

At every phase boundary, update statuses, evidence, the Resume block, and Session resources. Run:

```bash
python <toolkit>/scripts/resume.py --task <task-dir> --check
```

Only suggest `/compact` or `/clear` when the profile requests it and the command reports
`SAFE TO CLEAR`.

## Phase 5 — Definition of done

Load `reference/dod-gates.md`. Mark every applicable catalog and profile `dod_extras` gate PASS
with evidence, FAIL, or N/A with a reason. A checked box without a command is FAIL.

## Phase 6 — Self-attack

Name the three likeliest production failures and test them. Fix confirmed failures. Record risks
that cannot be exercised; do not silently downgrade them.

## Phase 7 — Commit, document, and review

Before the first commit and final cleanup, load `reference/hygiene.md`. Stage named files only,
never broad globs; keep the suite green; follow the profile’s version rule; record and remove every
resource started by the task.

Run the deterministic check:

```bash
python <toolkit>/scripts/check.py --repo <worktree> --base <integration-ref>
```

Create `completion-documentation.md`, then hand off to `vince-review` in a fresh, write-capable
context. The prompt contains only the task ID, repo/branch, profile, ledger and task paths, reviewer
model/role mapping, Pass 0 instruction, and read-only live-infrastructure boundary. Never advocate
for the implementation or paste ledger conclusions into the prompt.

Load `reference/completion-and-review.md` before documentation or handoff. It defines completion
documentation, reviewer isolation, verdict persistence, remediation routing, release/version rules,
metrics, learning, and cleanup.

PASS closes the task only after the ledger points at `review-verdict.md`, `vince-learn` runs,
metrics are appended, any configured docs are published, and session resources are removed. FAIL
loads `reference/remediation.md`, reproduces findings, fixes root causes, and re-proves affected
criteria before a fresh re-review. Repeated failure of the same cause is a STOP.

## Live infrastructure and escalation

Read-only inspection of shared systems is allowed. Writes to shared databases, caches, clusters,
brokers, identity systems, third-party accounts, or deployments require explicit human authority.
Also stop for ambiguous criteria, public-contract expansion, an impossible RED, an unusable suite,
ownership uncertainty, or scope beyond the confirmed contract.
