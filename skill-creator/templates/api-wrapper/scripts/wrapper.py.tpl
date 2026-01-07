#!/usr/bin/env python3
"""API Wrapper archetype for {{SKILL_NAME}}.

Pattern: Filesystem pattern (input -> fetch -> save -> summarize)

- Raw responses are saved to workspace/
- Stdout is summaries + artifact paths + tiny previews (capped)
"""
from __future__ import annotations

import argparse
from datetime import datetime

from _fs import write_json, safe_preview_json
from http_client import get_json


def fetch(query: str) -> dict:
    # TODO: Replace with your API endpoint.
    # Use env vars for keys, never hard-code secrets.
    # Example:
    #   api_key = os.environ["EXAMPLE_API_KEY"]
    #   url = f"https://api.example.com/search?q={query}"
    #   status, payload = get_json(url, headers={"Authorization": f"Bearer {api_key}"})
    #   if status != 200:
    #       raise RuntimeError(payload)
    #   return payload

    # Placeholder payload:
    return {"query": query, "results": [f"item-{i}" for i in range(1, 101)]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query", help="Query string")
    ap.add_argument("--out", default="", help="Optional output filename under workspace/")
    args = ap.parse_args()

    payload = fetch(args.query)

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = args.out.strip() or f"{{SKILL_NAME}}_{ts}.json"
    path = write_json(filename, payload)

    results = payload.get("results", [])
    preview = results[:2] if isinstance(results, list) else results

    print(f"Saved raw payload to: {path}")
    print(f"Summary: results_count={len(results) if isinstance(results, list) else 'n/a'} query={args.query!r}")
    print("Preview (capped):")
    print(safe_preview_json(preview, max_bytes=512))


if __name__ == "__main__":
    main()
