# Harnesses and bindings

The skills are plain markdown with two frontmatter fields. A **binding** is a small JSON file
saying how one harness wants that markdown on disk. `install.py` reads the binding and renders
the canonical skill into the runtime's native shape — deterministically, so every installed byte
can be checked against its source later.

Nothing in a skill body is harness-specific. Where a skill needs a capability (a browser, a
subagent, symbol navigation) it names the capability and gives examples, then leaves the
substitution to the runtime.

## Shipped bindings

| Binding | Harness | Installs to | Shape | Status |
|---------|---------|-------------|-------|--------|
| `claude` | Claude Code | `.claude/skills/<skill>/SKILL.md` | dir per skill, YAML frontmatter | **verified** |
| `generic` | Any AGENTS.md runtime | `.agents/vince/<skill>/SKILL.md` + `AGENTS.md` block | dir per skill, no frontmatter | **verified** |
| `cursor` | Cursor | `.cursor/rules/<skill>.mdc` | flat, MDC frontmatter (`alwaysApply: false`) | unverified |
| `windsurf` | Windsurf | `.windsurf/rules/<skill>.md` | flat, `trigger: model_decision` | unverified |
| `codex` | Codex CLI | `.codex/vince/<skill>/SKILL.md` + `AGENTS.md` block | dir per skill, no frontmatter | unverified |
| `gemini` | Gemini CLI | `.gemini/commands/vince/<skill>.toml` | flat, TOML command (`description` + `prompt`) | unverified |

**`verified`** means installed and confirmed working on a real runtime. **`unverified`** means
the paths follow that runtime's documented convention but were not confirmed against a live
install — preview with `--dry-run`, check against your runtime's current docs, and correct the
JSON if they differ. Correcting a binding is editing one small file; there is no code to change.

## Choosing bindings

```bash
python scripts/install.py install --target .                      # auto-detect (default)
python scripts/install.py install --target . --binding claude,cursor
python scripts/install.py install --target . --binding all
python scripts/install.py install --scope user                    # home dirs, no repo footprint
```

`auto` looks for each binding's marker directory (`.claude/`, `.cursor/`, …) at the target. If a
target already has installs recorded, `auto` refreshes exactly those. If nothing is detected it
falls back to `generic`, which works anywhere.

Bindings with no `user_dir` (Cursor, Windsurf — their rules are per-project) are skipped with a
note under `--scope user`.

## The two layouts

**`dir`** — one directory per skill, `SKILL.md` inside, `reference/` subdirectory carried over
untouched. Links inside the skill are unchanged.

**`flat`** — one file per skill in a shared rules directory. Reference docs become siblings named
`<skill>-<ref>.md`, and every `reference/<x>.md` link in the text is rewritten to match, so the
skill still resolves its own references. Reference docs are always plain markdown regardless of
the binding's frontmatter dialect — only the skill entry gets the native format.

## Frontmatter dialects

| Dialect | Rendered as |
|---------|-------------|
| `yaml` | `name` + `description`, unchanged from the source |
| `mdc` | `description`, `globs`, `alwaysApply: false` |
| `windsurf` | `trigger: model_decision`, `description` |
| `toml-command` | `description = "…"` and `prompt = """…"""` |
| `none` | frontmatter stripped, description kept as a lead blockquote so it stays discoverable |

## Index blocks

A binding may name an `index` file (`AGENTS.md`, `GEMINI.md`). The installer writes a delimited
block into it:

```markdown
<!-- BEGIN vince -->
## Vince — implementer and reviewer (not optional)
…the gate, in plain language, plus a table of skills and where they live…
<!-- END vince -->
```

One block per index file, covering **every** installed binding that shares it — several harnesses
read `AGENTS.md`, and they get one merged block rather than four. Rewriting is idempotent
(replace between markers), uninstalling one binding rewrites the block for what remains, and
uninstalling the last one strips the block and removes the file if nothing else was in it.

Index blocks are project scope only; they are skipped for user-scope installs.

## Adding a harness

Copy the closest existing binding and edit it:

```json
{
  "id": "myharness",
  "label": "My Harness",
  "status": "unverified",
  "detect": [".myharness"],
  "project_dir": ".myharness/skills",
  "user_dir": "~/.myharness/skills",
  "layout": "dir",
  "entry": "SKILL.md",
  "frontmatter": "none",
  "index": "AGENTS.md",
  "invocation": "/{skill}",
  "notes": "What is verified, what is assumed."
}
```

| Field | Meaning |
|-------|---------|
| `detect` | paths whose presence at a target means this harness is in use (`auto`) |
| `project_dir` / `user_dir` | where skills go; `user_dir: null` if the harness has no user scope |
| `layout` | `dir` or `flat` |
| `entry` / `extension` / `prefix` | filename shape for that layout |
| `frontmatter` | one of the dialects above |
| `index` | index file to write the pointer block into, or `null` |
| `invocation` | how a user invokes a skill; `{skill}` is substituted |

Then verify honestly:

```bash
python scripts/install.py install --target /tmp/probe --binding myharness --dry-run
python scripts/install.py install --target /tmp/probe --binding myharness
python scripts/install.py doctor  --target /tmp/probe
```

Open the rendered files, start the runtime against that directory, and confirm the skills are
discovered and invocable. Only then change `status` to `verified` — the status field is a claim
about reality, and an overstated one wastes somebody's afternoon.

If a dialect genuinely cannot be expressed by the existing options, add a branch to
`render_entry()` in `scripts/install.py`. That function is the entire rendering surface.
