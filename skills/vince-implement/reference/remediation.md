# Remediation and self-healing

Read when a review comes back FAIL, or when something the profile told you turns out to be wrong.

## Phase 8 — Remediation (when the verdict is FAIL)

A FAIL is a diagnosis to act on cleanly, not a nudge to try the same thing again. Rounds
multiply when you patch symptoms; they converge when you fix root causes. The rule that
matters here: **no endless FAIL loops.** You get a small, bounded number of rounds, and you
make each one count.

1. **Reproduce before you edit.** Every CRITICAL and every UNPROVEN AC came with repro steps —
   run them and watch it break. A finding you cannot reproduce is a disagreement for the user
   (Phase 7), not a thing you "fix" blind.
2. **Build a fix ledger.** In `implementation-status.md`, one row per finding:
   `finding → root cause (the real defect, not the symptom) → the single change that fixes it → the proof that flips it → the ACs/proofs it touches`.
   If you cannot name the root cause, you are not ready to edit. Reproduce and read the actual
   failing path first.
3. **Fix by root cause, worst first — not finding by finding.** Several findings usually share
   one cause; fix the cause once. Order strictly: CRITICAL (wrong results, isolation/auth,
   unproven ACs, dead tests) → MEDIUM → MINOR. Do not touch MINOR or refactor for taste while a
   CRITICAL is open — that is exactly how a 3-round fix becomes a 10-round one.
4. **Re-prove surgically.** For each AC you touched, re-run RED→GREEN→TAMPER. A dead test the
   reviewer killed with a mutation is not fixed until that same mutation makes it RED again —
   prove the tamper, don't just bolt on an assertion and hope.
5. **Regression pass before re-spawn.** Re-run the FULL suite and every prior wire proof, not
   only the AC you fixed. Fixes regress at a higher rate than fresh code, and the reviewer
   re-attacks everything the fix went near. A fix that broke a previously PROVEN AC is a net
   FAIL — catch it yourself, before the reviewer does.
6. Update the ledger, then **re-spawn a fresh reviewer** (Phase 7).

**Convergence guard — the anti-thrash rule (not optional):**

- Each pass, record the round number and the open-CRITICAL count in the fix ledger.
- **Thrash = the same root cause FAILs again after you "fixed" it, or the open-CRITICAL count
  does not drop between passes.** The instant you see it, STOP editing and escalate to the
  user. Retrying the same shape of patch will not work — your root-cause model is wrong. A
  stuck count never buys a third attempt; this is the lever against endless failing.
- **Converging = the count drops each pass and any new findings are genuinely deeper, not
  repeats.** Keep going, but post a one-line progress note to the user each round
  (`round N: X CRITICAL → Y`) so a long remediation is never a silent grind.
- **Backstop: not PASS after three re-reviews, even while converging → pause and check in.**
  Three clean rounds that still have not closed usually means the task is bigger than its
  contract, an AC is wrong, or a blocked dependency is in the way — the user's call, not
  another silent round.
- When you escalate, bring: the findings that will not die, your current root-cause hypothesis,
  exactly what each round tried and why it failed, and the real options (the AC or design may
  be wrong, the fix may need blocked data/infra, or the task may need splitting). Ten rounds of
  the same red is a failure of this gate, not diligence.

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
