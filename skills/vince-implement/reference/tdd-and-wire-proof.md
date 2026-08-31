# TDD and wire proof

Load this reference before the first RED and keep it through Phase 4.

## Per-criterion evidence

RED must fail for the expected missing behavior. GREEN must pass because of the implementation,
not a weakened test. Preserve the green state before TAMPER. Use the configured diff-scoped
mutation runner or mutate by hand: flip a condition, return a wrong value, empty a collection, or
remove an isolation filter. The test must fail. Restore from the committed green state or an
explicit backup, rerun the focused test, then run the suite.

Never restore an uncommitted new implementation with a destructive checkout. Never commit a
mutation. Never accept a surviving mutant on changed behavior without either a new assertion or a
written equivalent-mutant justification.

Forbidden shortcuts include editing expected results to match a bug, adding skip/ignore/xfail,
mocking the behavior under test, asserting only mock calls, committing red, or treating coverage as
fault detection.

## Wire proof

Use the profile’s concrete rig:

| Change | Required observation |
|--------|----------------------|
| HTTP | real authenticated request, status, and body |
| Queue/event | produced and consumed correlation plus resulting state |
| Job | real trigger, side effect, and repeat/idempotency observation |
| CLI | user-style invocation, exit code, stdout, and stderr |
| Shared package | bumped package consumed and run by a dependent |
| Frontend | running app driven in a real browser; DOM, console, network, and locales checked |
| Migration | realistic copy, row/sample diff, and rollback |
| Config/infra | disposable environment with observed effect |

Merged is not deployed. Never claim live behavior without checking the deployed revision. Missing
permissions, credentials, data, or rigs are BLOCKED findings, not permission to fake a weaker path.
