# Remediation and self-healing

Read when a review returns FAIL or project instructions are stale.

## Remediation — only when the user requests fixes

FAIL ends the review: no automatic remediation or re-review.
When the user authorizes fixes, reproduce the unmet stated requirement, fix that behavior,
and rerun its relevant tests. Do not turn optional suggestions into new acceptance criteria.
Report what is fixed and stop. A further review is a separate user-directed action, not the
next automatic phase. It uses the same stated requirements unless the user changes them.

## Self-healing — when the profile is wrong

Profiles go stale: the test runner changes, a script is renamed, a branch is retired. A stale
profile is worse than none, because you trust it. So when anything you read from the profile
does not work, you repair it rather than working around it — **bounded**, and always recorded.

1. **Confirm it is the profile, not you.** Run the recorded command verbatim and read the
   actual error. A missing dependency is an environment problem; a renamed script is a profile
   problem.
2. **Re-derive it once.** Look at the manifest, the scripts block, CI config, and the last few
   commits that touched them. Run the candidate. If it works, you have the replacement.
3. **Repair and stamp.** Update that row in `.vince/profile.md`, and add a line under its
   *Corrections* section: date, what was wrong, what it is now, what proved it. The next
   session inherits the fix instead of rediscovering it.
4. **Two failures is a stop.** If the re-derived command also fails, or a second profile field
   turns out wrong in the same task, stop repairing and report: the profile needs a full
   `vince-setup` refresh, and that is not a thing to do in the middle of an unrelated task.
5. **Never route around it.** Silently substituting a different test command, skipping the
   baseline, or "just this once" running the suite a different way makes every later comparison
   meaningless — including the reviewer's.

The same rule covers a missing task dir, a wire-proof rig that no longer exists, and a
`dod_extras` gate whose command is gone. Repair, record, or stop. Never proceed on a fiction.
