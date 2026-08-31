---
name: vince-cleanup
description: Safely clean leaked worktrees, attributable processes, background jobs, and regenerable output after a task. Use for cleanup, locked directories, failed worktree removal, stray processes, or unexplained workspace disk use.
---

# Vince — Cleanup

A session that ends without teardown leaves three things behind: **git worktrees** full of
throwaway state, **processes** still holding directories open, and **output** nobody needed. The
worktrees waste disk, the processes waste RAM and make the directories undeletable, and the
output hides real diffs.

`vince-implement` tells a session to sweep up after itself. This skill is for when that did not
happen — the session crashed, was interrupted, or predates the rule.


## Communication and efficiency

Be literal and calm before destructive actions. Load `reference/voice.md` only if a report needs
tone guidance. Load `reference/token-discipline.md` only when inventory output or context becomes
large; otherwise keep commands bounded and never spawn a helper for mechanical discovery.

## Stance: this is the most destructive skill here

Everything else in this toolkit reads, writes documents, or runs tests. This one kills processes
and deletes directories. So it is built to refuse:

- **Inventory before you touch anything.** Nothing is stopped or deleted until the whole picture
  is on screen and attributed.
- **Never act on what you cannot attribute.** A `node` process you did not start might be the
  user's dev server, their editor's language server, or another agent session mid-task. Stopping
  processes by *name* can terminate an unrelated editor or dev server.
- **Unsaved work is never yours to delete.** A dirty worktree or unpushed commits is a STOP and a
  report, not a `--force`.
- **Regenerable or nothing.** Delete build output, caches and scratch. Never delete source,
  logs someone may need, or anything you cannot name the regenerating command for.
- Being slightly too conservative costs disk. Being too aggressive costs somebody a day's work.
  Those are not symmetric, so lean hard one way.

## 1. Inventory

Do all four, and write the results down before acting.

**Worktrees.** For each repo in scope:

```bash
git -C <repo> worktree list
git -C <repo> worktree list --porcelain   # includes branch + bare/detached state
```

For each one that is not the main checkout, gather: path, branch, `git -C <wt> status --porcelain`
(dirty?), and `git -C <wt> log --branches --not --remotes --oneline` (unpushed commits?).

**Processes holding paths in scope.** The specific thing that makes directories undeletable, and
the step most likely to be done wrongly.

> **Do not start by grepping command lines for the directory.** The process that bites you is
> `python -m http.server` started a week ago inside `dist/`: its command line is
> `python -m http.server 4200`, its image is `python.exe`, and **neither contains the path**. The
> association lives in the working directory and open handles, which `Win32_Process` does not
> expose. A command-line filter returns nothing and you conclude the directory is held by
> nothing — the exact dead end this section exists to prevent.

Sweep on three axes instead. Any one of them finds the class; together they are hard to escape.

```powershell
# 1. LISTENING PORTS - a preview or dev server exists to serve, so it is bound to something
Get-NetTCPConnection -State Listen |
  Select-Object LocalPort, OwningProcess,
    @{n='Name';e={(Get-Process -Id $_.OwningProcess -EA SilentlyContinue).Name}},
    @{n='Started';e={(Get-Process -Id $_.OwningProcess -EA SilentlyContinue).StartTime}} |
  Sort-Object LocalPort

# 2. AGE + IMAGE - dev tooling that has been up for days is nobody's active work
Get-Process node,python,python3,dotnet,java,ruby,php,deno,bun -EA SilentlyContinue |
  Where-Object { $_.StartTime -lt (Get-Date).AddHours(-12) } |
  Select-Object Id, Name, StartTime,
    @{n='Cmd';e={(Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine}}

# 3. OPEN HANDLES - definitive, needs Sysinternals handle.exe
handle.exe -nobanner -accepteula "<path>"
```

```bash
# macOS / Linux - same three axes
lsof -nP -iTCP -sTCP:LISTEN                 # ports
ps -eo pid,lstart,etime,comm,args --sort=start_time | head -30   # age
lsof +D "<path>" 2>/dev/null | head -40     # handles (also catches cwd)
fuser -v "<path>" 2>&1
```

Then, for each candidate, resolve what it is actually sitting on — the question the command line
cannot answer:

```powershell
handle.exe -nobanner -p <pid>            # every handle, including the directory it holds
```
```bash
lsof -p <pid> | grep -E 'cwd|DIR'        # cwd is the line that matters
readlink /proc/<pid>/cwd                 # Linux, exact
```

**Shapes that hide from a path grep.** Every one of these serves or watches a directory while
naming it nowhere:

| Command | Why it hides |
|---------|--------------|
| `python -m http.server <port>` | module run; serves **cwd**, which appears in no argument |
| project-local `serve`, `http-server`, or `live-server` binary | serves cwd or a short relative path |
| `php -S localhost:8000`, `ruby -run -e httpd .` | same shape |
| `node` from a dev server (Vite, Next, Angular) | image is `node`; the project path may only be in cwd |
| `dotnet watch`, test runners in `--watch` | long-lived, re-spawn children |
| `kubectl port-forward` | holds a port, not a directory, but leaks the same way |
| orphaned `tail`/`sed`/`grep` on Windows/Git-Bash | left by a backgrounded pipeline |

A week-old `python` bound to a dev port is not somebody's careful setup. It is a preview server
somebody started once to look at a build, and it will hold that directory until the machine
reboots.

**Harness background jobs.** Whatever your harness tracks. These are the easiest and safest to
deal with, because they are attributable by construction — start there.

