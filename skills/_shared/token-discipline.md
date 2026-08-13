# Token discipline

Vince is thorough, and thorough is expensive. Most of that cost is avoidable waste rather than
the work itself, and the waste has four shapes: **context you loaded and did not need**, **command
output you dumped instead of summarised**, **subagents you spawned out of habit**, and **sessions
you never reset**.

Rigour is not negotiable. How much you spend achieving it is.

## Read narrowly

- **Never `cat` a whole file to find one thing.** Grep for the symbol, then read the range around
  it. Reading a 2,000-line file to change 10 lines costs the whole file, every turn it stays in
  context.
- **Diffs before files.** `git diff --stat` to see the shape, then `git diff -- <path>` for the
  files that matter. `git diff` unbounded on a large branch can be tens of thousands of tokens.
- **Bound every command that can be long.** `| head -50`, `--max-count`, `-n 200`, `--since`. A
  full `npm test` log is mostly noise; the counts and the failures are the evidence.
- **Do not paste output twice.** If it is in the ledger, reference it. The ledger is the record —
  repeating it into the conversation buys nothing.
- **Load a `reference/` file when you reach the step that needs it**, not at the start. That is
  the whole reason they are separate files.

## Spend the model where judgement is needed

Deterministic checks do not need a language model. `scripts/check.py` runs the mechanical half of
a review — stray files, attribution trailers, new skips, debug statements, possible secrets,
whole-file rewrites, branch behind base — as one command with a compact report:

```bash
python <toolkit>/scripts/check.py --repo <repo> --base <integration branch>
```

Run it **before** the handoff so the implementer fixes the cheap things, and again as the first
step of a review. One tool call replaces roughly ten commands and their raw output, and it cannot
be forgotten or mis-parsed.

What is left is what actually needs a model: the blind pass, behaviour attacks, data isolation,
blast radius, and whether the work matches what was asked for.

## Subagents cost a whole extra context

Every subagent starts fresh: it re-reads the skill, the profile, the diff. That is real money, and
the fresh context is exactly why it is worth it for review — but only when review is the point.

- **One reviewer per task, not per criterion.** The reviewer covers the whole ledger.
- **T1 tasks do not spawn a reviewer at all** — they use the self-review checklist. Check the tier
  before spawning; a typo fix does not need a second context.
- **Batch small related tasks into one review** where they share a branch and a ledger.
- **Do not spawn a subagent to do something you could do in three tool calls.** Delegation pays
  when it saves your context more than it costs; searching for one symbol does not qualify.
- **Give a subagent the narrowest brief that still works.** A reviewer needs paths and the task
  ID, not a transcript.
- **Prefer a scoped agent type over a general-purpose one** where the harness offers it, and use a
  cheaper model for mechanical or search-shaped subagents. Reserve the strongest model for the
  review's judgement passes, where the quality difference actually shows.

## The ledger is your memory — use it and reset

This is Vince's structural advantage and it is routinely wasted. Everything that matters is on
disk: the contract, the evidence, the verdict, the resources you started. **You do not need the
conversation history to continue a task.**

- Compact or clear between phases of a long task, and between tasks entirely. Re-read the ledger
  instead of scrolling back.
- Past ~150k context, every turn is paying for history you are not using. Reset earlier than feels
  comfortable — the ledger is what makes that safe.
- Long-running loop sessions are the most expensive shape there is. If a task is waiting on
  something, stop and resume rather than idling.
- One task at a time where you can. Parallel sessions all draw from the same limit, and a queue
  spends it more evenly.

## Write short

- Reports go to a human. Lead with the answer. Nobody needs the narration of every command.
- The ledger records evidence, not prose. Command, output, verdict.
- Do not restate the plan you already agreed, or re-explain a concept you explained a turn ago.

## What never gets cut

Do not save tokens by skipping the gate. Specifically: no dropping the RED step, no reusing a
baseline you did not observe, no reviewing in-context to save a subagent, no marking something
`PROVEN` because re-running the proof felt expensive. Those do not save money; they just move the
cost to whoever finds the bug in production.

If a task is genuinely too big to do properly within budget, say so and propose splitting it. That
is an honest answer. A quietly weakened gate is not.
