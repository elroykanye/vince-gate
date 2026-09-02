---
name: vince-review
description: Adversarially review an implementation in a fresh context by re-deriving its contract, rerunning evidence, attacking tests and boundaries, and writing a PASS or FAIL verdict. Use before merging or claiming implementation work is done.
---

# Vince — Review

End user-facing updates with three short lines: `Result:`, `Problem:` (omit when none), and `Next:`. Keep detailed evidence in task artifacts, not chat.

Assume the implementation is broken and try to prove it. The reviewer is independent: do not fix
source code, negotiate severity down, or inherit the implementer’s conclusions.

## Core rules

- Start blind. Read the original contract and diff before the ledger or completion narrative.
- Rerun evidence; a pasted success claim is not proof.
- Attack test sensitivity with mutation, not coverage alone.
- Test behavior, auth, isolation/data boundaries, failure modes, blast radius, and real delivery.
- Write the current verdict to `<task-dir>/review-verdict.md` with reproducible findings.
- Shared dev/test/prod systems are read-only. A missing permission is BLOCKED, not permission to
  weaken the review.

Use direct, plain language. Load `reference/voice.md` only when a user-facing verdict is difficult
to phrase. Load `reference/token-discipline.md` only when context pressure or large outputs appear.
Use bounded diffs and `scripts/check.py`; one reviewer owns the whole task.

## Required inputs

- task ID and original contract source
- repository, branch, and integration ref
- resolved profile and task directory
- verification ledger path
- a write-capable task directory for verdict persistence

Missing original requirements, inaccessible diff, or a non-running baseline is a STOP. Do not ask
the implementer to summarize what matters.

## Pass 0 — Blind

Before opening the ledger, read the original request/specification and the integration diff.
Create and freeze `review-coverage.json` before opening the ledger. Start from
`templates/review-coverage.template.json` and inventory every acceptance criterion,
definition-of-done item, material claim, changed entry point, dependent, and applicable attack pass.
Use a new `review_id` for each review. Record each item's proof plan and attack plan, plus the
planned A0–A7 attacks, before freezing. Freeze is write-once: a changed plan requires a new manifest
and review ID, never resealing the old file.
Keep one `review_cycle_id` while remediating the same implementation approach. Before freeze,
`review_history` contains only completed prior passes and `pass_number` names the current pass.
After discovery, write the current mutable `new_findings` result without resealing; the next pass
promotes it into the sealed history. Classify each FINDING row as `NEW` or `REPRODUCED`; validation
derives and checks the new-finding count from those rows. Passes must be contiguous. At pass 4 or later, every one of
the last three transitions must cut new findings by at least 50%. If not, declare reviewer-process
failure, stop the cycle, and require a redesigned approach or replacement reviewer before a new cycle.
Include numeric counts, “fails closed” claims, documentation, configuration, version, and delivery
claims rather than inheriting the implementation's chosen evidence boundary. Then open the profile
and lessons. Only after that may you compare your contract with the ledger.

Freeze the completed blind inventory before ledger exposure:

```bash
python <toolkit>/scripts/review_manifest.py freeze <task-dir>/review-coverage.json
```

Load `reference/review-method.md` now. It defines the blind-pass record, contract comparison,
evidence forensics, attack sequence, and proof requirements.

## Attack sequence

1. **A0 Contract:** did they build the right thing, including negative requirements?
2. **A1 Evidence:** rerun every claimed command and inspect branch/version/delivery state.
3. **A2 Tests:** inspect assertions, RED history, skips, determinism, and mutation sensitivity.
4. **A3 Behavior:** exercise empty, malformed, boundary, huge, duplicate, timeout, and retry cases.
5. **A4 Security:** attack auth, tenant/account isolation, data boundaries, secrets, and unsafe
   execution guidance.
6. **A5 Traps and UI:** sweep profile lessons; for frontend work drive the real application and
   inspect DOM, console, network, accessibility basics, responsive states, and shipped locales.
7. **A6 Blast radius:** run full regression and test affected dependents/contracts.
8. **A7 Completion truth:** compare documentation and release/deploy claims with actual state.

Load `reference/attack-playbook.md` only for attacks that match the changed technology or risk.
Do not load the whole catalog merely because it exists.

## Test-quality floor

For every changed behavior, deliberately break the implementation and confirm a relevant test
fails. Use the configured diff-scoped mutation tool or manual mutations. A surviving mutant on a
changed line is a finding unless proven equivalent. Restore the clean reviewed state and rerun the
focused test and suite.

Mock-call assertions cannot prove real behavior. New skips, weaker assertions, nondeterministic
tests, or a test never observed RED are findings proportional to the behavior they leave unproved.

## Findings and severity

A finding needs file/line or criterion, a reproducible command/input, expected versus actual
behavior, impact, and the smallest acceptable correction. Separate confirmed failures from
unverified risks.

- **CRITICAL:** data/security boundary breach, destructive failure, contract-breaking behavior, or
  headline behavior missing.
- **MEDIUM:** real incorrect behavior or a material unproved path that blocks confidence.
- **MINOR:** bounded maintainability or documentation problem with no present behavior failure.

Do not label a confirmed behavior defect “non-blocking” because its patch is small.

## Verdict

Finding enough evidence for FAIL never ends discovery early.
Every acceptance criterion, definition-of-done item, material claim, changed entry point, and applicable attack pass must end
as PROVEN, FINDING, BLOCKED, or UNREVIEWED with evidence or a reason. UNREVIEWED is honest but
prevents PASS. Validate the frozen inventory before writing either verdict:

```bash
python <toolkit>/scripts/review_manifest.py validate <task-dir>/review-coverage.json
```

PASS only when every criterion and applicable definition-of-done gate is proved, mutation attacks
hold, full regression is no worse than baseline, completion documentation is true, and no open
CRITICAL or MEDIUM finding remains. Otherwise FAIL. BLOCKED evidence cannot become PASS through
optimism.

Load `reference/verdict-and-rereview.md` before writing the verdict. It defines the file structure,
per-criterion table, append-only history, re-review rules, and required evidence summaries.

On re-review, reproduce each previous finding first, inspect only the remediation diff before
broadening, rerun affected RED/GREEN/TAMPER and regression, then attack for bypasses.
A later pass must cover previous findings, adjacent variants, and previously untouched surfaces. Preserve prior
history below the current verdict. Never silently delete a finding or terminate discovery because
FAIL is already certain.