**Stray output.** Scratch dirs, build output, tool artifacts (`.playwright-mcp/`, coverage,
`dist/`, `target/`, `__pycache__`), log files, and `.orig`/`.rej`/stackdump files. Check whether
each is gitignored — an ignored artifact is regenerable and safe; a *tracked* file that looks like
output is a finding about the repo, not rubbish to delete.

## 2. Attribute each item

Three buckets, and the middle one is where the discipline lives:

| Bucket | How you know | What you may do |
|--------|--------------|-----------------|
| **Yours** | recorded in a ledger's *Session resources* block, or you started it this session | act, subject to the safety rules below |
| **Unknown** | no ledger references it, no way to tie it to a finished task | **report only.** Ask. Never act unprompted |
| **Someone else's** | another live session's worktree, a process with a live parent, a task whose ledger is still open | leave it, and say so |

Ledgers are the attribution source: `<task root>/{active,archive}/*/verification-ledger.md`
records the worktree path and any long-running process a task started. A worktree named after a
task whose ledger shows PASS and pushed is safely yours. A worktree matching no ledger at all is
`unknown` — it may predate Vince, and it may be the only copy of something.

## 3. Act, in order of reversibility

**a. Stop tracked background jobs.** Harness-tracked first; they stop cleanly and cost nothing.

**b. Stop attributed processes — gracefully first.**

```bash
# Windows: ask, then insist
Stop-Process -Id <pid>            # graceful
Stop-Process -Id <pid> -Force     # only after the graceful attempt failed

# Unix
kill <pid>        # SIGTERM, wait a moment
kill -9 <pid>     # only if it ignored SIGTERM
```

By **PID from the inventory**, never by name.

**Then verify the stop actually achieved something** — "killed it" is not the same as "the
directory is free":

```powershell
Get-Process -Id <pid> -EA SilentlyContinue          # gone?
Get-NetTCPConnection -LocalPort <port> -EA SilentlyContinue   # port released?
Remove-Item "<path>\.probe" -EA SilentlyContinue; New-Item "<path>\.probe" -ItemType File
```

A supervisor may restart the child, in which case stop the supervisor rather than the child and
say so. A port that stays bound means another process holds it too — the case that prompted this
section had **two** servers on the same port, and killing one changed nothing observable.

**c. Remove worktrees that are provably safe.**

```bash
git -C <repo> worktree remove <path>     # refuses on dirty or unpushed - that refusal is a STOP
git -C <repo> worktree prune             # clears records of directories already gone
```

`git worktree remove` refusing is the safety net doing its job. Do not reach for `--force`, and
**never `rm -rf` a worktree** — that leaves the repo's metadata inconsistent and destroys whatever
was in it. If it refuses, report exactly what is uncommitted or unpushed and let the user decide.

Removal failing with a *permission* or *in use* error is different: something still holds it. Go
back to the process inventory for that path, clear the holder, retry.

**d. Delete regenerable output.** Only paths you can name the regenerating command for, and only
after showing the list.

## 4. When a directory will not delete

The specific failure that sends people here. Work it in this order rather than escalating force:

1. **Identify the holder** with the commands above. Do not guess.
2. **Nothing shown holding it?** You probably searched the wrong way. Command-line and image-path
   filters miss anything that serves its *working directory* — re-run the three-axis sweep above
   (ports, age, handles) before concluding it is unheld. Only after that, check for a lingering
   handle from something that is not a server at all: the folder open in Explorer, a terminal
   `cd`'d into it, an antivirus scan mid-flight. Closing that window is often the whole fix.
3. **A live holder you can attribute?** Stop it (step 3b), then retry.
4. **A live holder you cannot attribute?** Stop. Report the PID, image path and command line and
   ask. This is exactly the case where killing blind breaks something the user cares about.
5. **Still stuck?** Say so plainly and leave it. A directory that survives a reboot is a real
   problem worth a human; a directory you forced away can be a lost afternoon.

Never resort to `rm -rf`, `Remove-Item -Force -Recurse`, or `takeown`/`icacls` on a path you did
not create, and never on a git worktree at all.

## 5. Report

```markdown
## Cleanup — <workspace> — <date>

**Reclaimed:** <n> worktrees, <n> processes stopped, <size> of output

### Removed
- `<path>` — worktree for <task-id> (PASS, pushed) · `git worktree remove` clean
- pid 4812 `node` — dev server from <task-id>, stopped gracefully

### Freed
- port 4200 released, `<path>` now writable (probe file created and removed)

### Left alone, deliberately
- `<path>` — 3 uncommitted files. Not mine to delete. `git -C <path> status` to see them
- pid 9310 `node` — cannot attribute; command line suggests your editor's language server

### Needs your decision
- `<path>` — worktree matching no ledger, branch `x` has 2 unpushed commits
```

Then state what is still holding anything, and what you did not touch. A cleanup that silently
skipped things is how the next session hits the same wall.

## Prevention

Cleanup is a recovery tool; the fix is upstream. `vince-implement`'s *Workspace hygiene* section
covers it: prefer bounded commands over persistent ones (`tail -n 200`, not `tail -f`; run the
suite once, not in `--watch`), record the worktree and any long-running process in the ledger's
**Session resources** block as you create them, and sweep before reporting done.

That block is what makes this skill able to act confidently rather than ask about everything —
attribution is the whole difference between "removed 4 worktrees" and "found 4 worktrees, please
advise". If a task recorded nothing, cleanup after it is necessarily conservative.

The optional Stop hook (`hooks/README.md`) also refuses to end a session whose ledger reads PASS
while the worktree it recorded still exists.
