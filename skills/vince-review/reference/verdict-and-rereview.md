# Verdict and stopping

Write `<task-dir>/review-verdict.md` with the newest result first:

```markdown
# Vince review — <task> — <date>

VERDICT: <PASS | FAIL>
Reviewed commit: `<revision>`

## Stated requirements
| Requirement | MET / NOT MET | Test or other proof and observed result |
|-------------|---------------|----------------------------------------|

## Unmet requirements
Only for FAIL: exact requirement, reproducible discrepancy or missing proof, and expected/actual result.

## Out-of-scope notes
Optional; these do not affect the verdict or authorize more work.

## Review history
Earlier verdicts, preserved without rewriting them.
```

All stated requirements are met and their relevant tests pass → PASS. Otherwise FAIL for the
specific unproved or unmet points. Do not fail a completed task for an optional suggestion,
attack category, process quota, or extra condition that was never a task requirement.

If a verification ledger exists, update the verification ledger's `Reviewer verdict` field
with the result and a pointer to `review-verdict.md`. This records the verdict; it does not add
acceptance criteria or change historical results. Extra metrics or learning tags are not PASS gates.

Write the verdict once and stop: no automatic remediation or re-review. On FAIL, return the unmet
points to the user. If the user later requests fixes or another review, keep the same stated
requirements unless the user changes them; do not broaden the review to find new work.
