---
name: vince-review
description: Review a task against its stated requirements and relevant tests, then write PASS or FAIL and stop. Use to check whether requested work is done, not for a general audit.
---

# Vince — Review

Before the final user-facing response, apply `reference/brief.md`.

The task's stated requirements are the verdict boundary.
**All stated requirements are met and their relevant tests pass → PASS.**
An unmet requirement or failing/missing proof of that requirement → FAIL.
Anything else is out of scope and cannot prevent PASS.

## Review once

1. Read the original task and its explicitly agreed acceptance criteria. Use those points as
   the checklist. Do not add acceptance criteria from personal preferences, project lessons,
   attack catalogs, or a wish for more comprehensive software.
2. Inspect the relevant change and tests against each point. Check that the implementation
   actually does what the point requires and that its tests exercise the required behavior.
   Green tests that do not prove a requirement are not proof that it is met.
3. Run the relevant tests on the reviewed revision, or verify recorded execution when rerunning
   is unavailable. Record the commands, results, and any requirement that remains unverified.
   Do not accept invented, stale, skipped, or weakened tests as proof of required behavior.
4. Write the per-requirement result and overall verdict to `<task-dir>/review-verdict.md`.
   Stop after writing the verdict. There is no automatic remediation or re-review.

Load `reference/review-method.md` for test/evidence checks and
`reference/verdict-and-rereview.md` when writing the result.

## Keep the boundary

- Every blocking finding must identify the exact stated requirement, the observed violation
  or missing proof, and how to reproduce it. Do not invent a finding quota or a default FAIL.
- Do not require a mutation campaign, RED history, full repository suite, security audit,
  adjacent-failure search, deployment, installation, or new documentation unless the task's
  stated requirements call for it. If TDD or regression preservation is explicitly required,
  check that requirement; do not turn it into an unlimited audit.
- No mandatory attack-category checklist, convergence percentage, cycle, or pass-count target.
  Do not invoke legacy forensic review-manifest machinery for an ordinary requirements review.
  Those tools apply only when explicitly requested as part of the task.
- Out-of-scope concerns may be noted separately, but must not become findings, a FAIL, extra
  work, or another review. Escalate a serious risk plainly without silently expanding the task.
- PASS is final for this review's stated scope and revision, not a claim of perfect software.
  A subsequent fix or review requires user direction; never start one yourself.
- Preserve earlier verdicts. This policy change does not retroactively pass historical work.
- Review independently: do not fix source or inherit the implementer's conclusions. Shared
  systems are read-only; running destructive tests requires explicit permission.
