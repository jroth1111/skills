#!/usr/bin/env python3
"""Basic Logic archetype for {{SKILL_NAME}}.

Use this when the work is local and deterministic:
- parse files
- transform data
- generate outputs
- write artifacts to workspace/
"""
from __future__ import annotations

import argparse
from _fs import write_text, safe_preview_text


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default="hello world", help="Example input")
    args = ap.parse_args()

    # TODO: implement real logic
    output = args.text.upper()

    path = write_text("{{SKILL_NAME}}_output.txt", output)

    print(f"Wrote artifact: {path}")
    print("Preview (capped):")
    print(safe_preview_text(output, max_bytes=512))


if __name__ == "__main__":
    main()
