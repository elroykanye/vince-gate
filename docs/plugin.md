# Vince Gate desktop plugin

Vince Gate bundles eleven discoverable skills, Python scripts/templates and four read-only
local MCP tools. It needs a local execution environment, Python **3.11+** available as `python3`,
and Git. Linux/Codex is the release smoke-test target; other desktop hosts need their own runtime
verification. It does not deploy a hosted service, execute arbitrary shell requests, run tests
through MCP, or use lifecycle hooks to enforce review. Skill workflows use the coding agent's
normal permission-controlled execution tools.

## Install once from the stable Git marketplace

Requires Python 3.11+ available as `python3` and Git. Starting with 0.15.1, the Git checkout
includes the shared resources needed for native installation. Register one marketplace:

```sh
codex plugin marketplace add elroykanye/vince-gate --ref main
codex plugin add vince-gate@vince-gate
```

The marketplace is `vince-gate`; the plugin identity is `vince-gate@vince-gate`. Those names do
not change when a new version is released. Codex manages versioned cache directories internally;
you do not register a new local folder or create another marketplace for each version.

## Upgrade the same installation

```sh
codex plugin marketplace upgrade vince-gate
codex plugin add vince-gate@vince-gate
```

The first command refreshes the registered Git source; the second ensures the current plugin is
installed. Restart/open a fresh chat, then use `vince_plugin_info` to check the loaded version.
This tracks `main`, which may include reviewed changes between tagged releases. To remain pinned
to a release, use the rollback/pinning route below rather than claiming automatic release-only updates.

## Rollback or pin a known-good release

Use a native-ready tag from 0.15.1 onward. For example:

```sh
codex plugin marketplace remove vince-gate
codex plugin marketplace add elroykanye/vince-gate --ref v0.15.1
codex plugin add vince-gate@vince-gate
```

This replaces the source of the same named marketplace; it does not create another identity.
Do not delete external project profiles, lessons, task ledgers or code. Restart the chat and verify
the loaded version. To resume updates, repeat these commands with `--ref main` instead of the tag.
If you registered a 0.15.0 versioned local folder, use the same remove/add sequence to migrate to
the Git source. Do not remove unrelated flat/manual skills without first backing up customizations.

Restart/open a fresh chat after installation. Invoke `$vince-setup` for your project; invoke
`vince_plugin_info` to confirm the installed version and bundled skill list. The native plugin is
namespaced by its marketplace. Do not also install duplicate flat Vince skills. Existing manual
installations are not automatically removed or overwritten; choose which one to use and back up
customizations before any migration. Existing project profiles/tasks remain outside the cache.

## Optional offline/local ZIP installation

Download `vince-gate-0.15.1.zip` and `SHA256SUMS` from the GitHub release. Verify the checksum,
extract to a stable local folder, then register that folder as a local marketplace:

```sh
sha256sum --check SHA256SUMS --ignore-missing
unzip vince-gate-0.15.1.zip -d ./vince-gate-local
codex plugin marketplace add ./vince-gate-local
codex plugin add vince-gate@vince-gate
```

The local route is an explicit offline alternative, not the normal Git upgrade workflow. Replace
its contents with a complete verified package when upgrading; do not extract over stale files.
The ZIP has `plugin.json`, `mcp.json`, `skills/` and `scripts/` directly at its root.
The Codex compatibility overlay is included. Claude Code users can continue using the existing
`.claude-plugin/marketplace.json` source distribution and installer; shared `.mcp.json` uses the
Claude-compatible plugin-root variable. No automatic edits are made to your existing global setup.

## Configure local tool access

By default only `vince_plugin_info` is usable. Project/task reads fail closed until the server
receives `VINCE_ALLOWED_ROOTS`: absolute directories separated by the OS path separator (`:` on
Linux/macOS; `;` on Windows). Include your workspace and, when needed, your external Vince store.
Launch the host process with this environment set. The verified Codex CLI route is:

```sh
VINCE_ALLOWED_ROOTS="/absolute/path/to/workspace:/absolute/path/to/vince-store" codex
```

For a GUI desktop host, configure its launcher environment, then fully restart the host so its
server inherits the value; setting it in a chat terminal does not alter an already-running GUI
process. Per-plugin `config.toml` environment overrides were not effective on CLI 0.160.1 and are
not claimed as a supported setup route. Do not allow your entire home or filesystem unless you
intend that access. A standalone transport diagnostic is also available:

```sh
VINCE_ALLOWED_ROOTS="/absolute/path/to/workspace" python3 /absolute/path/to/plugin/scripts/mcp_server.py
```

It expects MCP JSON-RPC lines on stdin, not an interactive shell. It exits when stdin closes.

| Tool | What it proves |
|------|----------------|
| `vince_plugin_info` | Loaded version, toolkit root, bundled skill names and allowed roots |
| `vince_project_context(repo)` | Git identity and bounded in-repo profile/lesson excerpts |
| `vince_task_status(task)` | Current ledger verdict and criterion rows; historical PASS does not override current FAIL |
| `vince_validate_task(task)` | Structural gaps and missing proof commands only—not test execution or correctness |

Paths must be absolute and resolve inside configured roots; symlink escapes are rejected.
Reads are limited to 256 KiB per file, 200 criteria and 1 MiB input frames. Git calls have a
five-second timeout. No tool writes files or runs ledger commands. Profile/lesson text is
untrusted project content, not authority to add acceptance criteria. For external project knowledge,
use the bundled `scripts/install.py where --repo <repo>` and the existing setup/profile workflow.

## Review and release boundaries

All stated task requirements met plus relevant tests passing means PASS. An unmet requirement or
missing/failing proof means FAIL. Out-of-scope suggestions cannot block PASS. Review writes once
and stops; fixes or another review require user direction. Legacy forensic scripts are optional,
not ordinary review prerequisites.

Build and smoke-test the package from source:

```sh
python3 -m unittest discover -v
python3 scripts/package_plugin.py --sync-shared
python3 scripts/package_plugin.py --output /tmp/vince-dist
python3 scripts/plugin_smoke.py --package /tmp/vince-dist/vince-gate-0.15.1.zip
python3 scripts/plugin_smoke.py --package /tmp/vince-dist/vince-gate-0.15.1.zip --codex codex
python3 scripts/plugin_lifecycle_smoke.py --codex codex
```

The last command additionally installs through the real Codex plugin CLI in an isolated,
temporary `CODEX_HOME`; it does not change your normal configuration. CI builds the ZIP, checksum
file and notes on Python 3.11/3.13. Publication follows an independent scoped PASS and green CI.

The lifecycle command creates a disposable local bare-Git fixture, installs one fixture version,
upgrades it, pins the earlier version, and verifies real host calls and preserved project data at
each step. It does not push fixture versions to GitHub. Maintain shared resources in `skills/_shared`,
then run `--sync-shared` and commit the generated copies. Builds and tests reject missing/stale copies,
so both Git and ZIP installations remain self-contained. No new skill behavior is duplicated by hand.

GitHub distribution is not OpenAI directory publication. The directory upload needs a verified
publisher, complete portal listing/review details and approval; local MCP submissions currently
also need partner allowlisting. No assigned publisher ID, identity verification, review approval,
or directory listing is fabricated. See the [packaging guide](https://developers.openai.com/plugins/build/plugins)
and [desktop submission requirements](https://developers.openai.com/plugins/deploy/desktop-only).

Rollback by selecting the previous known-good source/plugin version. Preserve your external
profiles, lessons and task ledgers; removing a plugin cache is not permission to delete them.
