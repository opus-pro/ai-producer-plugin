import importlib.util
import io
import json
from pathlib import Path
import queue
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "codex_mcp", Path(__file__).resolve().parents[1] / "plugins/aip/skills/aip/scripts/codex_mcp.py"
)
codex_mcp = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(codex_mcp)


class _Input:
    def __init__(self, proc):
        self.proc = proc
        self.closed = False

    def write(self, line):
        request = json.loads(line)
        self.proc.writes.append(request)
        if "id" in request:
            if self.proc.replies:
                self.proc.stdout.feed(self.proc.replies.pop(0))
            else:
                self.proc.stdout.close()
        return len(line)

    def flush(self):
        return None

    def close(self):
        self.closed = True


class _Output:
    def __init__(self):
        self.items = queue.Queue()

    def feed(self, item):
        self.items.put(json.dumps(item) + "\n")

    def close(self):
        self.items.put(None)

    def __iter__(self):
        while True:
            item = self.items.get()
            if item is None:
                return
            yield item


class _Process:
    def __init__(self, replies):
        self.replies = list(replies)
        self.writes = []
        self.stdout = _Output()
        self.stderr = io.StringIO("")
        self.stdin = _Input(self)
        self.code = None
        self.terminated = False
        self.killed = False

    def poll(self):
        return self.code

    def terminate(self):
        self.terminated = True
        self.code = 0
        self.stdout.close()

    def kill(self):
        self.killed = True
        self.code = -9
        self.stdout.close()

    def wait(self, timeout=None):
        return self.code


def _reply(request_id, result):
    return {"id": request_id, "result": result}


def _connected_replies(call_result):
    return [
        _reply(1, {"protocolVersion": "1"}),
        _reply(2, {"thread": {"id": "ephemeral-thread"}}),
        _reply(3, call_result),
    ]


class CodexMcpTests(unittest.TestCase):
    def start(self, replies, cli="codex"):
        self.proc = _Process(replies)
        patcher = patch.object(codex_mcp.subprocess, "Popen", return_value=self.proc)
        patcher.start()
        self.addCleanup(patcher.stop)
        client = codex_mcp.CodexMcp("explicit-aip", "/workspace", cli=cli)
        self.addCleanup(client.close)
        return client.__enter__()

    def test_initializes_ephemeral_thread_and_returns_structured_content(self):
        client = self.start(_connected_replies({"structuredContent": {"project_id": "p"}}))
        self.assertEqual(client.call("get_project", {"project_id": "p"}), {"project_id": "p"})
        client.close()
        self.assertEqual(
            [(row.get("method"), row.get("params")) for row in self.proc.writes],
            [
                ("initialize", {"clientInfo": {"name": "ai-producer-plugin", "version": "1.0.0"}, "capabilities": {"experimentalApi": True}}),
                ("initialized", {}),
                ("thread/start", {"cwd": "/workspace", "ephemeral": True}),
                ("mcpServer/tool/call", {"threadId": "ephemeral-thread", "server": "explicit-aip", "tool": "get_project", "arguments": {"project_id": "p"}}),
            ],
        )
        self.assertTrue(self.proc.terminated)

    def test_parses_text_payload_and_keeps_signed_url_out_of_errors(self):
        signed = "https://storage.test/put?X-Goog-Signature=private"
        client = self.start(_connected_replies({"content": [{"type": "text", "text": json.dumps({"upload_url": signed})}]}))
        self.assertEqual(client.call("sign_workspace_upload", {}), {"upload_url": signed})
        client.close()
        client = self.start(_connected_replies({"isError": True, "content": [{"type": "text", "text": signed}]}))
        with self.assertRaisesRegex(RuntimeError, "codex_mcp_tool_failed") as raised:
            client.call("sign_workspace_upload", {})
        client.close()
        self.assertNotIn("private", str(raised.exception))

    def test_fails_closed_for_host_request_eof_and_disallowed_tools(self):
        client = self.start(_connected_replies({"structuredContent": {}}))
        with self.assertRaisesRegex(ValueError, "allowed publication"):
            client.call("start_transcribe_project", {})
        client.close()
        host = {"id": 3, "method": "permissions/requestApproval", "params": {"secret": "private"}}
        client = self.start([
            _reply(1, {"protocolVersion": "1"}),
            _reply(2, {"thread": {"id": "ephemeral-thread"}}),
            host,
        ])
        with self.assertRaisesRegex(RuntimeError, "codex_app_server_host_request") as raised:
            client.call("get_task", {})
        client.close()
        self.assertNotIn("private", str(raised.exception))
        proc = _Process([_reply(1, {"protocolVersion": "1"})])
        with patch.object(codex_mcp.subprocess, "Popen", return_value=proc):
            with self.assertRaisesRegex(RuntimeError, "codex_app_server_terminated"):
                with codex_mcp.CodexMcp("aip", "/workspace"):
                    pass

    def test_invalid_structured_content_and_timeout_are_safe(self):
        client = self.start(_connected_replies({"structuredContent": ["not", "an", "object"]}))
        with self.assertRaisesRegex(RuntimeError, "codex_mcp_invalid_response"):
            client.call("get_project", {})
        client.close()
        original_timeout = codex_mcp._REQUEST_TIMEOUT_SECONDS
        self.addCleanup(setattr, codex_mcp, "_REQUEST_TIMEOUT_SECONDS", original_timeout)
        self.assertGreaterEqual(original_timeout, 90)
        client = self.start([
            _reply(1, {"protocolVersion": "1"}),
            _reply(2, {"thread": {"id": "ephemeral-thread"}}),
        ])
        codex_mcp._REQUEST_TIMEOUT_SECONDS = 0
        with self.assertRaisesRegex(RuntimeError, "codex_app_server_timeout"):
            client.call("get_task", {})
        client.close()

    def test_unavailable_cli_is_redacted_and_explicit_cli_is_used(self):
        with patch.object(codex_mcp.subprocess, "Popen", side_effect=FileNotFoundError("/private/path")) as popen:
            with self.assertRaisesRegex(RuntimeError, "codex_app_server_unavailable") as raised:
                codex_mcp.CodexMcp("aip", "/workspace", cli="chosen-codex").__enter__()
        popen.assert_called_once()
        self.assertNotIn("private", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
