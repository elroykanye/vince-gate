# Attack playbook

Concrete attacks with commands. Pick what the change actually touches, then push harder than
feels polite. Every attack you run goes in the attack log whether it broke something or not.

Where a command depends on the project (test runner, integration branch, isolation key,
locales), read it from `.vince/profile.md` rather than guessing.

## 1. Mutation testing by hand

Cheap and devastating. One mutation at a time, run the affected tests, restore.

| Mutation | Catches |
|----------|---------|
| Invert a boolean condition | tests that never hit the branch |
| Return a constant (`0`, `null`, `[]`, `""`) from the new function | tests asserting only "no exception" |
| Remove the isolation-key filter from a new query | isolation tests that do not exist |
| Remove the authorization check from the new entry point | auth tests that do not exist |
| Swap two arguments of the same type | positional-argument bugs |
| Off-by-one a boundary (`>=` to `>`) | boundary tests that do not exist |
| Delete the new field from the emitted event/response | contract tests that do not exist |
| Make the new entry point throw | error-path tests that do not exist |
| Short-circuit the cache to always miss, and always hit | tests that only pass on one cache state |

Safe procedure:

```bash
git stash list                      # note the starting state
# edit one thing
<test command for the affected tests>
git checkout -- <file>              # or git stash pop / git restore
git status --porcelain              # MUST be empty before moving on
```

Never commit a mutation, never push one, never mutate anything running on a shared environment.

If the branch has no test for a mutation you invented, that is itself the finding: the
implementation has an unguarded behaviour the ACs implied.

## 2. Dead-test smells

```bash
# which of the changed files are tests
git diff origin/<integration>...HEAD --name-only | grep -iE 'test|spec'
# skips and focus markers, branch vs base
git diff origin/<integration>...HEAD -U0 | grep -nE '\.skip|\.only|xfail|\[Ignore\]|@pytest\.mark\.skip|t\.Skip\(|describe\.only|it\.only'
```

Read the new tests and ask, per test: if the implementation were wrong, which line here would
fail? If you cannot point at the line, the test is decoration.

Other smells: expected values that were obviously copied from an actual run; a mock that returns
exactly the value being asserted; a test named for behaviour it never exercises; setup so
elaborate that it re-implements the logic under test; `try/catch` swallowing the assertion; an
E2E spec whose only assertion is that the page loaded.

## 3. Data-shape attacks

| Attack | Where it bites |
|--------|----------------|
| Empty result set | dashboards, charts, KPI cards, "no data" states |
| Single-element set | averages, min/max, chart axis ranges |
| Very large result set | unbounded "fetch all", response/message size limits, container memory limits |
| Null optional field | DTO mapping, tooltips, formatters, serializers |
| Zero and negative numbers | ratios, percentage change against a zero base, budgets |
| Gaps in a range | forecasting, pacing, running totals, calendar views |
| Unicode, emoji and very long strings | names, exports, filenames, column widths, DB column limits |
| Timezone, DST, year boundary | date ranges, weekly aggregation, scheduling |
| Locale other than the default | number, currency and date formatting hardcoded to one locale |
| Currency other than the default | money formatting and totals |
| Pagination first, last, beyond-end | list endpoints, infinite scroll |
| Duplicate submit / double click | idempotency, double writes, double charges |

## 4. Async, queue and consumer attacks

- Trigger the request, then let the reply never arrive. Does the caller time out cleanly with a
  real error, or hang until the client gives up?
- Replay the same message twice. Duplicate records, doubled totals, duplicate side effects?
- Payload size. Does a realistic worst-case account blow the transport limit?
- Restart the consumer mid-flow. Is the in-flight message lost, reprocessed safely, or
  poison-pilled?
- Malformed or older-version payload. Does the consumer crash-loop or handle it?
- Is the isolation key on the message and carried into every write it triggers?
- Does the topic/queue/type name match the project's convention, and is the version right?
- Ordering: does the handler assume messages arrive in order? Prove it when they do not.

## 5. Auth and isolation attacks

- A second account's credentials against the new entry point or the new resource ID. Anything
  other than a clean denial with no data is `CRITICAL`.
- No credentials, expired credentials, credentials without the permission.
- New permission or role key: grep wherever the project provisions them. Not provisioned means
  nobody can use the feature, or worse, the check silently passes.
- Direct object reference: swap an ID for one belonging to another account.
- Does the frontend hide it while the API still serves it?
- Are errors leaking existence ("no such record" vs "forbidden") in a way that enumerates?

## 6. Frontend attacks

```bash
# locale parity across every shipped locale (the profile names the command)
<locale parity command>
# debug statements in changed frontend files
git diff origin/<integration>...HEAD --name-only | grep -E '\.(ts|tsx|js|jsx|vue|svelte)$'
```

- Interpolation variables identical across every locale for each key.
- Narrow viewport: does the body scroll horizontally? Do sticky elements actually stick (an
  ancestor `overflow-x: hidden` silently kills `position: sticky`)? Measure the computed value.
- Layout after inserting/removing an item: overlaps, reflow, scroll jumps.
- Effect cleanup, dependency arrays, stale closures, subscriptions never torn down.
- Direct state mutation instead of a new object.
- Loading, empty and error states, not just the happy path.
- Identifier resolution consistency (`id` vs `entityId` vs `entity?.entityId || entity?.id`).
- Keyboard-only path through the new UI, focus order, labels on new controls.

## 7. Deploy-state attacks

```bash
# is the branch even merged
git fetch origin && git log --oneline origin/<integration> | head -20
# what is actually running (adapt to the platform)
kubectl get pods -n <ns> -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}'
docker ps --format '{{.Image}}\t{{.Status}}'
```

Claims of live behaviour need the running build to agree. Merged is not deployed, and pushed is
not merged. Also check whether config the change depends on actually exists in the running
environment, because a missing environment variable turns a working feature into a silent empty
state.

## 8. Shared library and dependency attacks

- The changed package's version versus the integration branch: bumped, and by exactly one step?
- Dependents: do the task-relevant consumers reference the new version, and do they build?
- Publish order: the library must land before dependents can restore it.
- Is the change breaking for a consumer that was not updated? Check the public surface diff.
- New dependency added: is it necessary, maintained, licensed compatibly, and locked?

## 9. Documentation attacks

- Every file path in the completion documentation: does it exist on the branch?
- Every code snippet: does it match the code at that path, or was it written from memory?
- Every claim of "verified": what command, what output?
- Does the doc describe what was intended rather than what shipped?

## 10. The honest last question

Before writing the verdict, ask: if this shipped tonight and broke tomorrow, what would the
post-mortem say the reviewer missed? Then go test that specific thing. If you cannot test it,
write it into the verdict as a named residual risk rather than leaving it silent.
