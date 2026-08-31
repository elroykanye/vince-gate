---
name: vince-learn
description: Promote recurring review findings and user corrections into Vince lessons, known traps, definition-of-done gates, and evidence-based metrics. Use after a PASS, during adoption, or when reviews repeatedly catch the same class of problem.
---

# Vince — Learn

The reviewer finds the same class of bug in the same codebase over and over, because nothing
carries the finding forward. This skill is that carrier: it converts findings into
configuration, so the *next* task is stopped at the gate rather than caught at review.

**One rule above all: promote patterns, not incidents.** A single typo does not become a
permanent gate. Something that has now happened twice, or that would have shipped a wrong
result, does.


## Communication and efficiency

Lessons are terse, factual artifacts. Load `reference/voice.md` only for the user-facing summary.
Load `reference/token-discipline.md` only for a large archive adoption pass; aggregate metrics with
scripts instead of loading every historical ledger into context.

## Inputs

- `<task dir>/review-verdict.md` — the findings and their history (the `[caught: …]` tags say
  which attack found each one).
- `<task dir>/verification-ledger.md` — what was blocked, waived, or hard to prove.
- `.vince/metrics.jsonl` — one line per completed task.
- `.vince/lessons.md` and `.vince/profile.md` — what is already recorded. Read these first, so
  you sharpen an existing entry instead of adding a near-duplicate.
- The conversation, for user corrections — "no, we always do X here" is a lesson even when no
  review caught it.

## What gets promoted, and to where

| Signal | Goes to | Shape |
|--------|---------|-------|
| A finding of a kind that has now appeared **twice** in this project | profile `known_traps` | one line: the trap, where it bites, how to check |
| A finding class that a **command can detect** (locale parity, missing isolation key, debug statements, unbounded reads) | profile `dod_extras` | a real gate row: `Gate \| Verify \| PASS condition` — and the verify command must run |
| A **user correction** or standing preference | `.vince/lessons.md` | the correction, why, and how to apply it |
| A wire proof that was **hard to construct** and now exists | profile `wire_proofs` | the rig, so nobody rebuilds it |
| A profile field that was **wrong** during the task | profile *Corrections* | already written by the self-healing step; verify it is there |
| A **one-off** mistake with no pattern behind it | nothing | resist. Noise in these files is what makes people stop reading them |

Promotion to a gate is a commitment: every future task in this project pays for it. Ask whether
the cost is worth the class of bug it stops. If it is not, a `known_traps` line is enough.

## Which level does it belong to?

In a workspace with many repos there are two lessons files and two profiles, and putting a
lesson in the wrong one is how these files rot: estate-wide knowledge trapped in one repo helps
nobody, and one repo's quirk in the hub file is noise every other repo reads forever.

Route by asking **would this be true in a sibling repo?**

| Signal | Goes to |
|--------|---------|
| A trap in one repo's code or its stack's tooling | that repo's `.vince/lessons.md` / profile |
| A pattern seen in two or more repos | the hub's — and say which repos |
| A hub default that was wrong for a repo | the **hub** profile's *Corrections*, because the default is what needs fixing |
| A convention, contract or platform behaviour | the hub |

The one people get wrong: an inherited command that failed in a repo is not just that repo's
correction. Fix it in the repo profile *and* consider whether the hub's stack default is wrong
for every repo of that stack — a wrong default costs each of them a first-touch detour.

## The lessons file

The resolved `lessons.md` (`install.py where --repo <repo>` — it is in the store, not the repo,
unless the repo carries its own `.vince/`), newest first. Each entry is small and actionable:

```markdown
## <YYYY-MM-DD> — <one-line lesson>

**Seen in:** <task-id> (<severity>, caught by <attack>) — and <task-id> if a repeat
**What happened:** <one or two sentences, concrete>
**Why it happened:** <the root cause, not the symptom>
**How to avoid it:** <what a future implementer does differently — a check, a pattern, a command>
**Promoted to:** known_traps | dod_extras gate `<name>` | nothing (single incident, watching)
```

Keep it under about 30 entries. When it gets longer, merge entries that share a root cause and
drop ones whose gate now catches them automatically — a gate makes its own lesson redundant, and
that is the file working as intended.

## Reading the metrics

Add `tokens` to the metrics line when the harness reports it. Cost per task, trending against
`rounds`, is the number that tells you whether the gate is paying for itself — and whether a
particular repo's tasks are expensive because they are hard or because something is being done
wastefully.


With a handful of lines in `.vince/metrics.jsonl` you can answer questions worth acting on:

- **Which attacks earn their time here?** Count `caught_by` across tasks. If mutation testing
  finds most CRITICALs in this repo, the reviewer should spend more of its budget there; if the
  live-browser pass finds nothing over ten frontend tasks, say so honestly rather than ritually
  repeating it.
- **Are rounds trending down?** `rounds` per task over time is the honest measure of whether
  this is working. Flat or rising means the lessons are not reaching the implementer — that is a
  finding about the loop, and it belongs in your report.
- **Which severity dominates?** Lots of MEDIUM and no CRITICAL suggests the gate is calibrated
  about right. Repeated CRITICALs in one area mean that area needs a gate, not more attention.
- **Is a tier being abused?** A stream of T1 tasks that later needed fixes means the tiering
  rules are being stretched; tighten them in the profile.

Report what the numbers actually support. Fewer than about five tasks is an anecdote — say that
rather than inventing a trend.

## Adopting Vince on an existing project

Run this once over the history to seed the loop instead of starting blind:

1. Read `<task root>/archive/` for prior verdicts and ledgers, if any exist.
2. Mine the repo for the same signal: recurring review comments in PR history, clusters of
   `HACK`/`FIXME`/`WORKAROUND`, incident notes, `git log` for revert chains and repeated fixes in
   one file.
3. Ask the user directly: "what breaks here that shouldn't?" — the most valuable traps are
   usually known and unwritten.
4. Write the top five or six as lessons and traps. Not thirty; a file nobody reads teaches
   nothing.

## Boundaries

- **Never edit a `review-verdict.md`.** It is the reviewer's artifact and its history is
  append-only. You read it; you do not tidy it.
- **Never weaken a gate to make a task pass.** Removing a gate is a decision with a written
  reason and the user's agreement, recorded in the profile.
- **Do not promote to the toolkit silently.** If a lesson is genuinely generic — true of any
  codebase, not just this one — say so and propose it as an addition to the toolkit's
  `dod-gates.md` or `attack-playbook.md`. That is a change to everyone's Vince, so it is the
  user's call, not yours.
- Everything you write is small, dated and concrete. "Be careful with dates" helps nobody;
  "week aggregation used local time and shifted rows across the year boundary — assert in UTC"
  is a lesson.
