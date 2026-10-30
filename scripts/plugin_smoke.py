#!/usr/bin/env python3
"""Install a built ZIP in isolation, discover skills and invoke the real packaged stdio tools."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import queue
import signal
import subprocess
import sys
import tempfile
import threading
import time
import zipfile


def run(argv, **kwargs):
    result = subprocess.run(argv, text=True, capture_output=True, timeout=45, **kwargs)
    if result.returncode:
        raise ValueError(f"Command failed ({result.returncode}): {argv[0:3]}\n{result.stderr[-2000:]}\n{result.stdout[-2000:]}")
    return result.stdout


def native_probe(codex, env, project, expected_version, skills):
    """Use the real host's skill scanner, MCP discovery and tool-call API (no model turn)."""
    process = subprocess.Popen([codex, "app-server", "--stdio"], env=env,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, text=True,
                               start_new_session=os.name != "nt")
    messages = queue.Queue()

    def read_output():
        for line in process.stdout:
            try:
                messages.put(json.loads(line))
            except ValueError:
                pass
        messages.put(None)

    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()
    sequence = 0

    def rpc(method, params):
        nonlocal sequence
        sequence += 1
        process.stdin.write(json.dumps({"id": sequence, "method": method, "params": params}) + "\n")
        process.stdin.flush()
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            try:
                item = messages.get(timeout=max(0.01, deadline - time.monotonic()))
            except queue.Empty:
                break
            if item is None:
                break
            if item.get("id") == sequence:
                if "error" in item:
                    raise ValueError(f"Codex {method}: {item['error']}")
                return item["result"]
        raise ValueError("Codex host probe timed out: " + method)

    try:
        rpc("initialize", {"clientInfo": {"name": "vince_release_smoke", "version": "1"},
                           "capabilities": {"experimentalApi": True}})
        process.stdin.write('{"method":"initialized"}\n')
        process.stdin.flush()
        discovered = rpc("skills/list", {"cwds": [str(project)], "forceReload": True})
        serialized = json.dumps(discovered)
        if not all(skill in serialized for skill in skills):
            raise ValueError("Codex host did not discover all bundled Vince skills")
        thread = rpc("thread/start", {"cwd": str(project), "approvalPolicy": "never", "sandbox": "read-only", "ephemeral": True})
        thread_id = thread["thread"]["id"]
        inventory = rpc("mcpServerStatus/list", {"threadId": thread_id})
        servers = inventory.get("data", [])
        server = next((item for item in servers if "vince_plugin_info" in json.dumps(item.get("tools", {}))), None)
        if not server:
            raise ValueError("Codex host did not discover the plugin MCP tools: " + json.dumps(inventory)[:1200])
        called = rpc("mcpServer/tool/call", {"threadId": thread_id, "server": server["name"],
                                              "tool": "vince_plugin_info", "arguments": {}})
        if expected_version not in json.dumps(called) or "vince-review" not in json.dumps(called):
            raise ValueError("Codex host tool invocation returned unexpected plugin info")
        context = rpc("mcpServer/tool/call", {"threadId": thread_id, "server": server["name"],
                                               "tool": "vince_project_context", "arguments": {"repo": str(project)}})
        if str(project) not in json.dumps(context):
            raise ValueError("Codex plugin-server allowed-root environment did not reach the tool: " + json.dumps(context)[:1200] + " info=" + json.dumps(called)[:1200])
        return "PASS (host skill discovery, MCP discovery, plugin-info and allowed project-context calls)"
    finally:
        if process.poll() is None:
            if os.name == "nt":
                process.terminate()
            else:
                os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                if os.name == "nt":
                    process.kill()
                else:
                    os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=3)
        process.stdin.close()
        reader.join(timeout=1)
        process.stdout.close()


