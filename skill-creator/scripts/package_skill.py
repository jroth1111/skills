#!/usr/bin/env python3
"""Package a Skill folder into a .skill zip (folder at zip root)."""

import argparse
import subprocess
import sys
import zipfile
from pathlib import Path

from validate_skill import validate_skill

EXCLUDE_DIRS = {
    "__pycache__", ".git", ".svn", ".hg", "workspace",
    "__MACOSX", ".pytest_cache", ".venv", "node_modules",
    ".mypy_cache", ".ruff_cache",
}
EXCLUDE_SUFFIXES = {".zip", ".skill", ".pyc", ".pyo"}
EXCLUDE_NAMES = {".DS_Store", "Thumbs.db", ".gitkeep"}


def run_security_scan(skill_path: Path) -> bool:
    scan_script = Path(__file__).parent / "security_scan.py"
    result = subprocess.run(
        [sys.executable, str(scan_script), str(skill_path), "--exit-nonzero"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    return result.returncode == 0


def package_skill(skill_path: str, output_dir: str | None = None, *, run_scan: bool = False) -> Path | None:
    skill_path = Path(skill_path).resolve()

    if not skill_path.exists():
        print(f"Error: Skill folder not found: {skill_path}")
        return None

    if not skill_path.is_dir():
        print(f"Error: Path is not a directory: {skill_path}")
        return None

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        print(f"Error: SKILL.md not found in {skill_path}")
        return None

    print("Validating skill...")
    valid, errors, warnings = validate_skill(skill_path)
    if not valid:
        print("Validation failed:\n")
        for e in errors:
            print(f"- {e}")
        print("\nPlease fix the validation errors before packaging.")
        return None
    print("Skill validation passed.")

    # Warn if scripts/ exists without skill.spec.json (suggests incomplete skill)
    scripts_dir = skill_path / "scripts"
    spec_file = skill_path / "skill.spec.json"
    if scripts_dir.exists() and scripts_dir.is_dir() and not spec_file.exists():
        print("\nNote: Skill has scripts/ but no skill.spec.json.")
        print("Consider adding spec for testable triggers and acceptance criteria.")
        print("Run: python scripts/forge.py --interactive")

    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"- {w}")
    print()

    if run_scan:
        print("Running security scan...")
        if not run_security_scan(skill_path):
            print("\nSecurity scan failed. Fix findings before packaging.")
            return None
        print("Security scan passed.\n")

    skill_name = skill_path.name
    if output_dir:
        output_path = Path(output_dir).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path.cwd()

    zip_filename = output_path / f"{skill_name}.skill"

    try:
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in skill_path.rglob("*"):
                if file_path.is_dir():
                    continue
                # Skip symlinks for safety (don't package external content)
                if file_path.is_symlink():
                    continue
                if file_path.name in EXCLUDE_NAMES:
                    continue
                # Use relative path for exclusion check (fix: was using absolute path parts)
                rel_path = file_path.relative_to(skill_path)
                if any(part in EXCLUDE_DIRS for part in rel_path.parts):
                    continue
                if file_path.suffix in EXCLUDE_SUFFIXES:
                    continue
                arcname = file_path.relative_to(skill_path.parent)
                zipf.write(file_path, arcname)

        print(f"Successfully packaged skill to: {zip_filename}")
        return zip_filename

    except Exception as e:
        print(f"Error creating zip file: {e}")
        return None


def main() -> None:
    ap = argparse.ArgumentParser(description="Package a Skill folder into a .skill zip.")
    ap.add_argument("skill_dir", help="Path to the skill folder")
    ap.add_argument("output_dir", nargs="?", help="Optional output directory")
    ap.add_argument(
        "--scan",
        action="store_true",
        help="Run security scan before packaging",
    )
    args = ap.parse_args()

    print(f"Packaging skill: {args.skill_dir}")
    if args.output_dir:
        print(f"   Output directory: {args.output_dir}")
    print()

    result = package_skill(args.skill_dir, args.output_dir, run_scan=args.scan)

    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
