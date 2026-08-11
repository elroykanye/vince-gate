# Definition-of-done gate catalog

Every gate resolves to PASS with evidence, FAIL, or N/A with a written reason. A ticked box
with no command behind it counts as FAIL. Record the command and its output in the
verification ledger, not just the verdict.

Sections apply per change type — skip a whole section with a one-line N/A when the task does
not touch it. The project profile (`.vince/profile.md`) supplies the concrete commands and may
add gates of its own under `dod_extras`; those are as mandatory as these.

## Correctness and coverage (always)

| Gate | Verify | PASS condition |
|------|--------|----------------|
| Every AC has a test that was seen RED first | ledger evidence log | RED + GREEN + TAMPER present for each AC |
| Full suite no worse than baseline | run the suite, diff counts | zero new failures, zero new skips |
| No test was weakened to pass | `git diff <base>...HEAD -- '*test*' '*spec*'` | no assertions deleted or loosened without a written reason |
| No skips introduced | grep changed tests for `.skip`, `.only`, `xfail`, `[Ignore]`, `@pytest.mark.skip`, `t.Skip(` | zero new occurrences |
| End-to-end path proven | the wire proof from Phase 4 | real transport, no mocks in the proven path |
| Lint / format / type check clean | the profile's static commands | no new violations vs baseline |

## Security, authorization and data isolation

| Gate | Verify | PASS condition |
|------|--------|----------------|
| Isolation key on every query | inspect each new read/write against the store | every query filters by the profile's `isolation_key` (tenant/org/owner) |
| Isolation key on every event/message | inspect new payloads | present and propagated end to end |
| New entry points protected | new routes/handlers/commands carry the project's authz check | no unguarded new entry point |
| New permission/role keys provisioned | grep wherever the project seeds them | every new key has a definition |
| Cross-account read attempt fails | request the resource as a second account | denied with no data, never a partial leak |
| Input validated at the boundary | inspect new request/message parsing | untrusted input validated and bounded before use |
| No secrets in code or config diff | grep diff for keys, tokens, passwords, connection strings | zero |

## APIs and services

| Gate | Verify | PASS condition |
|------|--------|----------------|
| Health endpoints | the project's liveness/readiness paths respond | success status |
| Metrics | new counters/timers exposed where the project collects them | present |
| Logging | structured logging with the project's fields | structured, no string-concatenated logs, no PII |
| Error handling | errors surface in the project's error envelope | no raw exception or stack trace leakage |
| API docs | new endpoints appear in the generated schema/docs | visible and typed |
| No debug output | grep changed files for `Console.WriteLine`, `print(`, `fmt.Println`, `System.out` | zero in non-test code |
| No unbounded reads | inspect new data access for "fetch all" shapes | paged, filtered, or bounded; responses within transport size limits |
| Timeouts and retries bounded | inspect new outbound calls | explicit timeout, bounded retries, no retry storm |

## Frontend

| Gate | Verify | PASS condition |
|------|--------|----------------|
| All shipped locales | the profile's locale parity command | identical key sets across every locale |
| Interpolation variables match | compare placeholders per key across locales | identical variable sets |
| Deleted keys cleaned everywhere | grep removed keys in every locale file | zero orphans |
| No debug statements | grep changed files for `console.log`, `console.warn`, `console.debug`, `debugger` | zero in non-test code |
| No hardcoded locale/currency | grep for a hardcoded locale tag, currency literal, `toLocaleString(` without a locale arg | formatting comes from config/i18n |
| Responsive | check the project's breakpoints, overflow handling, touch target size | no layout collapse, no horizontal body scroll |
| Accessible enough to use | keyboard path, focus order, labels on new controls, contrast | new UI is operable without a mouse |
| Loading / empty / error states | drive each state | each degrades honestly, no blank card, no raw payload |

## Data and messaging

| Gate | Verify | PASS condition |
|------|--------|----------------|
| Ownership respected | only the owning component writes the store/collection/table | no cross-writes |
| Indexes exist for new query shapes | check index/migration definitions | new filters and sorts are covered |
| Migration is reversible and tested | run up, run down, run up again on a realistic copy | no data loss, idempotent |
| Backwards compatibility | old readers against new writes, and the reverse | both directions survive a rolling deploy |
| Event/message naming | matches the project's documented convention | no invented topic or type names |
| Idempotency | replay the same message twice | no duplicate records, no double side effects |
| Failure path | let a downstream reply never arrive | caller times out cleanly with a real error, no hang |

## Shared libraries and packages

| Gate | Verify | PASS condition |
|------|--------|----------------|
| Version bumped | manifest version vs the integration branch | exactly one increment above the branch's current value |
| Dependents updated | grep dependents for the package version | task-relevant dependents on the new version |
| Publish order respected | check CI order | library publishes before dependents can restore |
| Consumed locally before publish | local package/link build | a dependent builds and runs against the local build |
| Not binary/API breaking for un-updated consumers | inspect the public surface diff | removals and signature changes are deliberate and announced |

## Deployment and hygiene

| Gate | Verify | PASS condition |
|------|--------|----------------|
| Deploy config updated | chart/manifest/compose values, env vars, resources | new config present, limits sane |
| Line endings clean | `git show --stat`, `git diff --stat` | only intended lines changed, no whole-file CRLF flip |
| Branch hygiene | branched off the integration branch, never committed on it | clean feature branch |
| Commit messages | `git log --format='%s' origin/<integration>..HEAD` | every message matches the profile's convention, under 72 chars, one logical change |
| No AI attribution | `git log --format='%B' origin/<integration>..HEAD \| grep -iE 'co-authored-by\|generated with\|🤖'` | zero matches, in commits and in the PR body |
| No stray artifacts | `git diff --stat origin/<integration>...HEAD` | no `.serena/`, `node_modules/`, `.env`, lockfile noise, stackdumps, scratch files |
| Version bumped where required | manifest vs the integration branch | bumped per the profile's `versioning` rule |
| Synced before push | `git fetch origin <integration> && git merge origin/<integration>` | branch contains the current integration branch, no conflict markers anywhere |
| Deployed state matches the claim | read the running image tag / build number / deployed commit | what is running is what the ledger claims |
| Docs match reality | completion documentation cross-checked against the branch | every claimed path and snippet exists |
