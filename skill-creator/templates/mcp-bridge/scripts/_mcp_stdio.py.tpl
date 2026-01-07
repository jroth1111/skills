"""Minimal MCP stdio JSON-RPC client (stdlib-only).

Implements:
- initialize
- notifications/initialized
- tools/list
- tools/call
- ping response (if server pings us)

Notes:
- stdio transport messages are newline-delimited JSON with no embedded newlines.
- server must not write non-JSON to stdout (stderr is for logs).

This is a pragmatic bridge template, not a full client framework.
"""
from __future__ import annotations

import json
import shlex
import subprocess
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, Optional

JSON = Dict[str, Any]


def _dumps(msg: JSON) -> str:
    # No embedded newlines. Compact separators.
    return json.dumps(msg, ensure_ascii=False, separators=(",", ":"))


@dataclass
class McpInitResult:
    protocolVersion: str
    capabilities: Dict[str, Any]
    serverInfo: Dict[str, Any]
    instructions: Optional[str] = None


class McpStdioClient:
    def __init__(
        self,
        command: str,
        *,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout_s: float = 60.0,
        log_stderr: bool = False,
        stderr_tail: int = 200,
    ) -> None:
        self.command = command
        self.cwd = cwd
        self.env = env
        self.timeout_s = timeout_s
        self._log_stderr = log_stderr
        self._stderr_lines: Deque[str] = deque(maxlen=stderr_tail)

        self._proc: Optional[subprocess.Popen[str]] = None
        self._id = 0
        self._lock = threading.Lock()
        self._cv = threading.Condition(self._lock)
        self._responses: Dict[str, JSON] = {}
        self._closed = False

    def start(self) -> None:
        if self._proc is not None:
            return
        args = shlex.split(self.command)
        self._proc = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            cwd=self.cwd,
            env=self.env,
            bufsize=1,
        )
        assert self._proc.stdout and self._proc.stdin

        threading.Thread(target=self._reader_stdout, daemon=True).start()
        threading.Thread(target=self._reader_stderr, daemon=True).start()

    def _reader_stdout(self) -> None:
        assert self._proc and self._proc.stdout
        for line in self._proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except Exception:
                # Protocol violation: ignore
                continue
            self._handle_message(msg)

    def _reader_stderr(self) -> None:
        assert self._proc and self._proc.stderr
        for line in self._proc.stderr:
            # Keep stderr logs out of stdout protocol.
            self._stderr_lines.append(line.rstrip())
            if self._log_stderr:
                print(line.rstrip(), file=sys.stderr)

    def _handle_message(self, msg: JSON) -> None:
        # Response
        if "id" in msg and ("result" in msg or "error" in msg) and "method" not in msg:
            with self._cv:
                self._responses[str(msg["id"])] = msg
                self._cv.notify_all()
            return

        # Server request (has method + id)
        if "method" in msg and "id" in msg:
            method = msg.get("method")
            req_id = msg.get("id")
            if method == "ping":
                self._send({"jsonrpc": "2.0", "id": req_id, "result": {}})
                return
            # Unsupported server request: reply with method not found
            self._send(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not supported by bridge: {method}"},
                }
            )
            return

        # Notification (method without id): ignore by default
        return

    def _send(self, msg: JSON) -> None:
        if self._closed:
            return
        assert self._proc and self._proc.stdin
        payload = _dumps(msg) + "\n"
        self._proc.stdin.write(payload)
        self._proc.stdin.flush()

    def request(self, method: str, params: Optional[JSON] = None) -> JSON:
        with self._lock:
            self._id += 1
            req_id = str(self._id)
        req: JSON = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            req["params"] = params
        self._send(req)
        return self._wait_response(req_id)

    def notify(self, method: str, params: Optional[JSON] = None) -> None:
        msg: JSON = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        self._send(msg)

    def _wait_response(self, req_id: str) -> JSON:
        deadline = time.time() + self.timeout_s
        with self._cv:
            while req_id not in self._responses:
                remaining = deadline - time.time()
                if remaining <= 0:
                    raise TimeoutError(f"Timed out waiting for response id={req_id}")
                self._cv.wait(timeout=min(remaining, 0.25))
            return self._responses.pop(req_id)

    def initialize(self, *, client_name: str = "skill-bridge", client_version: str = "0.1.0", protocol_version: str = "2025-06-18") -> McpInitResult:
        self.start()
        resp = self.request(
            "initialize",
            {
                "protocolVersion": protocol_version,
                "capabilities": {},
                "clientInfo": {"name": client_name, "version": client_version},
            },
        )
        if "error" in resp:
            raise RuntimeError(resp["error"])
        result = resp.get("result") or {}
        self.notify("notifications/initialized")
        return McpInitResult(
            protocolVersion=result.get("protocolVersion", ""),
            capabilities=result.get("capabilities", {}),
            serverInfo=result.get("serverInfo", {}),
            instructions=result.get("instructions"),
        )

    def list_tools(self) -> JSON:
        return self.request("tools/list")

    def call_tool(self, name: str, arguments: JSON) -> JSON:
        return self.request("tools/call", {"name": name, "arguments": arguments})

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if not self._proc:
            return
        try:
            if self._proc.stdin:
                self._proc.stdin.close()
        except Exception:
            pass
        try:
            self._proc.terminate()
        except Exception:
            pass
        try:
            self._proc.wait(timeout=5)
        except Exception:
            try:
                self._proc.kill()
                self._proc.wait(timeout=5)
            except Exception:
                pass
        try:
            if self._proc.stdout:
                self._proc.stdout.close()
            if self._proc.stderr:
                self._proc.stderr.close()
        except Exception:
            pass

    def get_stderr_tail(self) -> list[str]:
        return list(self._stderr_lines)
