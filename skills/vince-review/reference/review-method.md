# Review method

Load this reference after opening the original contract and diff, before the ledger.

## Blind record

Write the contract in your own words, list each observable behavior and negative constraint, map
changed entry points and dependents, and name the three most plausible failures. This record must
precede exposure to the implementer’s evidence.

Freeze that record as `review-coverage.json`. Give every item a stable ID, source, literal claim,
planned proof, and attacks. Include all A0–A7 passes. Do not remove an item after reading the
ledger; append discrepancies as new material-claim items. A review is exhaustive only when every
item has a terminal status and reproducible evidence or an explicit blocking reason.

## Contract and evidence forensics

Compare the blind criteria with the ledger verbatim. Missing, narrowed, invented, or contradictory
criteria are findings. For every claimed proof, rerun the exact command, confirm it targets the
reviewed branch, inspect pass/fail/skip counts, and verify that captured outputs could not come from
stale artifacts. Check version files, changelog, tags, installation manifests, and deployed revision
when those claims are in scope.

## Test attacks

- Confirm each behavioral test was seen RED for the expected reason.
- Inspect assertions for the actual output, state, or transport result.
- Search for skip, ignore, xfail, quarantine, retry masking, broad exception handling, and sleeps.
- Mutate each changed decision or output. Restore and rerun green plus regression.
- Treat surviving changed-line mutants as missing assertions unless equivalent is demonstrated.

## Behavior and boundaries

Exercise empty, minimum, maximum, malformed, missing optional, repeated, reordered, concurrent,
timeout, partial-failure, and locale variants that apply. For account-bearing software, use two
identities and prove cross-account reads and writes fail at the enforcing layer. Test unauthenticated,
authenticated-but-forbidden, and stale/revoked authorization paths.

For user interfaces, drive the running product rather than trusting a spec or screenshot. Inspect
the DOM, network, console, keyboard path, focus, responsive sizes, long content, loading, empty, and
error states. For packages or CLIs, invoke them as a consumer would.

## Blast radius and delivery

Run the full suite and compare baseline counts. Build/run affected dependents when public surfaces
changed. Confirm merged versus deployed state explicitly. Compare completion documentation with the
actual diff, tests, configuration, version, and deployment; inaccuracies are findings.

## Completion rule

Complete the whole frozen inventory even after the first finding makes FAIL inevitable. Reconcile
counts one raw case at a time, map every prose promise to the assertion or attack that enforces it,
and compare ledger, completion documentation, tracker, published documentation, configuration, and
live state wherever each is in scope. Record unavailable proof as BLOCKED or UNREVIEWED; neither is
permission to omit it or claim PASS.
