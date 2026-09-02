# Verdict and re-review

Load this reference only when writing or updating the verdict.

Write `<task-dir>/review-verdict.md` with the newest verdict first:

```markdown
# Vince review — <task> — <date>

VERDICT: <PASS | FAIL>

## Per-criterion verdict
| ID | Result | Evidence rerun | Attacks |
|----|--------|----------------|---------|

## Findings
### <SEVERITY>-1: <title> [CONFIRMED | RISK] [caught: <attack>]
- Location / criterion:
- Reproduction:
- Expected / actual:
- Impact:
- Required correction:

## Attacks that held
## Known review gaps
## Required before re-review
## Review history
```

Every finding must carry one `[caught: <attack>]` tag naming the attack that exposed it. This is a
machine-readable input to `vince-learn`, not optional prose. After persisting the verdict, you must
update the verification ledger's `Reviewer verdict` field with PASS or FAIL and a pointer to
`review-verdict.md`; a verdict that is not linked from the ledger cannot close the task.

PASS requires every criterion PROVEN, applicable gates satisfied, full regression no worse than
baseline, mutation sensitivity on changed behavior, truthful completion documentation, and no open
CRITICAL or MEDIUM finding. Record blocked attacks as gaps; if they prevent proving a criterion,
the verdict is FAIL.

For re-review, reproduce old findings before reading remediation claims, inspect the remediation
diff, rerun affected proof and full regression, then attempt bypasses and nearby variants. Move the
previous current verdict into append-only Review history. A finding closes only with reproducible
evidence; disagreement is recorded, not silently erased.
