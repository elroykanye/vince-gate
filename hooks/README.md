# Hooks — enforcement instead of instruction

**Status: experimental, opt-in.** Everything else in this toolkit is instructions a model can
forget. Hooks are executed by the harness, so they cannot be forgotten. That is the whole point,
and it is also why they need to be careful: a gate that fires wrongly is worse than no gate.

Currently ships one hook, for Claude Code.

## `vince_gate_stop.py`

A **Stop hook** that refuses to end a session while the active ledger says the work is unproven.
This is vince's prime directive — *no done without a PASS verdict* — enforced rather than asked
for. Exit code 2 blocks the stop and returns the message to the model as feedback.

It blocks when a recent ledger under `.vince/tasks/active/` has any `AC-`/`DOD-` row whose status
is `NOT-PROVEN`, `RED`, `GREEN` or `TAMPER-PASSED` (i.e. not yet `PROVEN`), or whose
`Reviewer verdict:` line is absent, `NOT-RUN` or `FAIL`.

It deliberately stays out of the way when: there is no `.vince/tasks/active/` directory, no
ledger has been touched in the last 24 hours (`VINCE_STOP_MAX_AGE_HOURS`), every row is `PROVEN`
and the verdict is `PASS`, or the stop was already blocked once (`stop_hook_active`) — that last
guard is what stops a session deadlocking.

`VINCE_STOP_DISABLE=1` turns it off without editing settings.

### Install

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python /absolute/path/to/vince-gate/hooks/vince_gate_stop.py"
          }
        ]
      }
    ]
  }
}
```

In `.claude/settings.json` for one project, or `~/.claude/settings.json` for all of them. Use an
absolute path, and `python3` if `python` is not Python 3.8+ on your machine.

### Verify it before you trust it

```bash
cd /tmp && mkdir -p probe/.vince/tasks/active/t && cd probe
printf '# t\nReviewer verdict: NOT-RUN\n\n| ID | R | L | C | Status |\n|--|--|--|--|--|\n| AC-1 | x | UNIT | `t` | RED |\n' \
  > .vince/tasks/active/t/verification-ledger.md
echo "{\"cwd\":\"$PWD\"}" | python /path/to/vince-gate/hooks/vince_gate_stop.py; echo "exit=$?"
# expect: a message on stderr and exit=2
```

### Known caveat

Claude Code has [an open issue (#24327)](https://github.com/anthropics/claude-code/issues/24327)
where a hook returning exit 2 sometimes leaves the session idle instead of the model acting on
the feedback — you type "continue" and it proceeds. That is why this is opt-in rather than part
of a normal install. If you hit it, `VINCE_STOP_DISABLE=1` is the escape hatch.

## What is deliberately *not* here

A `PreToolUse` hook blocking `Write`/`Edit` until a RED test exists would enforce test-first
directly. It is not shipped because the false-positive rate is the whole question: the hook
cannot tell "editing implementation code before a failing test" from "writing the failing test",
"fixing the build", "editing a doc", or "responding to the reviewer". A gate that blocks half
of legitimate work gets disabled within a day, and then enforces nothing at all.

If you want it for a specific repo whose layout makes the distinction cheap (a strict
`src/` vs `tests/` split, say), it is a short script — but write it for that repo rather than
expecting a generic one to work.

## Writing your own

Hooks receive a JSON payload on stdin and signal through exit codes: **0** allow, **1** warn
without blocking, **2** block and send stderr back to the model as feedback. Keep them under
~500ms since they gate every matched call, and make them fail *open* — a hook that crashes
should not brick the session. `vince_gate_stop.py` is a reasonable template: it parses stdin
defensively, treats every unknown state as "allow", and never blocks twice.
