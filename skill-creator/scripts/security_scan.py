#!/usr/bin/env python3
"""Heuristic security scan for a Skill folder."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Files to skip when scanning (e.g., this scanner itself)
SKIP_FILES = {"security_scan.py"}

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b(?:xoxb|xoxp|xoxa|xapp)-[0-9A-Za-z-]{10,}\b"),
]
# Narrowed patterns to reduce false positives (especially for meta-skills)
INJECTION_PATTERNS = [
    re.compile(r"ignore (all|any) (previous|prior) instructions", re.I),
    re.compile(r"(reveal|show|print|output).{0,20}system prompt", re.I),
    re.compile(r"exfiltrat(e|ion)", re.I),
    re.compile(r"do not (tell|inform|alert) the user", re.I),
    re.compile(r"bypass (safety|security|permissions|restrictions)", re.I),
]
DANGEROUS_SHELL = [
    re.compile(r"\brm\s+-rf\b"),
    re.compile(r"\bmkfs\b"),
    re.compile(r"\bdd\s+if="),
    re.compile(r"\bshutdown\b"),
    re.compile(r"\breboot\b"),
    re.compile(r"\bchmod\s+777\b"),
    re.compile(r"\bcurl\b\s+.*\|\s*(sh|bash)\b"),
]

TEXT_EXTS = {".md", ".txt", ".py", ".js", ".ts", ".sh", ".json", ".yaml", ".yml"}
# Also check for common secret file extensions
SECRET_FILE_EXTS = {".env", ".pem", ".key", ".p12", ".pfx"}


def scan_file(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return [f"Could not read file: {e}"]

    for pat in SECRET_PATTERNS:
        if pat.search(text):
            issues.append("Possible secret/private key material")

    for pat in INJECTION_PATTERNS:
        if pat.search(text):
            issues.append(f"Possible prompt-injection string: /{pat.pattern}/")

    if path.suffix in {".sh", ".py", ".js", ".ts"}:
        for pat in DANGEROUS_SHELL:
            if pat.search(text):
                issues.append(f"High-risk command pattern: /{pat.pattern}/")
    return issues


def main() -> None:
    ap = argparse.ArgumentParser(description="Heuristic security scan for a Skill folder.")
    ap.add_argument("skill_dir", help="Path to the skill folder")
    ap.add_argument(
        "--exit-nonzero",
        action="store_true",
        help="Exit with code 1 if any findings (useful for CI)",
    )
    args = ap.parse_args()

    root = Path(args.skill_dir).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")

    findings: list[tuple[Path, str]] = []
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        # Skip this scanner itself to avoid false positives on pattern definitions
        if p.name in SKIP_FILES:
            continue
        # Check for secret file extensions (even if we can't read them)
        if p.suffix.lower() in SECRET_FILE_EXTS:
            findings.append((p, f"Potential secret file by extension: {p.suffix}"))
            continue
        if p.suffix.lower() not in TEXT_EXTS and p.name != "SKILL.md":
            continue
        for issue in scan_file(p):
            findings.append((p, issue))

    if not findings:
        print("No obvious issues found (heuristic scan).")
        return

    print("Security scan findings (review required):\n")
    for p, issue in findings:
        rel = p.relative_to(root)
        print(f"- {rel}: {issue}")

    print("\nNote: heuristic scanner. Manual review still matters.")

    if args.exit_nonzero:
        sys.exit(1)


if __name__ == "__main__":
    main()
