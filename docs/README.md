# Vince documentation

New here? Start with the [user guide](../USER-GUIDE.md) — install, first project, reading a
verdict, and what to do when it says FAIL.

- [methodology.md](methodology.md) — why the method is shaped this way, and the failure mode each
  rule exists to stop. Read this if you are deciding whether to adopt it.
- [skills.md](skills.md) — the six skills, their phases and attack passes, and the handoff
  contract between implementer and reviewer.
- [profile.md](profile.md) — `.vince/profile.md`: every field, who reads it, how to keep it true.
- [harnesses.md](harnesses.md) — the binding model: how the same skills render for Claude Code,
  Cursor, Windsurf, Codex, Gemini CLI or any AGENTS.md runtime, and how to add one.
- [install.md](install.md) — install, update, drift detection, repair and uninstall.

Quick start:

```bash
python ../scripts/install.py install --scope user   # available in every project
```

then `/vince-setup` once in a project, and `/vince-implement` for every task after.
