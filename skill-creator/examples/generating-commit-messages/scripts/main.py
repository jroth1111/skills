#!/usr/bin/env python3
from __future__ import annotations

import subprocess

from _fs import write_text, safe_preview_text


def main() -> None:
    diff = subprocess.run(
        ["git", "diff", "--staged"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    ).stdout

    if not diff.strip():
        print("No staged changes. Stage files first, then rerun.")
        return

    path = write_text("staged_diff.txt", diff)
    print(f"Saved staged diff to: {path}")
    print("Preview (capped):")
    print(safe_preview_text(diff, max_bytes=512))


if __name__ == "__main__":
    main()
