#!/usr/bin/env python3
"""
Quick validation script for skills - minimal version (wrapper for validate_skill).
"""

import sys
from pathlib import Path

from validate_skill import validate_skill as validate_skill_impl


def validate_skill(skill_path):
    ok, errors, warnings = validate_skill_impl(Path(skill_path))
    if not ok:
        return False, "; ".join(errors)
    if warnings:
        return True, f"Skill is valid! Warning: {warnings[0]}"
    return True, "Skill is valid!"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: scripts/quick_validate.py <skill_directory>")
        sys.exit(1)

    valid, message = validate_skill(sys.argv[1])
    print(message)
    sys.exit(0 if valid else 1)
