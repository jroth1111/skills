#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


def run(cmd: list[str]) -> int:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(p.stdout.rstrip())
    return p.returncode


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate + scan all skills under a directory.")
    ap.add_argument("--skills-dir", default=".claude/skills", help="Directory containing skill folders")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Run validate_skill.py --strict for each skill",
    )
    ap.add_argument(
        "--fail-on-findings",
        action="store_true",
        help="Treat security scan findings as failures",
    )
    args = ap.parse_args()

    skills_dir = Path(args.skills_dir).expanduser().resolve()
    if not skills_dir.exists():
        raise SystemExit(f"Not found: {skills_dir}")

    validators = [
        (Path(__file__).parent / "validate_skill.py", ["--strict"] if args.strict else []),
        (
            Path(__file__).parent / "security_scan.py",
            ["--exit-nonzero"] if args.fail_on_findings else [],
        ),
    ]

    failures = 0
    for skill in sorted([p for p in skills_dir.iterdir() if p.is_dir()]):
        print(f"\n=== {skill.name} ===")
        for v, extra in validators:
            rc = run([sys.executable, str(v), str(skill), *extra])
            if rc != 0 and (v.name == "validate_skill.py" or args.fail_on_findings):
                failures += 1

    if failures:
        raise SystemExit(f"\nAudit finished with {failures} validation failure(s).")
    print("\nAudit finished (no validation failures).")


if __name__ == "__main__":
    main()
