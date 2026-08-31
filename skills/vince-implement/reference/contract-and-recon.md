# Contract and recon

Load this reference during Phases 0 and 1 only.

## Contract sources

Use the original tracker ticket and comments, program plan, versioned specification, existing task
directory, or the user-confirmed chat restatement. Store work under the resolved task root at
`active/<task-id>/`. Never create a ticket merely to satisfy the method.

For each acceptance criterion, record the exact wording, proof command, expected observation, and
proof level before implementation:

| Level | Meaning |
|-------|---------|
| STATIC | source/configuration inspection, compile, type check, or lint |
| UNIT | isolated internal behavior with boundaries substituted |
| INTEGRATION | real call across the owning interface |
| E2E-WIRE | complete path a user or consumer actually travels |
| MANUAL-OBSERVED | captured manual proof when automation is genuinely unavailable |

Observable behavior requires integration evidence and at least one task criterion must reach
E2E-WIRE.

## Profiles and memory

Resolve paths with `install.py where`. In a workspace, merge the hub profile with the repo profile:
repo scalars override; `dod_extras` and `known_traps` are additive. Hub commands are inferred and
unverified until run in this repository. Read lessons and configured decisions before designing.

If the repo has no verified profile, promote only commands actually run, observed baseline,
mutation setup, relevant paths, and working rigs. Record unknown or blocked facts honestly. A
wrong command may be re-derived once and recorded under Corrections; two wrong profile fields
require `vince-setup` refresh.

## Recon

- Confirm the owning repository and dependency order.
- Read repository instructions and only documentation touched by the scope.
- Create a worktree from the remote integration branch, not stale local state.
- Record the worktree before editing.
- Run the full suite per repository and capture pass/fail/skip counts.
- Treat a non-running suite, wrong owner, or required live write as a STOP.
- Prefer symbol navigation and bounded searches over whole-tree context dumps.