def smoke(package, codex=None):
    with tempfile.TemporaryDirectory(prefix="vince-plugin-smoke-") as raw:
        base = Path(raw)
        plugin = base / "plugin"
        with zipfile.ZipFile(package) as archive:
            if sum(item.file_size for item in archive.infolist()) > 32 * 1024 * 1024:
                raise ValueError("Package exceeds smoke-test size limit")
            for item in archive.infolist():
                destination = (plugin / item.filename).resolve()
                if plugin not in destination.parents or (item.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError("Unsafe archive path")
            archive.extractall(plugin)
        manifest = json.loads((plugin / "plugin.json").read_text(encoding="utf-8"))
        skills = sorted(path.parent.name for path in (plugin / "skills").glob("vince-*/SKILL.md"))
        if len(skills) != 11 or "vince-review" not in skills:
            raise ValueError("Expected eleven discoverable Vince skills")
        for name in skills:
            if not (plugin / "skills" / name / "reference/brief.md").is_file():
                raise ValueError("Missing packaged shared reference")
        project = base / "existing-project"
        project.mkdir()
        marker = project / "user-data.txt"
        marker.write_text("preserve this exact user data\n", encoding="utf-8")
        run(["git", "init", "-q", str(project)])
        task = project / "task"
        task.mkdir()
        ledger = task / "verification-ledger.md"
        ledger.write_text("Profile: fixture\nRepo(s): fixture\nBaseline: 1 passed\n"
                          "Reviewer verdict: NOT-RUN\n"
                          "| AC-1 | preserve data | INTEGRATION | test | PROVEN |\n"
                          "## Resume\nNext action: independent review\n", encoding="utf-8")
        original_ledger = ledger.read_bytes()
        env = dict(os.environ, VINCE_ALLOWED_ROOTS=str(project))
        config = json.loads((plugin / "mcp.json").read_text())
        server = config["mcpServers"]["vince"]
        argv = [server["command"], *[arg.replace("${PLUGIN_ROOT}", str(plugin)) for arg in server["args"]]]
        messages = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "vince-smoke", "version": "1"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        ]
        for ident, name, arguments in [(3, "vince_plugin_info", {}),
                                       (4, "vince_project_context", {"repo": str(project)}),
                                       (5, "vince_task_status", {"task": str(task)}),
                                       (6, "vince_validate_task", {"task": str(task)})]:
            messages.append({"jsonrpc": "2.0", "id": ident, "method": "tools/call", "params": {"name": name, "arguments": arguments}})
        stdout = run(argv, input="\n".join(map(json.dumps, messages)) + "\n", env=env)
        replies = {message["id"]: message for message in map(json.loads, stdout.splitlines())}
        if len(replies) != 6 or any("error" in value for value in replies.values()):
            raise ValueError("MCP protocol smoke failed")
        if any(replies[i]["result"].get("isError") for i in range(3, 7)):
            raise ValueError("Packaged tool invocation failed")
        if replies[3]["result"]["structuredContent"]["version"] != manifest["version"]:
            raise ValueError("Loaded plugin version mismatch")
        if marker.read_text(encoding="utf-8") != "preserve this exact user data\n" or ledger.read_bytes() != original_ledger:
            raise ValueError("Read-only smoke changed project data")
        report = {"version": manifest["version"], "skills": skills, "tools": 4,
                  "stdio": "PASS", "project_data": "PRESERVED", "native_codex_install": "NOT-RUN"}
        if codex:
            env["CODEX_HOME"] = str(base / "isolated-codex")
            Path(env["CODEX_HOME"]).mkdir()
            run([codex, "plugin", "marketplace", "add", str(plugin), "--json"], env=env)
            added = run([codex, "plugin", "add", "vince-gate@vince-gate", "--json"], env=env)
            listed = run([codex, "plugin", "list", "--json"], env=env)
            if "vince-gate" not in added or "vince-gate" not in listed:
                raise ValueError("Native plugin installation was not discoverable")
            # Host installation must carry skill files, not only metadata.
            installed = list(Path(env["CODEX_HOME"]).rglob("vince-review/SKILL.md"))
            if not installed:
                raise ValueError("Native plugin cache lacks Vince Review")
            report["native_codex_install"] = "PASS"
            report["native_codex_host"] = native_probe(codex, env, project, manifest["version"], skills)
            if marker.read_text(encoding="utf-8") != "preserve this exact user data\n" or ledger.read_bytes() != original_ledger:
                raise ValueError("Host plugin probe changed project data")
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--codex", help="Additionally verify real Codex plugin installation in isolated CODEX_HOME")
    args = parser.parse_args()
    try:
        report = smoke(args.package, args.codex)
    except (ValueError, OSError, zipfile.BadZipFile, subprocess.SubprocessError) as error:
        sys.stderr.write(str(error) + "\n")
        return 1
    sys.stdout.write(json.dumps(report, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
