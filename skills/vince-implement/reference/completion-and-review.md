# Completion and review

Load this reference before documentation, commit/release preparation, and reviewer handoff.

## Completion documentation

Write `completion-documentation.md` in the task directory before review. Cross-check it against the
integration diff and deployed state. Include contract, implementation, tests, wire proof, security,
deployment status, known limits, and reproducible commands. Publish externally only after PASS.

## Fresh review

Run `scripts/check.py` first. Spawn one fresh, write-capable reviewer using the exact profile model
and agent mapping. Its prompt must instruct `vince-review` against the stated requirements, identify task ID, repo,
branch, ledger, task directory, and profile, and state that all shared infrastructure is read-only.
Do not include persuasive summaries, severity opinions, or pasted evidence conclusions.

The reviewer writes `<task-dir>/review-verdict.md`. The first review is the task's default and only
automatic review. Its PASS condition is all stated requirements met and relevant tests passing;
do not introduce extra reviewer gates. On FAIL, stop automatic work, persist the verdict, and report it.
Fixes require user direction and end **fixed-but-unreviewed** after the affected requirements and
their relevant tests are re-proved. A further review requires a separate explicit user request;
do not create another pass, widen the scope, or enter a fix/review loop automatically.

## Release and closure

- Stage named files only; do not use broad add/commit flags.
- No attribution trailers unless the profile explicitly permits them.
- Apply the profile’s exact version rule from current integration state.
- Keep release metadata, changelog, manifest, and tag consistent.
- Run `vince-learn` after PASS and append one compact metrics JSON line.
- Publish configured documentation and verify the destination.
- Stop attributed processes and remove the task worktree only after clean, pushed or explicitly
  handed-off state is confirmed.
- Update the ledger’s Reviewer verdict and Resume block before reporting completion.
