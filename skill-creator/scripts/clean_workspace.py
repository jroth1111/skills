#!/usr/bin/env python3
"""Clean workspace artifacts for a skill.

Usage:
  python scripts/clean_workspace.py [path/to/workspace] [--dry-run]
  python scripts/clean_workspace.py --skill-dir path/to/skill [--dry-run]
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def clean_workspace(path: Path, dry_run: bool) -> None:
    """Remove all files and folders under the workspace directory."""
    if not path.exists():
        print(f"Workspace not found: {path}")
        return

    if not path.is_dir():
        raise SystemExit(f"Not a directory: {path}")

    if path.name != "workspace":
        raise SystemExit("Refusing to clean: path must be named 'workspace'")

    for item in path.iterdir():
        if dry_run:
            print(f"[dry-run] remove {item}")
            continue
        # Handle symlinks safely - unlink them, don't follow them
        if item.is_symlink():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

    if dry_run:
        print("Dry run complete.")
    else:
        print(f"Workspace cleaned: {path}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Clean skill workspace artifacts.")
    ap.add_argument(
        "path",
        nargs="?",
        default="workspace",
        help="Path to workspace directory (default: ./workspace)",
    )
    ap.add_argument(
        "--skill-dir",
        help="Path to skill directory (uses <skill-dir>/workspace)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="List files to remove without deleting",
    )
    args = ap.parse_args()

    if args.skill_dir:
        skill_dir = Path(args.skill_dir).expanduser().resolve()
        workspace = skill_dir / "workspace"
    else:
        workspace = Path(args.path).expanduser().resolve()

    clean_workspace(workspace, args.dry_run)


if __name__ == "__main__":
    main()
