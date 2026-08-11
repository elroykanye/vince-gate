# The method

Vince exists because agents are good at producing work that *looks* finished. The method is
built around one asymmetry: writing plausible code is cheap, and proving code correct is not.
So every rule here spends effort on the expensive half.

## Two hats, never worn at once

An implementer arguing that their own work is done is not a review. The implementer and the
reviewer are separate skills, and the reviewer runs in a **fresh subagent** with none of the
implementer's context — no summary, no severity opinions, no "already verified" claims in the
spawn prompt. The one thing that reliably defeats an adversarial review is being told what to
think before it starts.

The reviewer never fixes anything, either. Finding and reproducing is the whole job; a reviewer
that starts patching stops being able to see the work from outside.

## The reviewer starts blind

Separating the reviewer's context is necessary but not sufficient, because the ledger travels
across that boundary — and the ledger is a document whose every row asserts the work is proven.
Framing of that kind measurably suppresses what a reviewer detects, and autonomous agents are
markedly more susceptible to it than people are.

So the review opens on the diff and the original contract, with findings written down before the
ledger is read. Commit messages, PR text and ledger prose are claims about the work, never
evidence of it. The verdict then records how many findings were blind and how many arrived only
after reading the ledger — which makes a review that read the answer sheet visible instead of
indistinguishable from a thorough one.

## Evidence, not adjectives

"Verified", "should work", "tests pass", "minor", "non-blocking" are banned unless followed by a
command and its output. The verification ledger exists so that every acceptance criterion has,
on disk, the exact command that proves it and what that command printed. A proof invented after
the code is written is a rationalisation; a proof decided before it is a contract.

## RED before GREEN, and TAMPER after

Test-first is not a style preference here — it is the only cheap way to know a test can fail.
A test that was never seen red proves nothing about the implementation, and there is no way to
tell the difference later by reading it.

TAMPER closes the other half: break the implementation on purpose and confirm the test notices.
Dead tests are the single most common way a task passes review it should not have. Coverage does
not substitute — suites at 100% coverage routinely kill single-digit percentages of mutants, so
a green coverage number is close to no evidence at all.

Where the stack has a mutation tool, TAMPER runs it scoped to the diff and treats surviving
mutants as work: each one is an assertion the tests are missing. Where it does not, the same
thing happens by hand, one mutation per criterion. The reviewer re-runs it either way, so the
implementer may as well find them first.

Commit the green implementation **before** tampering. `git checkout --` on an uncommitted file
throws the implementation away with the mutation, and on a new file it fails outright and leaves
the mutation in place — either way the next mutation runs against a broken baseline and its
result means nothing.

## Model diversity, where you can get it

A fresh context removes the generator's reasoning trace and the local scaffolding that produced
the work. It does not remove the failure modes that live in the model's parameters: the blind
spot that wrote the bug is the blind spot that misses it. Context separation plus a different
model — ideally a different vendor — is stronger than either alone, so the profile can name a
`reviewer_model` and the verdict records which model actually ran.

## Levels of proof, and the one that is not negotiable

`STATIC` < `UNIT` < `INTEGRATION` < `E2E-WIRE`. A user-observable criterion proven only at unit
level is **not proven**, and at least one criterion per task must reach `E2E-WIRE` — the real
path, real transport, no mocks anywhere in it.

This rule exists because the failures that reach users are almost never unit-level. A page that
returns a gateway 404 in a browser while every server-side check is green; per-item render tests
that pass while the assembled page is wrong; a consumer that works in-process and dies on a real
message. Unit green is not working software.

## The contract is copied, never paraphrased

Acceptance criteria go into the ledger **verbatim**. Paraphrasing is how scope silently shrinks:
each restatement softens one qualifier, and three restatements later the task is smaller than
the one that was asked for. The reviewer re-derives the criteria from the original source and
diffs them against the ledger precisely to catch this.

## FAIL is the default, and PASS is earned

A reviewer that starts from "probably fine" finds nothing. Starting from FAIL means every PASS
has an attack log behind it — what was tried, what held. A PASS with no attack log is worthless,
and so is a fabricated finding: everything is either `CONFIRMED` (reproduced) or explicitly
`SUSPECTED` with what could not be verified.

## What this does not buy you

Independent review measurably beats same-session review, and the gap is widest exactly where it
matters most — critical errors. It still finds a minority of defects, and the category it barely
improves is *contextual* errors: whether the code actually works in its real environment.

That is not an argument against the review; it is the argument for everything around it. The
wire proof, the mutation gate, the DoD gates and the suite baseline are all verification that
does not depend on a model's judgement at all, and they carry as much of the weight here as the
reviewer does. A PASS means a determined adversary with your suite and your environment could
not break it in one pass. It has never meant "correct".

## Bounded remediation

FAIL → fix → re-review can loop forever if each round patches symptoms. So remediation is
explicitly bounded:

- fix by **root cause**, worst first, never finding-by-finding;
- **thrash** (the same cause fails again, or the open-CRITICAL count does not drop) is an
  immediate stop-and-escalate, not a third attempt;
- three re-reviews without a PASS, even while converging, is a check-in — usually the task is
  bigger than its contract, a criterion is wrong, or a dependency is blocked.

The reviewer carries the open-CRITICAL count in every history line so the trend is visible to
both sides.

## Read-only on shared state

Never write to shared dev/test/prod infrastructure to unblock a verification run — not a
database record, not a cache key, not a cluster resource, not identity state. This holds even
when the change is one record, carefully verified and trivially reversible.

The reason is not that agents are careless; it is that code has branches, PRs and review, and
live shared state has no such net. A gap discovered during verification is a **finding** to
report with the exact change you would make — not an obstacle to route around. This rule is
written into both skills and must be restated in every subagent prompt, because a subagent that
was not told will helpfully fix things.

## Honest partial delivery

Partial delivery reported honestly beats full delivery claimed falsely, every time. A blocked
criterion is marked `BLOCKED` with what blocks it — never `WAIVED` without a user decision on
record, and never quietly downgraded to a passing row. When the blocker belongs to someone else
entirely, it becomes a tracked external request rather than a silent TODO that resurfaces three
sessions later.
