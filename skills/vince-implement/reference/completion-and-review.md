# Completion and review

Load this reference before documentation, commit/release preparation, and reviewer handoff.

## Completion documentation

Write `completion-documentation.md` in the task directory before review. Cross-check it against the
integration diff and deployed state. Include contract, implementation, tests, wire proof, security,
deployment status, known limits, and reproducible commands. Publish externally only after PASS.

## Fresh review

Run `scripts/check.py` first. Spawn one fresh, write-capable reviewer using the exact profile model
and agent mapping. Its prompt must instruct `vince-review` and Pass 0, identify task ID, repo,
branch, ledger, task directory, and profile, and state that all shared infrastructure is read-only.
Do not include persuasive summaries, severity opinions, or pasted evidence conclusions.

The reviewer writes `<task-dir>/review-verdict.md`. On FAIL, load `reference/remediation.md`,
reproduce each finding before editing, fix root causes, repeat RED/GREEN/TAMPER and regression for
affected criteria, then request a fresh re-review. T3 receives a second review pass even after an
initial PASS. Repeating the same root-cause failure twice stops remediation for user direction.

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
