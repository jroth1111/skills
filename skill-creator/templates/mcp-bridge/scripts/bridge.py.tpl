#!/usr/bin/env python3
"""MCP Bridge archetype for {{SKILL_NAME}}.

Use when you must use an MCP server (auth/network boundary), but still want:
- orchestration in code (loops/retries/batching)
- filesystem-based artifacts
- minimal context flooding

This script:
- spawns an MCP server via stdio
- initializes session
- calls a tool with JSON args
- saves the raw result to workspace/
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime

from _fs import write_json, safe_preview_json
from _mcp_stdio import McpStdioClient


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", required=True, help="Server command, e.g. 'uvx some-mcp-server@latest' or 'node server.js'")
    ap.add_argument("--tool", required=True, help="Tool name to call (after discovery)")
    ap.add_argument("--args", default="{}", help="JSON string of tool arguments")
    ap.add_argument("--list-tools", action="store_true", help="List tools and exit")
    args = ap.parse_args()

    client = McpStdioClient(args.server)

    init = client.initialize(client_name="{{SKILL_NAME}}-bridge", client_version="0.1.0")
    print(f"Connected to server: {init.serverInfo.get('name','?')} protocol={init.protocolVersion}")

    if args.list_tools:
        tools = client.list_tools()
        path = write_json("tools_list.json", tools)
        print(f"Saved tools list: {path}")
        print("Preview (capped):")
        print(safe_preview_json(tools.get("result", {}), max_bytes=512))
        client.close()
        return

    try:
        tool_args = json.loads(args.args)
        if not isinstance(tool_args, dict):
            raise ValueError("args must be a JSON object")
    except Exception as e:
        raise SystemExit(f"Invalid --args JSON: {e}")

    result = client.call_tool(args.tool, tool_args)

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out = write_json(f"{{SKILL_NAME}}_{args.tool}_{ts}.json", result)

    print(f"Saved tool result: {out}")
    print("Preview (capped):")
    preview = result.get("result", {})
    print(safe_preview_json(preview, max_bytes=512))

    client.close()


if __name__ == "__main__":
    main()
