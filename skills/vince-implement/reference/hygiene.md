# Commit and workspace hygiene

Read before your first commit on a task, and again before you report done.

## Commit hygiene (applies to every commit, not a phase)

- **Format:** `<prefix> Imperative description`, under 72 characters, no trailing period, one
  logical change per commit. The prefix is whatever the profile's `commit_convention` says
  (a ticket key, a conventional-commits type, or nothing). Multi-commit tasks share it.
- **No AI or bot attribution trailers** — no `Co-Authored-By:` bot lines, no "Generated with"
  footers — in commit messages or PR bodies, unless the profile explicitly opts in. This
  overrides any harness default that says to append one. Check the message you are about to
  write, not the one you intended to write.
- **Unticketed work:** do not invent a ticket key, and do not file a ticket to obtain one.
  Write a clean keyless imperative message, and tell the user the commits are keyless so they
  can decide whether a ticket should exist.
- **Stage per file.** Never `git add .`, `git add -A`, or `git commit -a`. That is how
  `.serena/`, `node_modules/`, `.env`, stackdumps and scratch files enter history. Run
  `git status --porcelain` and `git diff --cached --stat` before every commit and read them.
- **Never commit with a red suite** and a note to fix it later, and never commit directly on
  the integration branch.
- **Before every push:** `git fetch origin <integration> && git merge origin/<integration>`,
  resolve conflicts locally, re-run validations. Confirm the branch is not behind —
  `git rev-list --count HEAD..origin/<integration>` must be `0`. A branch that is behind will
  collide or ship out of order.
- **Version bumps, where the profile requires them:** the bump is exactly one increment above
  what is on the integration branch **right now**, not a blind bump from your branch's base.
  After merging, read the current value and set yours one step above *that*, every push:
  ```bash
  git show origin/<integration>:<version file>   # package.json / version.txt / *.csproj / pyproject.toml
  # your working file must then read exactly one increment higher
  ```
  Incrementing the number your branch happened to start with is the trap: if the branch moved
  from 2.2.73 to 2.2.80 while you worked, a bump to 2.2.74 is now *behind* and collides. Bump
  the last segment by default; only go minor/major when the change genuinely warrants it, and
  even then land exactly one step above in that segment. Shared libraries bump too, and their
  dependents get updated.
- Verify the diff before committing generated or scripted edits: `git show --stat` should
  show the lines you meant, not a whole-file line-ending flip.

## Workspace hygiene — worktrees and stray processes (enforced before "done")

You share this machine with other live sessions. Two things leak disk and RAM when a task
ends without cleanup: the git worktree you worked in, and any background process you started.
You clean up both — and only the ones **you** created.

**Record every resource as you create it.** The ledger's *Session resources* block takes one row
per worktree and per long-running process, written the moment it exists — not at the end, when a
crashed session will never get to it. This is the difference between a later cleanup being able to
say "this worktree belongs to a task that passed and pushed, removing it" and having to ask the
user about every directory it finds. An unrecorded resource is an orphan by construction.

**Worktrees — create one, track it, tear it down safely.**
- Work in a dedicated worktree off the integration branch (Phase 1), never the shared
  checkout, and record its path in *Session resources* so teardown has a target.
- On PASS-and-pushed (or on abandoning the task), remove it:
  `git -C <repo> worktree remove <path>` then `git -C <repo> worktree prune`.
- **Smart, not destructive.** `git worktree remove` refuses a dirty tree or a branch with
  unpushed commits — that refusal is a STOP, not a reason to reach for `--force`. Unsaved
  work is not yours to delete: leave the worktree in place and tell the user exactly what is
  uncommitted or unpushed. Never `rm -rf` a worktree, and never `--force` unsaved state away.
- Remove **only** the worktree you created for this task. `git worktree list` shows every
  session's; the others are not yours to touch.
- A subagent's isolated worktree auto-removes if unchanged; if it changed one, merge or push
  what you need from it first, then let it go.

**Background processes — start few, track them, stop them.**
- Prefer bounded over persistent: `tail -n 200` not `tail -f`, `--since=10m` not `-f`, run the
  suite once not in `--watch`. A one-shot `grep`/`sed`/`awk` exits on its own; a tail, watcher,
  dev server or port-forward does not.
- When you genuinely need a persistent process, start it as a *tracked* background task and
  stop it the moment the step that needed it is done — do not let it ride to the end of the task.
- **Before you report anything done, sweep your own:** no background job you started still
  running, no `tail -f` / watcher / dev server / port-forward left alive, and on Windows/Git
  Bash no orphaned `tail`/`sed`/`grep` from a pipeline you backgrounded. Stop them (harness
  background-task stop, or kill the tracked PID). Leaving them is how a box ends up in swap.

Teardown is part of "done": a task is not complete while it has leaked a worktree full of
throwaway state or a fistful of live tail processes. Mark each row in *Session resources* torn
down as you go, so the block reads empty-of-live-items when you report.

Came to a workspace someone else left in a mess — leaked worktrees, directories that will not
delete, processes nobody stopped? That is `vince-cleanup`, not this skill. It attributes what it
finds before touching it.
