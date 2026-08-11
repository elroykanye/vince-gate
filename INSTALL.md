# Install

Two ways: hand the block below to your agent and let it do the work, or
[run four commands yourself](#manual-install).

Requirements: Python 3.8+, git, and an agent harness. No dependencies, no network calls at
runtime, no account.

---

## Paste this to your agent

Copy everything in the box into your coding agent. It will clone, detect your harness, install,
verify, and report back.

```text
Install vince-gate for me (https://github.com/elroykanye/vince-gate).

1. CLONE. Put it somewhere permanent, not a temp directory — ask me where if it is not
   obvious from how this machine is organised. If it is already cloned here, use that copy
   and `git pull` instead of cloning again.

2. LOOK BEFORE INSTALLING. From the clone, run:
       python scripts/install.py bindings
   (use `python3` if `python` is not Python 3.8+). This lists the agent harnesses it knows
   and which are verified. Show me the output.

3. PICK A SCOPE and tell me which before you run it:
   - `--scope user` installs into my home harness directories. Available in every project,
     never appears in any project's working tree, cannot be committed by accident.
     This is the right default — use it unless I say otherwise.
   - `--target <path to repo>` installs into one repo, so a team gets the gate from a
     checkout. Use this if I asked for it, or if only one project should have it.

4. DRY RUN FIRST:
       python scripts/install.py install <scope flags> --dry-run
   Show me the file list. Leave `--binding` at its default (auto — it detects which harnesses
   are in use) unless I named specific ones.

5. INSTALL, then VERIFY:
       python scripts/install.py install <scope flags>
       python scripts/install.py status  <scope flags>
   The status must print `healthy` and exit 0. If it does not, stop and show me the output.

6. CONFIRM DISCOVERY. Check that the skills are actually visible to the harness you are
   running in — list your available skills, or look in the directory the installer wrote to.
   If you cannot confirm it, say so plainly. Do not assume it worked because the files exist.

7. REPORT: where the clone lives, which scope and bindings you installed, the version, how I
   invoke the skills in this harness, and what I should do next (run `vince-setup` once in a
   project before the first task).

RULES:
- Do not modify any file outside the clone and the install target.
- Do not commit or push anything.
- If a step fails, stop and show me the exact command and its output. Do not work around it,
  do not substitute a different command, and do not report success you did not verify.
```

### What that will do to your machine

Worth knowing before you authorise it:

- Clones the repo where you say.
- Writes skill files into your harness's skills directory — `~/.claude/skills/` for a user-scope
  Claude Code install, `<repo>/.claude/skills/` (or `.cursor/rules/`, etc.) for project scope.
- Writes one manifest: `~/.vince/install.json` or `<repo>/.vince/install.json`, recording a
  checksum per installed file so drift can be detected later.
- For project scope only, adds a delimited block to `AGENTS.md`/`GEMINI.md` if your harness uses
  one, stating the gate in plain language.

That is all. No hooks, no settings edits, no daemons, no global state.

---

## Then, once per project

Paste this in a session opened on the project you want gated:

```text
Set up vince-gate on this project.

1. Confirm it is installed and healthy — run the installer's `status` command from the clone.
   If it is not installed, stop and tell me.
2. Invoke the `vince-setup` skill. It inspects this repo and writes `.vince/profile.md`: the
   test commands, integration branch, tracker, versioning rule, data isolation key, locales
   and wire-proof rigs.
3. Every command it records must be one you actually ran and watched succeed. Anything you
   could not confirm must be written as `unknown — <what you tried>` or marked
   `(inferred, unverified)`. Do not write a plausible-looking guess: everything downstream
   trusts this file.
4. Add `.vince/tasks/` and `.vince/install.json` to this repo's .gitignore. Leave
   `.vince/profile.md` tracked — it is project knowledge worth committing.
5. Show me the finished profile and tell me which fields you could not verify.
```

Read the profile it produces. Five minutes there is the highest-value five minutes you will
spend on this toolkit — a wrong isolation key means the reviewer's sharpest attack is aimed at
the wrong field, silently.

After that, `/vince-implement` (or your harness's equivalent) on every task, before code.

---

## Manual install

```bash
git clone https://github.com/elroykanye/vince-gate.git
cd vince-gate
python scripts/install.py bindings                  # what it knows, and what is verified
python scripts/install.py install --scope user      # or --target /path/to/repo
python scripts/install.py status  --scope user      # must say healthy, exit 0
```

Then in a project: `/vince-setup` once, `/vince-implement` per task.

| Want | Command |
|------|---------|
| Every project on this machine | `install --scope user` |
| One repo, committed for a team | `install --target /path/to/repo` |
| Specific harnesses | `install --target . --binding claude,cursor` |
| Everything it supports | `install --target . --binding all` |
| See it first | add `--dry-run` |

Only the `claude` and `generic` (AGENTS.md) bindings are verified. Cursor, Windsurf, Codex and
Gemini CLI follow each runtime's documented convention but have not been confirmed against a
live install — preview with `--dry-run`, check the paths against your runtime's current docs,
and correct the JSON in `bindings/` if they differ. That is a one-file change with no code in it.

---

## Updating

```text
Update vince-gate for me.

1. `git pull` in the clone.
2. Run the installer's `install` command against the same scope/target as before — the
   manifest at `.vince/install.json` records what that was.
3. Run `status` afterwards; it must say healthy and exit 0.
4. If the installer refuses because files were edited in place, STOP. That is not an error to
   force past: someone improved a skill at the target and it never made it back to the clone.
   Show me the diff and let me decide. Do not pass --force without asking.
```

By hand:

```bash
cd vince-gate && git pull
python scripts/install.py install --scope user
python scripts/install.py status  --scope user
```

## Repairing

```bash
python scripts/install.py doctor --scope user          # diagnose
python scripts/install.py doctor --scope user --fix    # repair all but in-place edits
```

For the layer above the files — is the *profile* still true, are there ledgers that never got
reviewed, are there leaked worktrees — invoke the `vince-doctor` skill, which validates by
running things rather than by hashing them.

## Uninstalling

```bash
python scripts/install.py uninstall --scope user
```

Removes only what the manifest recorded, then empty directories, then the index block. Anything
you added or edited is left alone unless you pass `--force`.

## If something goes wrong

- **Skills do not appear.** Check the binding's paths against your runtime's docs
  (`install.py bindings`); an `unverified` binding is the usual suspect. Confirm the install
  landed where you think (`install.py status`).
- **The agent ignores the gate.** Skills auto-activate on their description; a terse request may
  not trigger one. Invoke it by name, and add the gate to the project's `CLAUDE.md`/`AGENTS.md` —
  the `generic` binding writes exactly that block for you.
- **Anything else.** [USER-GUIDE.md](USER-GUIDE.md#troubleshooting) has the longer list.
