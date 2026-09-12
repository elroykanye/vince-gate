# Vince brief

Use this only before the final user-facing response. It applies for the current Vince task unless
the user says `normal mode` or `verbose mode`. It shapes presentation; it does not limit analysis,
evidence, safety checks, or task artifacts.

- Start with `Result:` (or the immediate safe action when one is required).
- Add `State:` only for ongoing multi-step work. Use a numbered list only when more than one user
  action remains; show at most five visible items.
- Add `Problem:` only for a real failure, blocker, or uncertainty. Do not invent a cause: say
  `unknown` and name the next diagnostic when evidence does not establish one.
- End with `Next:` and exactly one concrete action when work remains. Do not add a recap, tangent,
  promise, or closing pleasantry.

The user explicitly asks for detail: give the detail in skimmable sections. For destructive work,
real ambiguity, authorization limits, or a rule that fights the task, safety and task correctness
win over this format.
