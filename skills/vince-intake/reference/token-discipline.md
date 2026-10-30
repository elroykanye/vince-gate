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
- **Prefer a scoped agent type over a general-purpose one** where the harness offers it.

### Models: recommend, do not pretend to choose

You almost certainly **cannot select your own model** — that is the harness's setting, not
something a skill controls. So do not claim to have "picked a cheaper model", and do not silently
assume one was used.

What to do instead, once per task, in one line:

- Say **which model you are running as**, if you know it, in the verdict and the handoff. A review
  whose model is unrecorded cannot be weighed later.
- If the profile names `reviewer_model` or `mechanical_model`, **state them in the handoff** so
  whoever spawns the subagent can honour them, and give the exact flag or command for the harness
  in use.
- Recommend the split where it pays: the strongest model for the review's judgement passes (blind
  pass, behaviour, isolation, blast radius), something cheaper for search, file-finding and
  mechanical sweeps. The quality difference shows in the first group and is invisible in the
  second.
- If nothing is configured, say so once and move on. Nagging about it every task is its own waste.

## Checkpoints — the ledger is your memory

Vince's structural advantage, and the most commonly wasted one: the contract, the evidence, the
verdict and the resources you started are all on disk. **You do not need the conversation history
to continue a task.** But that is only true if the ledger is actually complete, so check rather
than assume.

### At every checkpoint

Checkpoints are phase boundaries — after Phase 1's baseline, after each AC completes in Phase 3,
before the Phase 7 handoff, and after a FAIL before starting remediation.

1. Bring the ledger current: statuses, evidence, Session resources.
2. Write or update the **Resume block** — current phase, the single next action, anything in
   flight. Two or three lines. This is what a fresh session reads first.
3. Verify it is genuinely sufficient:
   ```bash
   python <toolkit>/scripts/resume.py --task <task dir> --check
   ```
   `SAFE TO CLEAR` (exit 0) means the ledger stands alone. `NOT SAFE TO CLEAR` names exactly what
   is missing — fix that before clearing, or the gap goes with the conversation.

**Never suggest clearing without running that check.** Suggesting a reset on an insufficient
ledger destroys work, which is worse than any amount of context you were trying to save.

### Pressure signals

You cannot see your own token count. You *can* see these proxies, so keep a rough tally and
treat any of them as "checkpoint now":

- a phase boundary (always)
- ~15 files read, or ~5 full suite runs, since the last checkpoint
- a large diff, a long build log, or a big test output captured this turn
- the same file read more than twice — you are re-reading because it fell out of your head
- entering remediation, which re-reads everything the fix touches

These are approximations and the skill says so. A checkpoint costs a minute; being wrong in the
other direction costs the whole session's history.

### Proposing a compact or clear

**Off by default.** With `checkpoints: suggest` in the profile, at a checkpoint where
`resume.py --check` returns SAFE TO CLEAR, say so in one line:

> Checkpoint: AC-2 proven, ledger current, `resume.py` says safe. Good moment to `/compact` or
> `/clear` — I'll pick up from the ledger.

With `checkpoints: insist`, also stop and ask at pressure thresholds rather than only mentioning
it. Setting `off` means never raise it.

**You cannot run the compaction yourself** — `/compact` and `/clear` are the user's to type. Do
not claim to have triggered one, and do not pretend a suggestion was an action. Propose, and let
them decide.

### Between tasks

Clear entirely. A new task shares nothing with the old one but the profile, and that is on disk
too. Long-running loop sessions are the most expensive shape there is: if a task is waiting on
something, stop and resume rather than idling. And prefer one task at a time — parallel sessions
all draw on the same limit, and a queue spends it more evenly.

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
