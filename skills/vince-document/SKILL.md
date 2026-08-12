---
name: vince-document
description: Use when a task is completed or in progress and needs completion documentation written to the task dir as completion-documentation.md, and for publishing that doc to whatever destination the project profile names (wiki, docs site, PR description). Triggers on requests like "document this task", "write completion docs", "create task documentation", "publish the docs", or after finishing implementation work.
---

# Vince — Document

Generate professional completion documentation for an implementation task. Output goes to
`<task dir>/completion-documentation.md` — the same dir that holds the verification ledger
(`<task root>/active/<task-id>/`, or `archive/` if the task has already been swept there).

The local markdown is the source of truth. Anything published elsewhere is a copy.


## Voice

Read `reference/voice.md` and talk that way: friendly and dry, brutally honest about facts, and
never assuming the reader knows the jargon — keep the precise term, add the plain-English
translation. Jokes never carry information, and they switch off entirely for anything
destructive, any security or data finding, and any time you were wrong.
Completion documentation is outward-facing and outlives the branch. Write it plainly; save the personality for telling the user what you wrote.

## Inputs required

```
Task type:      Feature | Enhancement | Bug fix | Technical debt | Research | Integration | Migration
Task ID/name:   <ticket key or short slug>
Description:    full description with acceptance criteria
Implementation: file paths of the key implementation areas
Status:         Completed | In progress | Pending review | Deployed
```

If any of these are missing, ask before proceeding. If the task dir already holds a
`verification-ledger.md`, read it first — the ACs and their proof commands come from there, not
from memory.

## Process

1. **Gather inputs.** Extract task type, description, acceptance criteria, file paths, status.
2. **Consult project knowledge.** Read the profile's `memory` targets for anything that
   constrains how this should be described (recorded decisions, conventions, glossary), plus the
   affected repo's own `CLAUDE.md`/`AGENTS.md`. Load only what the task's scope touches.
3. **Read and trace the implementation.** Read every file at the given locations. Trace imports,
   dependencies and called services. Identify new components, modified components, integration
   points, contracts (API, event, schema) and data changes.
4. **Write the documentation** using the structure below.
5. **Validate.** Every path, snippet, endpoint and table name in the doc must exist as described
   on the branch. Open each one and check. The reviewer's A7 does exactly this, and a doc that
   describes intent as if it were shipped behaviour is a finding.

## Document structure

Include every section that applies. Skip a section that genuinely does not (no DB changes, no
API surface) — but never skip Architecture Overview, Implementation Details or New Components.

```markdown
# <task-id> <Task Title> — Implementation Documentation

## Task overview
Task type, description, status, affected repos/services.

## Requirements
User stories, acceptance criteria (verbatim), business value.

## Technical implementation

### Architecture overview
Mermaid diagram showing the components involved, the data flow, and where the change sits.

### Architecture changes
Table: Component | Before | After

### New components created
Table: Component | File path | Description

### Implementation details
Real code snippets from the files you read. Key logic, not boilerplate.

### Related files and dependencies
Files discovered during tracing, beyond those the user listed.

## Integration points
Contracts touched: API endpoints, events/messages, shared libraries, third-party calls.

## API documentation
Endpoints with method, path, request/response examples, auth requirements.

## Data changes
Tables/collections, schema, indexes, migrations, ownership (which component writes what).

## Testing
What was proven and how — mirror the verification ledger's proof levels and commands.

## Deployment
Build/deploy artifacts, config and environment variables, deploy order across components.

## Performance considerations
Latency impact, caching, data volume, what to watch.

## Security considerations
Authorization checks, permission/role keys, data isolation, secret handling.

## Monitoring and logging
Metrics added, structured log fields, dashboards or alerts that should notice a regression.

## Future enhancements
Deferred work, known limitations, technical debt created.
```

A copy-ready skeleton is at `templates/completion-documentation.template.md` in the Vince toolkit
— its path is recorded as `source` in `.claude/.vince-install.json`. Work from the structure
above if it is not there.

## Diagram standards

All diagrams use Mermaid:

- `flowchart LR` / `flowchart TD` for architecture
- `sequenceDiagram` for request and message flows
- `erDiagram` for data schemas
- `classDiagram` for object structures
- `stateDiagram-v2` for state machines

## Formatting standards

- Clean, plain, professional. No emojis.
- Real code snippets from actual files, never pseudocode.
- Portable markdown — it may be pasted into a wiki, a PR body, or a docs site.
- Tables for structured comparisons (before/after, component lists).
- Absolute claims need the command that backs them, same as everywhere else in this toolkit.

## Task type specializations

| Task type | Extra focus |
|-----------|------------|
| Feature | User stories, feature flags, new UI, rollout plan |
| Enhancement | Before/after comparison, measured performance delta |
| Bug fix | Root cause analysis, reproduction steps, regression prevention |
| Technical debt | What got simpler, what it unblocks, remaining debt |
| Research | Findings, options considered, recommendation, proof of concept |
| Integration | Auth flow, data mapping, retry/failure handling, sequence diagram |
| Migration | Data volumes, cutover plan, rollback path, backwards compatibility window |

## Publishing

The profile's `docs_destination` decides where (and whether) this gets published — a wiki space,
a docs-site path, a PR description, or nothing at all. Follow it; do not invent a destination.

Sequence and boundaries:

1. Write and validate the local `completion-documentation.md` first.
2. Publish only after `vince-review` returns PASS. Anything outward-facing outlives the branch,
   so it should not describe unverified work.
3. Confirm with the user before publishing. Creating or updating a shared page is not a local
   edit.
4. If the profile names a dedicated publishing skill or script, use it rather than hand-driving
   an MCP or API — it owns the space/folder IDs, the title convention and the backlink pattern,
   and bypassing it produces orphan pages in the wrong place.
5. After publishing, verify the link actually landed (fetch it, or check the backlink on the
   ticket). "Filed" without a verified link is an unproven claim.

## Common mistakes

| Mistake | Fix |
|---------|-----|
| Publishing before review passed | Local doc first, `vince-review` PASS, then publish |
| Publishing by hand when the project has a publishing skill | Use the skill the profile names |
| Skipping the project knowledge lookup | Read the profile's memory targets first |
| Generic architecture diagram | Show the actual components and data flow from this implementation |
| Pseudocode instead of real snippets | Read and quote the actual implementation |
| Missing data isolation section | Any task touching data documents how the isolation key is handled |
| No before/after for changes | The architecture changes table must show what changed |
| Writing to the wrong path | Always the task dir that holds the verification ledger |
| Describing intent as shipped behaviour | Verify every claim against the branch before saving |
