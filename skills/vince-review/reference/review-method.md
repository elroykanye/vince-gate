# Requirements and tests

Start with the original task, not the implementer's claims. Make one checklist row per stated
requirement, including only definition-of-done conditions explicitly agreed for this task.
Do not add acceptance criteria during review. Anything else is out of scope.

For each row:

- Locate the implementation and relevant test or other appropriate proof.
- Confirm the assertion checks the required outcome, not merely that a mock was called or a
  command ran. A concrete counterexample matters only if it violates that stated requirement.
- Run the relevant test command for the reviewed revision. Read its actual outcome; distinguish
  assertion failures from environment/setup errors. A claimed pass without verifiable execution
  does not establish the requirement.
- Mark the requirement MET or NOT MET, citing the observed result. If required proof is unavailable,
  say exactly which point is unverified; do not replace it with an unrelated test.

Use task-specified test, TDD, integration, or regression requirements as written. Do not add an
exhaustive audit, mutation campaign, extra edge-case catalog, or full-suite rerun as a default gate.
An optional improvement is not a missing requirement.

All stated requirements are met and their relevant tests pass → PASS.
Otherwise FAIL, identifying only the unmet points or their missing/failing proof.
Stop after writing the verdict; no automatic remediation or re-review.
