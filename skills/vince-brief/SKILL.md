---
name: vince-brief
description: Keep Vince task updates action-first, concise, and easy to resume. Use after a Vince workflow starts or when the user asks for a shorter, clearer status; do not use to replace evidence or safety decisions.
---

# Vince — Brief

End user-facing updates with three short lines: `Result:`, `Problem:` (omit when none), and `Next:`. Keep detailed evidence in task artifacts, not chat.

Brief mode is persistent for the current Vince task: apply it to every user-facing response until
the user says `normal mode` or `verbose mode`. It is presentation only. Vince evidence, safety,
authorization, and required detail outrank it.

Before the final user-facing response, apply `reference/brief.md`.
Do not load it while reasoning, investigating, or writing task artifacts.
