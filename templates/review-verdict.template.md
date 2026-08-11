# Review verdict — <task-id>

**Current: FAIL | PASS** · `<YYYY-MM-DD>` · `<repo>@<branch>` @ `<commit>` · suite `<N/M/K>` (baseline `<N/M/K>`)

Reviewed by `vince-review` in a fresh context. Default verdict is FAIL; PASS is earned.

## Per-AC verdict

| ID | Requirement | Claimed | My verdict | Why |
|----|-------------|---------|------------|-----|
| AC-1 | | PROVEN | PROVEN / UNPROVEN / BROKEN | |

## Findings

### CRITICAL-1: <one line> [CONFIRMED | SUSPECTED]

- Where: `path/to/file:line`
- Repro: `<exact commands>`
- Expected: … Actual: …
- Impact: …

### MEDIUM-1: <one line> [CONFIRMED | SUSPECTED]

### MINOR-1: <one line> [CONFIRMED | SUSPECTED]

Severity: `CRITICAL` for wrong results, data loss, cross-account or auth leakage, unproven ACs,
dead tests, production breakage. `MEDIUM` for edge-case bugs, missing indexes, dead code,
missing error handling. `MINOR` for style and documentation gaps. An unproven AC is never
`MINOR`.

## Attacks that did not break it

- 

## What is genuinely good

<short, honest, no padding>

## Required before re-review

1. 

---

## Review history (newest first)

- `<YYYY-MM-DD>` — FAIL @ `<commit>` — `<N CRITICAL → M>`: <the deciding findings, one line>
