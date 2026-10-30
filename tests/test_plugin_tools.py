"""Exercise the shipped stdio entry point, not mocked tool handlers."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def exchange(root, messages, allowed=()):
    env = dict(os.environ, VINCE_ALLOWED_ROOTS=os.pathsep.join(map(str, allowed)))
    run = subprocess.run(
        [sys.executable, str(root / "scripts" / "mcp_server.py")],
        input="\n".join(json.dumps(m) for m in messages) + "\n",
        text=True, capture_output=True, timeout=15, env=env,
    )
    if run.returncode:
        raise AssertionError(run.stderr)
    return [json.loads(line) for line in run.stdout.splitlines()]


def request(method, params=None, ident=1):
    return {"jsonrpc": "2.0", "id": ident, "method": method, "params": {} if params is None else params}


def call(name, arguments=None, ident=1):
    return request("tools/call", {"name": name, "arguments": arguments or {}}, ident)


class PluginToolsTests(unittest.TestCase):
    def test_initialize_discovery_and_info(self):
        replies = exchange(ROOT, [
            request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                   "clientInfo": {"name": "fixture", "version": "1"}}),
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            request("tools/list", ident=2), call("vince_plugin_info", ident=3),
        ])
        self.assertEqual(3, len(replies))
        self.assertEqual("2024-11-05", replies[0]["result"]["protocolVersion"])
        tools = replies[1]["result"]["tools"]
        self.assertEqual({"vince_plugin_info", "vince_project_context", "vince_task_status",
                          "vince_validate_task"}, {t["name"] for t in tools})
        self.assertTrue(all(t["annotations"]["readOnlyHint"] for t in tools))
        info = replies[2]["result"]["structuredContent"]
        self.assertEqual("0.15.0", info["version"])
        self.assertIn("vince-review", info["skills"])

    def test_context_and_status_are_read_only_and_current(self):
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            repo = base / "project"
            repo.mkdir()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            task = base / "task"
            task.mkdir()
            ledger = task / "verification-ledger.md"
            ledger.write_text("Profile: fixture\nRepo(s): fixture\nBaseline: 1 passed\n"
                              "Reviewer verdict: FAIL\n"
                              "| AC-1 | add | UNIT | test | PROVEN |\n"
                              "## Resume\nNext action: ask user\n"
                              "## Review history\nReviewer verdict: PASS\n", encoding="utf-8")
            original = ledger.read_bytes()
            replies = exchange(ROOT, [call("vince_project_context", {"repo": str(repo)}),
                                     call("vince_task_status", {"task": str(task)}, 2),
                                     call("vince_validate_task", {"task": str(task)}, 3)], [base])
            self.assertEqual(str(repo.resolve()), replies[0]["result"]["structuredContent"]["repo"])
            status = replies[1]["result"]["structuredContent"]
            self.assertEqual("FAIL", status["reviewer_verdict"])
            self.assertEqual(1, len(status["criteria"]))
            self.assertEqual([], replies[2]["result"]["structuredContent"]["gaps"])
            self.assertEqual(original, ledger.read_bytes())
            self.assertEqual([ledger], list(task.iterdir()))

    def test_boundaries_and_invalid_calls_are_deliberate_errors(self):
        with tempfile.TemporaryDirectory() as raw, tempfile.TemporaryDirectory() as outside:
            base = Path(raw)
            (Path(outside) / "verification-ledger.md").write_text(
                "Reviewer verdict: FAIL\nprivate outside-workspace fixture\n", encoding="utf-8"
            )
            (base / "escape").symlink_to(outside, target_is_directory=True)
            inside = base / "inside"
            inside.mkdir()
            (inside / "verification-ledger.md").symlink_to(Path(outside) / "verification-ledger.md")
            messages = [call("vince_task_status", {"task": outside}),
                        call("vince_task_status", {"task": str(base / "escape")}, 2),
                        call("vince_task_status", {"task": 42}, 3),
                        call("vince_plugin_info", {"command": "echo forbidden"}, 4),
                        call("execute", {"command": "echo forbidden"}, 5),
                        call("vince_task_status", {"task": str(inside)}, 6)]
            for reply in exchange(ROOT, messages, [base]):
                self.assertTrue(reply["result"]["isError"])
                self.assertNotIn("Traceback", str(reply))
            denied = exchange(ROOT, [call("vince_task_status", {"task": str(base)})])
            self.assertTrue(denied[0]["result"]["isError"])

    def test_missing_malformed_and_oversize_inputs_do_not_crash(self):
        with tempfile.TemporaryDirectory() as raw:
            task = Path(raw)
            missing = exchange(ROOT, [call("vince_task_status", {"task": raw})], [task])
            self.assertTrue(missing[0]["result"]["isError"])
            (task / "verification-ledger.md").write_text("x" * 300000, encoding="utf-8")
            large = exchange(ROOT, [call("vince_validate_task", {"task": raw})], [task])
            self.assertTrue(large[0]["result"]["isError"])
        malformed = exchange(ROOT, [[], request("not/a/method"), request("tools/call", [])])
        self.assertTrue(all("error" in reply for reply in malformed))


if __name__ == "__main__":
    unittest.main()
