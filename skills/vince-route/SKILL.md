---
name: vince-route
description: Choose the least expensive capable model and narrowest useful agent role for an implementation task using exact harness-specific mappings from the project profile. Use before implementation planning, delegation, or review; recommend a user-visible model switch when warranted without weakening verification.
---

# Vince — Route

Choose enough intelligence for the work and no more. Token economy changes the model, context,
and delegation shape; it never removes required evidence.

Read the active harness row under **Model routing** in the project profile. Exact model identifiers
and exact harness agent types belong in the project profile, not this skill. Provider catalogs
change faster than Vince releases.

## Deterministic mapping lookup

The AI selects only the semantic class and role. It must not transcribe or construct identifiers.
The host gate or agent tool layer resolves the profile with `install.py where`, then runs the
resolver shipped beside this installed skill (the installer rewrites this relative path for
flat-layout harnesses):

```bash
python reference/route.py --profile <resolved-profile> --harness <active-harness> --class <class> --role <role>
```

Use the JSON `model` and `agent` values verbatim. Exit 2 or JSON status `ASK` stops routing and is
shown to the user. Do not turn it into `READY`. This deterministic lookup is required even when the
table looks easy to read; it prevents provider-like identifiers from being invented by analogy.
If the model's own sandbox cannot launch the helper, the host runs it and supplies the exact JSON to
the model. A sandbox failure without host lookup returns `ASK`; it never permits manual fallback.

## Output

Return one compact routing decision before implementation planning:

```text
ROUTE: <READY | SWITCH | ASK>
CLASS: <economy | balanced | frontier | reviewer>
MODEL: <exact model from the active harness profile row>
AGENT: <none | explorer | worker | reviewer> -> <exact harness agent type, if mapped>
WHY: <one sentence: complexity, risk, and token tradeoff>
```

- `READY`: the current model is the exact mapped model, or the harness cannot expose the current
  model and the recommendation has been stated honestly.
- `SWITCH`: the current model is known and is materially too expensive or too weak. Recommend the
  exact mapped model and tell the user how quality, latency, or token cost changes. A recommendation
  is not an automatic switch. Never claim Vince changed the model unless the harness confirms it.
- `ASK`: the active harness row, required class, exact model, or agent mapping is missing, stale,
  unavailable, or marked unverified for the intended use. Ask the user to select or refresh it.
  Do not substitute another model silently.

## Model class

Use the lowest class that safely covers the hardest judgement in the next phase:

| Class | Use for |
|-------|---------|
| `economy` | file discovery, deterministic searches, formatting, mechanical checks, bounded documentation edits, and T1 work |
| `balanced` | ordinary T2 implementation, contained debugging, tests, and routine refactors |
| `frontier` | architecture, T3 planning, security or data isolation, migrations, concurrency, ambiguous failures, and cross-repo reasoning |
| `reviewer` | fresh adversarial review; use the separately mapped reviewer model even when it equals another class |

Do not route an entire task at the class needed for one short phase. Re-evaluate at phase boundaries
and recommend switching down after the difficult judgement is complete.

## Fast lane and full-model handoff

When the active harness exposes both a low-latency coding model and a full reasoning model, use a
two-model workflow instead of keeping the full model on mechanical work:

1. Route bounded searches, precise single-file edits, formatting, and other micro-tasks to the
   verified `economy` fast lane.
2. Handoff architecture, ambiguous debugging, security decisions, and broad multi-file work to the
   verified `frontier` model before that reasoning begins.
3. Switch back down at the next mechanical phase boundary when the interruption is worth the saving.

Fast models may optimize for responsiveness and omit work a larger agent would volunteer. Vince must
explicitly run every required test and proof after their edits. Never infer a fast/full pair from a
provider family name: setup must verify availability in the active account and harness, including
preview access, context or modality limits, and rate limits. If either side is unavailable, use
`ASK`; do not invent a substitute or pretend the handoff occurred.

## Agent role

Choose the smallest capable role:

| Role | Use for |
|------|---------|
| `none` | the main agent can finish with a few bounded tool calls |
| `explorer` | a read-only, well-scoped codebase question whose answer prevents broad context loading |
| `worker` | an independent implementation slice with explicit file ownership |
| `reviewer` | the mandatory fresh-context Vince review |

Do not spawn an agent merely to appear parallel, repeat context the main agent already loaded, or
perform work cheaper than the handoff. Multiple agents are justified only when independent work can
run concurrently or fresh context is itself the requirement. Map the semantic role to the exact
agent type supported by the active harness profile. Copy the exact agent identifier verbatim from
the agent-role table; never derive it from a model identifier, role label, provider naming pattern,
or another table. Use `ASK` when the required mapping is absent.

## Non-negotiable floor

Do not weaken contract confirmation, RED/GREEN/TAMPER, full regression, wire proof, definition-of-
done gates, or independent review to save tokens. If the affordable mapped model cannot perform a
required proof reliably, recommend the next capable mapped class and explain why.

Keep the recommendation proportional. Do not ask the user to switch when the expected saving or
quality improvement is trivial compared with the interruption. When no switch or subagent is useful,
say so in the compact route block and continue.
