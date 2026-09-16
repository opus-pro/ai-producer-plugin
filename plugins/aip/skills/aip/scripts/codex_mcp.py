"""A bounded, fail-closed transport to an explicitly selected Codex MCP server.

This helper only opens Codex's local app-server stdio protocol. It never creates a
Codex turn, invokes a model, approves a host request, or discovers a server.
"""
from __future__ import annotations

import json
from pathlib import Path
import queue
import subprocess
import threading
import time
from typing import Any, Mapping, Union

_ALLOWED_TOOLS = frozenset({
    "get_project",
    "list_workspace",
    "sign_workspace_upload",
    "commit_workspace",
    "get_task",
})
_REQUEST_TIMEOUT_SECONDS = 90
_MESSAGE_QUEUE_MAXSIZE = 8
_STOP = object()


class CodexMcp:
    """Call a small read/publish MCP surface through an ephemeral Codex thread."""

    def __init__(self, server: str, cwd: Union[str, Path], cli: Union[str, None] = None) -> None:
        if not isinstance(server, str) or not server:
            raise ValueError("A nonempty MCP server name is required")
        self.server = server
        self.cwd = str(Path(cwd))
        self.cli = cli or "codex"
        self._messages: queue.Queue[object] = queue.Queue(maxsize=_MESSAGE_QUEUE_MAXSIZE)
        self._reader_overflow = threading.Event()
        self._closed = threading.Event()
        self._pending_id: Union[int, None] = None
        self._proc: Union[subprocess.Popen, None] = None
        self._stdout_thread: Union[threading.Thread, None] = None
        self._stderr_thread: Union[threading.Thread, None] = None
        self._sequence = 0
        self._thread_id: Union[str, None] = None

    def __enter__(self) -> "CodexMcp":
        try:
            self._proc = subprocess.Popen(
                [self.cli, "app-server", "--stdio"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except (OSError, ValueError):
            raise RuntimeError("codex_app_server_unavailable") from None
        assert self._proc.stdin is not None and self._proc.stdout is not None and self._proc.stderr is not None
        self._closed.clear()
        self._reader_overflow.clear()
        self._stdout_thread = threading.Thread(target=self._read_stdout, args=(self._proc.stdout,), daemon=True)
        self._stderr_thread = threading.Thread(target=self._drain_stderr, args=(self._proc.stderr,), daemon=True)
        self._stdout_thread.start()
        self._stderr_thread.start()
        try:
            self._request(
                "initialize",
                {"clientInfo": {"name": "ai-producer-plugin", "version": "1.0.0"}, "capabilities": {"experimentalApi": True}},
            )
            self._notify("initialized", {})
            started = self._request("thread/start", {"cwd": self.cwd, "ephemeral": True})
            thread = started.get("thread") if isinstance(started, Mapping) else None
            thread_id = thread.get("id") if isinstance(thread, Mapping) else None
            if not isinstance(thread_id, str) or not thread_id:
                raise RuntimeError("codex_app_server_invalid_response")
            self._thread_id = thread_id
            return self
        except Exception:
            self.close()
            raise

    def __exit__(self, _type: object, _value: object, _traceback: object) -> None:
        self.close()

    def close(self) -> None:
        """Stop only the app-server process this instance created."""
        proc, self._proc = self._proc, None
        self._thread_id = None
        self._pending_id = None
        self._closed.set()
        if proc is None:
            return
        if proc.stdin is not None:
            try:
                proc.stdin.close()
            except OSError:
                pass
        if proc.poll() is None:
            proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
        for reader in (self._stdout_thread, self._stderr_thread):
            if reader is not None:
                reader.join(timeout=1)
        self._stdout_thread = None
        self._stderr_thread = None

    def call(self, tool: str, arguments: Mapping[str, Any]) -> Any:
        """Call one allowed MCP tool and return its structured JSON payload.

        Signed URLs may be present in a successful in-memory result. All failures use
        fixed messages so server, transport, or tool errors cannot expose credentials.
        """
        if tool not in _ALLOWED_TOOLS:
            raise ValueError("MCP tool is outside the allowed publication surface")
        if not isinstance(arguments, Mapping):
            raise ValueError("MCP tool arguments must be an object")
        if self._proc is None or self._thread_id is None:
            raise RuntimeError("codex_mcp_not_connected")
        try:
            json.dumps(arguments)
        except (TypeError, ValueError):
            raise ValueError("MCP tool arguments must be JSON serializable") from None
        result = self._request(
            "mcpServer/tool/call",
            {"threadId": self._thread_id, "server": self.server, "tool": tool, "arguments": dict(arguments)},
        )
        if not isinstance(result, Mapping) or result.get("isError"):
            raise RuntimeError("codex_mcp_tool_failed")
        structured = result.get("structuredContent")
        if structured is not None:
            if not isinstance(structured, Mapping):
                raise RuntimeError("codex_mcp_invalid_response")
            return dict(structured)
        content = result.get("content")
        if not isinstance(content, list):
            raise RuntimeError("codex_mcp_invalid_response")
        for item in content:
            if isinstance(item, Mapping) and item.get("type") == "text" and isinstance(item.get("text"), str):
                try:
                    payload = json.loads(item["text"])
                except json.JSONDecodeError:
                    raise RuntimeError("codex_mcp_invalid_response") from None
                if isinstance(payload, dict):
                    return payload
                raise RuntimeError("codex_mcp_invalid_response")
        raise RuntimeError("codex_mcp_invalid_response")

    def _read_stdout(self, stream: Any) -> None:
        try:
            for raw in stream:
                if self._closed.is_set():
                    return
                try:
                    message = json.loads(raw)
                except (TypeError, json.JSONDecodeError):
                    continue
                if not isinstance(message, dict):
                    continue
                # Notifications have neither a response payload nor an approval/input
                # request id, and no caller observes them. Drop them before the bounded
                # queue. A serial transport needs only its pending response or a request
                # that must fail closed.
                is_host_request = "id" in message and "method" in message
                is_pending_response = message.get("id") == self._pending_id and (
                    "result" in message or "error" in message
                )
                if is_host_request or is_pending_response:
                    self._put_message(message)
        except OSError:
            pass
        finally:
            self._put_message(_STOP)

    def _put_message(self, message: object) -> None:
        try:
            self._messages.put(message, timeout=0.1)
        except queue.Full:
            # Never block a reader indefinitely. The caller will fail closed rather
            # than treating a potentially lost host request or response as success.
            self._reader_overflow.set()

    @staticmethod
    def _drain_stderr(stream: Any) -> None:
        # app-server diagnostics can include MCP response text. Drain solely to avoid
        # blocking the child; never retain or report it.
        try:
            for _line in stream:
                pass
        except OSError:
            pass

    def _notify(self, method: str, params: Mapping[str, Any]) -> None:
        self._send({"method": method, "params": dict(params)})

    def _request(self, method: str, params: Mapping[str, Any]) -> Any:
        self._sequence += 1
        request_id = self._sequence
        self._pending_id = request_id
        try:
            self._send({"id": request_id, "method": method, "params": dict(params)})
            deadline = time.monotonic() + _REQUEST_TIMEOUT_SECONDS
            while True:
                if self._reader_overflow.is_set():
                    raise RuntimeError("codex_app_server_transport_failed")
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RuntimeError("codex_app_server_timeout")
                try:
                    message = self._messages.get(timeout=remaining)
                except queue.Empty:
                    raise RuntimeError("codex_app_server_timeout") from None
                if message is _STOP:
                    raise RuntimeError("codex_app_server_terminated")
                if not isinstance(message, Mapping):
                    continue
                if "id" in message and "method" in message:
                    # A request can be a permission, an elicitation, or user input. This
                    # transport has no approval path and must leave it unanswered.
                    raise RuntimeError("codex_app_server_host_request")
                if message.get("id") != request_id:
                    continue
                if "error" in message:
                    raise RuntimeError("codex_app_server_request_failed")
                if "result" not in message:
                    raise RuntimeError("codex_app_server_invalid_response")
                return message["result"]
        finally:
            self._pending_id = None

    def _send(self, message: Mapping[str, Any]) -> None:
        proc = self._proc
        if proc is None or proc.stdin is None or proc.poll() is not None:
            raise RuntimeError("codex_app_server_terminated")
        try:
            proc.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
            proc.stdin.flush()
        except (OSError, ValueError, TypeError):
            raise RuntimeError("codex_app_server_transport_failed") from None
