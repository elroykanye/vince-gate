# Changelog

Versions are git tags. `VERSION` in the working tree names the release; `install.py status`
prints both that and the actual checkout, so a mid-line or modified clone is visible rather than
silently claiming to be a release.

See [INSTALL.md](INSTALL.md#versions) for upgrading, pinning and rolling back.

## v0.4.0 — 2026-08-11

**Added**

- **`vince-update`.** Moves an install between releases, and owns the half `install.py` cannot:
  reading the changelog *between* the installed and target versions, stopping on uncommitted
  toolkit work / in-place edits / a task in flight rather than forcing past them, reinstalling at
  the scope and bindings the manifest recorded, and then **migrating `.vince` config** so a new
  release's fields exist instead of being silently absent. New fields arrive `unknown` or
  `blocked` with what would resolve them - never invented. Rollback is the same flow with an
  older tag, and deliberately does not strip config, since older skills read newer profiles fine.

**Changed**

- The release checklist now requires **actionable upgrade notes** naming every config field or
  section a release adds, because `vince-update` reads them to migrate existing projects.

**Upgrade notes**

No new config fields. `vince-update` itself installs like any other skill; after upgrading, use
it instead of `git pull` + reinstall so config migration happens too.

Workspace profiles, for estates with many repos under one hub. Driven by a real limitation: a
hub cannot run a hundred suites, so a hub-level profile that claims verified commands is lying.

**Added**

- **Two-level profiles.** `<workspace>/.vince/profile.md` carries the repo map, stack
  definitions, branch model, tracker, isolation key, environments and estate-wide gates;
  `<repo>/.vince/profile.md` carries verified commands and the observed baseline.
- **The invariant, stated everywhere it is read: a hub profile cannot verify a command.** Every
  per-stack command in a hub profile is `(inferred, unverified)` by construction, and confidence
  does not survive inheritance.
- **First-touch promotion.** The first task in a repo runs what it inherited, writes that repo's
  profile with the commands that actually worked and the baseline actually observed, and records
  any hub default that was wrong. It costs nothing extra - the task was running them anyway.
- **Merge semantics.** Scalars override; `dod_extras` and `known_traps` are additive and the
  hub's cannot be removed by a repo; lessons are read at both levels and routed by scope.
- **Section status vocabulary**: `verified`, `inferred, unverified`, `unknown - <tried>`,
  `blocked - <what is needed>`. Wire-proof rigs and mutation tooling are usually legitimately
  blocked at onboarding; a blank section reads as nobody thought about it, `blocked` reads as a
  gap with an unblock.
- `vince-setup` gains workspace mode; `vince-doctor` validates both levels and reports hub
  profiles claiming impossible verification, plus repos worked in that never got a profile;
  `vince-learn` routes lessons by scope.
- **Per-repo baselines on multi-repo tasks.** The ledger carries one row per repo in dependency
  order. A suite never run in repo B cannot tell you whether you broke repo B - and a baseline
  taken with an unverified inherited command is now a reviewer FAIL condition.
- `templates/workspace-profile.template.md`.

**Upgrade notes**

Nothing breaks. A single-repo profile keeps working unchanged and needs no `Inherits from`
header. Adopt the hub model by running `vince-setup` at the workspace root; existing repo
profiles are already in the right shape.

## v0.2.1 — 2026-08-11

Version selection. v0.1.0 and v0.2.0 shipped without git tags, so there was no way to install or
roll back to a specific release - only "whatever `main` happens to be". Both are now tagged
retroactively at the commits that were those releases.

**Added**

- Annotated tags `v0.1.0` and `v0.2.0`.
- `install.py` prints the toolkit's git ref beside `VERSION`, so `0.2.1 (v0.2.0-4-gabc-dirty)`
  shows a mid-line or modified clone instead of letting it claim to be a clean release.
- This changelog, and a [Versions](INSTALL.md#versions) section covering what-am-I-running,
  upgrade, pin, roll back, agent-instruction pinning, and holding the Claude Code plugin at a
  tag via `extraKnownMarketplaces` with a `ref`.

## v0.2.0 — 2026-08-11

Makes the review measure rather than judge. Three changes aimed at the same weakness: a review
resting on the model's opinion of work the model just did.

**Added**

- **Blind first pass (`vince-review` Pass 0).** The reviewer derives findings from the diff and
  the original contract *before* opening the ledger, completion doc, commit messages or any prior
  verdict — all of which it now treats as claims, not evidence. The verdict records how many
  findings came blind versus only after. Skipping Pass 0 is a hard FAIL condition.
- **Tool-backed mutation testing.** The profile gains a `mutation` section naming the stack's
  tool and its diff-scoped invocation (StrykerJS/.NET, mutmut, PIT, go-mutesting, cargo-mutants).
  TAMPER and the reviewer's A2 both run it; a mutant surviving on a changed line is a missing
  assertion to kill or waive, and a hard FAIL if neither. Hand mutation remains the fallback.
- **`reviewer_model`.** The profile can name a different model to review with. Fresh context
  breaks the correlation introduced while generating, not the correlation in a model's
  parameters.
- **Claude Code plugin packaging.** `/plugin marketplace add elroykanye/vince-gate`, then
  `/plugin install vince-gate@vince-gate`. Skills arrive namespaced: `/vince-gate:vince-implement`.
- **Opt-in Stop hook** (`hooks/vince_gate_stop.py`) that blocks a session from ending while the
  active ledger has unproven rows or no PASS verdict. Fails open in every ambiguous case.
- **New DoD gate:** new code survives mutation.
- `install.py` reports the toolkit's git ref alongside `VERSION`.

**Changed**

- `--binding auto` now includes `generic` whenever the project has an `AGENTS.md`, rather than
  using it only as a last-resort fallback. Most coding agents read `AGENTS.md`, so it is the
  widest-reach binding available.
- README states the positioning directly: spec-driven frameworks enforce process; this enforces
  evidence.
- The docs are more explicit about limits — independent review still finds a minority of defects
  and barely improves on contextual errors, which is why the wire proof and mutation gate carry
  as much weight as the reviewer.

**Upgrade notes**

Nothing breaks. Existing `.vince/profile.md` files keep working; the new `mutation` and
`reviewer_model` fields are optional and both skills degrade to the previous behaviour without
them. To adopt them, re-run `vince-setup` or add the sections by hand. Reinstall with
`install.py install` against the same scope — the manifest records what that was.

## v0.1.0 — 2026-08-11

First release.

- Six skills: `vince-setup`, `vince-implement`, `vince-review`, `vince-document`,
  `vince-doctor`, `vince-learn`.
- Harness bindings for Claude Code, Cursor, Windsurf, Codex, Gemini CLI and any AGENTS.md
  runtime, rendered from one canonical markdown source. Claude and generic verified.
- `install.py` with install / status / doctor / uninstall / list / bindings, a checksummed
  manifest, drift detection, and refusal to clobber in-place edits.
- Templates for the profile, verification ledger, review verdict, lessons and completion doc.
- Paste-to-your-agent install guide.

Rewritten to be stack-agnostic from a set of skills originally built for one platform.

---

## Releasing

1. Land the work on `main`.
2. Bump `VERSION` **in the same commit as the last change of the line** — in 0.2.0 the bump
   landed last, so three commits carried 0.2.0 features while claiming 0.1.0. `install.py` now
   prints the git ref for exactly this reason, but the bump still belongs with the work.
3. Update this file. **Upgrade notes are not optional and must be actionable**: name every
   config field or section the release adds, because `vince-update` reads them to migrate
   existing projects. "Nothing breaks" is a complete note only when nothing was added.
4. Bump `version` in `.claude-plugin/plugin.json` — plugin users only receive updates when that
   string changes.
5. Tag annotated and push: `git tag -a vX.Y.Z -m "…" && git push origin vX.Y.Z`.
