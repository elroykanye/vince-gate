# Vince Gate local-tool data handling

Vince Gate 0.15.0 is MIT-licensed local developer tooling. Its bundled MCP server does not run
a hosted service, contact a Vince-operated endpoint, collect analytics, or maintain a user account.
It reads only the project/task paths permitted by the user's configured workspace roots, plus
its own packaged version/skill metadata. It returns Git identity, bounded project knowledge,
and task ledger information to the AI host that invoked the tool. It does not execute ledger
commands or modify project profiles, code or task ledgers.

Tool results are visible to the AI host and may be processed or retained under that host's own
settings and policies. Configure roots narrowly and do not put credentials or sensitive data in
profiles/ledgers that you do not want returned to the host. The plugin does not redact arbitrary
project text. Removing a plugin does not delete external project knowledge or task data.

The coding agent may separately execute Vince's scripts or edit files when the user authorizes
work through its normal execution tools. Those operations are distinct from the read-only MCP
tools. GitHub distribution and issue reports are governed by GitHub's own service policies; avoid
posting private project data or credentials in public support issues.

Source and support: https://github.com/elroykanye/vince-gate and its issue tracker.
