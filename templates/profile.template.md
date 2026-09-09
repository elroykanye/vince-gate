<!-- vince-profile: compact-v1; budget: 12000 chars -->
# Vince profile — <project>

repo: `<path>` | key: `<install.py where key>` | stored: `<store|in-repo>`
inherits: `<workspace profile|none — standalone repo>`

RULE: verified facts or explicit differences only. Use `(inferred, unverified)`,
`unknown — <attempt>`, or `blocked — <need>`; never guess or leave meaningful fields blank.
RULE: inherited scalars may be overridden; inherited `dod_extras` and `known_traps` are additive.

## Project
- root: `<path>` | stack: `<stack>` | shape: `<single|monorepo|polyrepo member>`
- siblings: `<paths and dependency order|none>`

## Commands
| purpose | command | proof/status |
|---|---|---|
| install | | |
| build | | |
| unit | | `<passed/failed/skipped, commit>` |
| integration | | |
| e2e | | |
| lint/format/types | | |
| locale parity | | |
| run local | | |
| mutation (diff) | | `<tool|manual>` |

## Delivery
- integration branch: `<name>` | branch pattern: `<pattern>`
- PR: `<host/target|none>` | commits: `<convention|none>` | AI trailers: `not allowed`
- version: `<file and rule|not required>` | checkpoints: `<off|suggest|insist>`
- voice: `<terse|plain|playful>`

## Model routing
- maximum verification age: `30 days`

RULE: exact harness-local IDs only. Verify availability; mark unchecked rows unverified. Use
economy for bounded micro-tasks and frontier for ambiguous/security/multi-file work.

| harness | economy | balanced | frontier | reviewer | verification |
|---|---|---|---|---|---|
| claude | | | | | |
| codex | | | | | |
| cursor | | | | | |
| gemini | | | | | |
| generic | | | | | |
| windsurf | | | | | |

| harness | explorer | worker | reviewer | verification |
|---|---|---|---|---|
| claude | | | | |
| codex | | | | |
| cursor | | | | |
| gemini | | | | |
| generic | | | | |
| windsurf | | | | |

## Tracker and tasks
- tracker/key/read: `<system> | <pattern> | <method>`
- task root: `<path>` | committed: `<yes|no>`

## Security
- isolation: `<key|none>` | enforced: `<where>`
- auth: `<model>` | roles: `<path>` | datastores: `<owner mapping>`

## Frontend
- locales/path: `<values>` | breakpoints: `<values>` | runner: `<value>`
- live URL: `<url>` | credentials: `<location, never value>`

## Wire proof
| change | verified rig or blocked reason |
|---|---|
| HTTP API | |
| async/queue | |
| background job | |
| CLI/library | |
| frontend | |
| migration | |
| infra/config | |

## Environments
| name | access | shared/read-only |
|---|---|---|
| local | | no |
| dev | | yes |
| prod | | yes |

## Memory and docs
- decisions: `<path>` | runbooks: `<path>` | conventions: `<path>`
- docs destination: `<destination/tool|none>`

## Extra DoD gates
| gate | verify | pass condition |
|---|---|---|
| | | |

## Known traps
- `<imperative rule> | source=<task(s)> | gate=<check|none>`

## Corrections
- `<date> | WAS=<wrong> | NOW=<truth> | PROOF=<command/result>`

## Tier overrides
- `<scope> | tier=<T1|T2|T3> | reason=<short>`
