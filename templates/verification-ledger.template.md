# <task-id or task name> Verification Ledger

Tier: `<T1 | T2 | T3>` (`<the rule that put it there>`)
Profile: `<repo profile>` inheriting `<hub profile, if any>`
Worktree: `<path>` (off `origin/<integration>`; remove on completion)
Reviewer verdict: NOT-RUN | FAIL | PASS (`<date>`, see `review-verdict.md`)

One row per repo the task touches, in dependency order (shared lib → service → consumer →
frontend). Each repo needs its **own** observed baseline:

| # | Repo | Branch | Baseline suite (passed/failed/skipped) | Commands verified here? |
|---|------|--------|----------------------------------------|-------------------------|
| 1 | | | | verified this task / already in repo profile |

## Session resources

Everything this task created that outlives a command, recorded **as you create it** - this is
what lets `vince-cleanup` act later instead of asking about everything. Tear all of it down
before reporting done.

| Resource | Where | Started | Torn down |
|----------|-------|---------|-----------|
| worktree | `<path>` (repo `<repo>`, branch `<branch>`) | `<date>` | no |
| background job | `<what it is, pid or harness job id>` | `<date>` | no |

## Contract

Every acceptance criterion and definition-of-done item, verbatim from the source. One row each.

| ID | Requirement (verbatim) | Proof level | Proof command | Status |
|----|------------------------|-------------|---------------|--------|
| AC-1 | | E2E-WIRE | | NOT-PROVEN |
| AC-2 | | INTEGRATION | | NOT-PROVEN |
| DOD-1 | | STATIC | | NOT-PROVEN |

Proof levels: `STATIC` < `UNIT` < `INTEGRATION` < `E2E-WIRE` < `MANUAL-OBSERVED` (last resort,
must say why automation was impossible). At least one row must reach `E2E-WIRE`. A
user-observable AC proven only at `UNIT` is NOT PROVEN.

Status vocabulary: `NOT-PROVEN`, `RED`, `GREEN`, `TAMPER-PASSED`, `PROVEN`, `BLOCKED`,
`WAIVED(user, date)`. `PROVEN` requires RED evidence, GREEN evidence and TAMPER evidence, all
three.

## Evidence log

Paste real command output. No paraphrasing, no summaries.

### AC-1 RED (<date>, commit `<sha>`)

```
$ <command>
<failure output — and it must fail for the reason you expect>
```

### AC-1 GREEN (<date>, commit `<sha>`)

```
$ <command>
<pass output>
```

### AC-1 TAMPER (<date>)

Committed the green implementation first, then mutated `<file>` (`<what you broke>`).

```
$ <command>
<failure output — the mutation killed the test>
$ git checkout -- <file> && git status --porcelain
<empty>
```

### Suite after AC-1 (<date>)

```
$ <suite command>
<counts — compare against baseline: no new failures, no new skips>
```

## Wire proof

| AC | Change type | Rig | Evidence |
|----|-------------|-----|----------|
| | | | |

## Definition-of-done gates

| Gate | Verdict | Evidence / reason |
|------|---------|-------------------|
| | PASS / FAIL / N/A | |

## Self-attack (Phase 6)

The three most likely production failures, and what happened when they were tested.

1. 
2. 
3. 

## Known risks / not covered

- 
