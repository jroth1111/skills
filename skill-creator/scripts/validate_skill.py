#!/usr/bin/env python3
"""Validate a Skill folder (strict)."""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from typing import List, Set

from _shared.frontmatter import extract_frontmatter, validate_frontmatter, parse_allowed_tools
from _shared.imports import imported_top_levels

TOOL_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:._-]*$")
ARCHETYPES = {"basic", "api-wrapper", "mcp-bridge"}
ARCHETYPES_REQUIRING_REQS = {"api-wrapper", "mcp-bridge"}
RISK_LEVELS = {"low", "medium", "high"}
TRIGGER_TERMS = [
    "use when",
    "use if",
    "use for",
    "use with",
    "when the user",
    "when working with",
]
TODO_RE = re.compile(r"\bTODO\b", re.IGNORECASE)
MIN_TRIGGER_COUNT = 5
MIN_ANTI_TRIGGER_COUNT = 3
MIN_ACCEPTANCE_TESTS = 3

COMMON_THIRD_PARTY = {
    "requests": "requests>=2.31.0",
    "httpx": "httpx",
    "mcp": "mcp",
}


def check_links(skill_dir: Path, skill_md_text: str) -> List[str]:
    import re as _re

    errors: List[str] = []
    for m in _re.finditer(r"\[[^\]]+\]\(([^)]+)\)", skill_md_text):
        target = m.group(1).strip()
        if not target or target.startswith("#"):
            continue
        if _re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
            continue
        if target.startswith("{baseDir}"):
            target = target[len("{baseDir}") :].lstrip("/")
        target = target.split("#", 1)[0].split("?", 1)[0].strip()
        if not target:
            continue
        p = (skill_dir / target).resolve()
        try:
            p.relative_to(skill_dir.resolve())
        except ValueError:
            errors.append(f"Link points outside skill directory: {target}")
            continue
        if not p.exists():
            errors.append(f"Broken link target: {target}")
    return errors


def check_python_syntax(file_path: Path) -> List[str]:
    try:
        ast.parse(file_path.read_text(encoding="utf-8"))
        return []
    except SyntaxError as exc:
        return [f"Python syntax error in {file_path.name}: {exc.msg} (line {exc.lineno})"]
    except Exception as exc:
        return [f"Could not parse {file_path.name}: {exc}"]


def load_spec(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_requirements(req_path: Path) -> str:
    try:
        return req_path.read_text(encoding="utf-8")
    except Exception:
        return ""


def validate_allowed_tools(tools: list[str]) -> List[str]:
    errors: List[str] = []
    for tool in tools:
        tool = tool.strip()
        if not tool:
            continue
        m = re.match(r"^([A-Za-z0-9:._-]+)\(([^)]*)\)$", tool)
        if m:
            base, pattern = m.groups()
            if not TOOL_NAME_RE.match(base):
                errors.append(f"Invalid tool name in allowed-tools: {tool}")
                continue
            if not pattern.strip():
                errors.append(f"Empty tool pattern in allowed-tools: {tool}")
            continue
        if not TOOL_NAME_RE.match(tool):
            errors.append(f"Invalid tool name in allowed-tools: {tool}")
    return errors


def validate_string_list(field: str, value: object) -> List[str]:
    """Validate a list of non-empty strings."""
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        return [f"skill.spec.json '{field}' must be a list of non-empty strings"]
    return []


def check_windows_paths(skill_md_text: str) -> List[str]:
    warnings: List[str] = []
    if re.search(r"[A-Za-z0-9_.-]+\\[A-Za-z0-9_.-]+", skill_md_text):
        warnings.append("Backslash path detected; use forward slashes (/) for portability")
    return warnings


def check_symlinks(skill_dir: Path) -> tuple[List[str], List[str]]:
    """Check for symlinks that resolve outside the skill directory."""
    errors: List[str] = []
    warnings: List[str] = []
    root = skill_dir.resolve()
    for p in skill_dir.rglob("*"):
        if not p.is_symlink():
            continue
        try:
            target = p.resolve()
        except FileNotFoundError:
            warnings.append(f"Broken symlink: {p.relative_to(skill_dir)}")
            continue
        try:
            target.relative_to(root)
        except ValueError:
            errors.append(
                f"Symlink points outside skill directory: {p.relative_to(skill_dir)} -> {target}"
            )
    return errors, warnings


def validate_spec(spec: dict) -> tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    required_fields = [
        "name",
        "title",
        "description",
        "archetype",
        "risk_level",
        "entry_point",
        "triggers",
        "anti_triggers",
        "acceptance_tests",
    ]
    for field in required_fields:
        if field not in spec:
            errors.append(f"skill.spec.json missing '{field}'")

    def check_str(field: str) -> None:
        value = spec.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"skill.spec.json '{field}' must be a non-empty string")

    for field in ("name", "title", "description", "archetype", "risk_level", "entry_point"):
        check_str(field)

    archetype = str(spec.get("archetype", "")).strip()
    if archetype and archetype not in ARCHETYPES:
        errors.append(f"skill.spec.json archetype must be one of {sorted(ARCHETYPES)}")

    risk = str(spec.get("risk_level", "")).strip()
    if risk and risk not in RISK_LEVELS:
        errors.append(f"skill.spec.json risk_level must be one of {sorted(RISK_LEVELS)}")

    for key in ("triggers", "anti_triggers", "acceptance_tests"):
        value = spec.get(key)
        if not isinstance(value, list) or len(value) == 0:
            errors.append(f"skill.spec.json '{key}' must be a non-empty list")
        else:
            # Validate each item is a non-empty string
            errors.extend(validate_string_list(key, value))

    for field in ("goals", "inputs", "outputs", "non_goals"):
        value = spec.get(field)
        if value is not None:
            errors.extend(validate_string_list(field, value))

    if "allowed_tools" in spec and "allowed-tools" in spec:
        errors.append("skill.spec.json should not include both 'allowed_tools' and 'allowed-tools'")
    allowed_tools = spec.get("allowed_tools", spec.get("allowed-tools"))
    if allowed_tools is not None:
        if isinstance(allowed_tools, str):
            warnings.append("skill.spec.json 'allowed_tools' should be a list of strings")
        elif isinstance(allowed_tools, list):
            errors.extend(validate_string_list("allowed_tools", allowed_tools))
        else:
            errors.append("skill.spec.json 'allowed_tools' must be a list of strings")

    integration = spec.get("integration")
    if integration is not None:
        if not isinstance(integration, dict):
            errors.append("skill.spec.json 'integration' must be an object")
        elif not all(isinstance(k, str) and isinstance(v, str) for k, v in integration.items()):
            errors.append("skill.spec.json 'integration' must map string keys to string values")

    return errors, warnings


def validate_skill(skill_dir: Path, strict: bool = False) -> tuple[bool, list[str], list[str]]:
    """Validate a skill folder.

    Args:
        skill_dir: Path to the skill folder
        strict: If True, require skill.spec.json and run full validation.
                If False (default), validate only against official Anthropic spec.
    """
    errors: List[str] = []
    warnings: List[str] = []

    skill_dir = Path(skill_dir).expanduser().resolve()
    skill_md = skill_dir / "SKILL.md"

    if not skill_dir.exists() or not skill_dir.is_dir():
        errors.append(f"Not a directory: {skill_dir}")
        return False, errors, warnings
    if not skill_md.exists():
        errors.append("Missing SKILL.md")
        return False, errors, warnings

    text = skill_md.read_text(encoding="utf-8")
    fm = extract_frontmatter(text)
    if fm is None:
        errors.append("SKILL.md must start with YAML frontmatter delimited by --- lines")
        return False, errors, warnings
    warnings.extend(getattr(fm, "warnings", []))

    fm_errors, fm_warnings = validate_frontmatter(fm.data)
    errors.extend(fm_errors)
    warnings.extend(fm_warnings)

    name_value = fm.data.get("name", "")
    name = name_value.strip() if isinstance(name_value, str) else ""
    if name and name != skill_dir.name:
        errors.append(f"Name '{name}' must match directory name '{skill_dir.name}'")

    allowed_raw = fm.data.get("allowed-tools")
    front_tools: List[str] = []
    if allowed_raw:
        front_tools = parse_allowed_tools(allowed_raw)
        errors.extend(validate_allowed_tools(front_tools))

    errors.extend(check_links(skill_dir, text))

    desc_value = fm.data.get("description", "")
    desc = desc_value.strip() if isinstance(desc_value, str) else ""
    if desc and not any(term in desc.lower() for term in TRIGGER_TERMS):
        warnings.append("Description may lack explicit trigger terms (for example, 'Use when ...')")
    if desc and len(desc) > 200:
        warnings.append("Description exceeds ~200 characters; consider tightening for reliable triggering")
    if desc and TODO_RE.search(desc):
        msg = "Description contains TODO placeholder"
        if strict:
            errors.append(msg)
        else:
            warnings.append(msg)

    warnings.extend(check_windows_paths(text))

    symlink_errors, symlink_warnings = check_symlinks(skill_dir)
    if strict:
        errors.extend(symlink_errors)
    else:
        warnings.extend(symlink_errors)
    warnings.extend(symlink_warnings)

    if len(text.splitlines()) > 500:
        warnings.append("SKILL.md exceeds 500 lines; move details into references")

    # Spec checks (optional in default mode, required in strict mode)
    spec_path = skill_dir / "skill.spec.json"
    spec = None

    if not spec_path.exists():
        if strict:
            errors.append("Missing skill.spec.json (required in strict mode)")
        else:
            warnings.append("No skill.spec.json found; consider adding one for complex skills")
    else:
        try:
            spec = load_spec(spec_path)
        except Exception as exc:
            errors.append(f"Invalid skill.spec.json: {exc}")

    # Only run spec validation if we have a spec file
    if spec is not None:
        spec_errors, spec_warnings = validate_spec(spec)
        if strict:
            errors.extend(spec_errors)
        else:
            # In default mode, spec issues are warnings
            warnings.extend(spec_errors)
        warnings.extend(spec_warnings)

        # Minimum recommended counts
        triggers = spec.get("triggers")
        if isinstance(triggers, list) and len(triggers) < MIN_TRIGGER_COUNT:
            warnings.append(f"Only {len(triggers)} trigger(s); recommend at least {MIN_TRIGGER_COUNT}")
        anti_triggers = spec.get("anti_triggers")
        if isinstance(anti_triggers, list) and len(anti_triggers) < MIN_ANTI_TRIGGER_COUNT:
            warnings.append(
                f"Only {len(anti_triggers)} anti-trigger(s); recommend at least {MIN_ANTI_TRIGGER_COUNT}"
            )
        acceptance = spec.get("acceptance_tests")
        if isinstance(acceptance, list) and len(acceptance) < MIN_ACCEPTANCE_TESTS:
            warnings.append(
                f"Only {len(acceptance)} acceptance test(s); recommend at least {MIN_ACCEPTANCE_TESTS}"
            )

        # Cross-check name/description
        if isinstance(spec.get("name"), str) and name and spec.get("name") != name:
            msg = f"skill.spec.json name '{spec.get('name')}' does not match SKILL.md name '{name}'"
            if strict:
                errors.append(msg)
            else:
                warnings.append(msg)
        if isinstance(spec.get("description"), str) and desc and spec.get("description") != desc:
            warnings.append("skill.spec.json description differs from SKILL.md description")

        risk_level = str(spec.get("risk_level", "")).strip()
        if risk_level == "high" and not strict:
            warnings.append(
                "risk_level is high; run validate_skill.py --strict and include verification/rollback steps"
            )

        entry = str(spec.get("entry_point", "")).strip()
        if entry:
            ep = (skill_dir / entry).resolve()
            try:
                ep.relative_to(skill_dir.resolve())
            except ValueError:
                msg = f"Entry point points outside skill directory: {entry}"
                if strict:
                    errors.append(msg)
                else:
                    warnings.append(msg)
            else:
                if not ep.exists():
                    msg = f"Entry point not found: {entry}"
                    if strict:
                        errors.append(msg)
                    else:
                        warnings.append(msg)
        elif strict:
            errors.append("skill.spec.json missing entry_point")

        archetype = str(spec.get("archetype", "")).strip()
        reqs_path = skill_dir / "requirements.txt"
        if archetype in ARCHETYPES_REQUIRING_REQS and not reqs_path.exists():
            warnings.append(f"Archetype '{archetype}' typically needs requirements.txt (deps). Missing.")

        spec_allowed_raw = None
        if "allowed_tools" in spec:
            spec_allowed_raw = spec.get("allowed_tools")
        elif "allowed-tools" in spec:
            spec_allowed_raw = spec.get("allowed-tools")

        if spec_allowed_raw is not None:
            if isinstance(spec_allowed_raw, str):
                spec_tools = parse_allowed_tools(spec_allowed_raw)
            elif isinstance(spec_allowed_raw, list):
                spec_tools = [t.strip() for t in spec_allowed_raw if isinstance(t, str) and t.strip()]
            else:
                spec_tools = []

            if not allowed_raw:
                msg = "skill.spec.json allowed_tools set but SKILL.md missing allowed-tools"
                if strict:
                    errors.append(msg)
                else:
                    warnings.append(msg)
            elif sorted(spec_tools) != sorted(front_tools):
                msg = "allowed-tools in SKILL.md does not match skill.spec.json allowed_tools"
                if strict:
                    errors.append(msg)
                else:
                    warnings.append(msg)

        for field in ("triggers", "anti_triggers", "acceptance_tests"):
            values = spec.get(field, [])
            if isinstance(values, list):
                for item in values:
                    if isinstance(item, str) and TODO_RE.search(item):
                        msg = f"skill.spec.json {field} contains TODO placeholder: '{item}'"
                        if strict:
                            errors.append(msg)
                        else:
                            warnings.append(msg)

    # Check scripts if they exist (no warning if missing - instruction-only skills are valid)
    scripts_dir = skill_dir / "scripts"
    reqs_path = skill_dir / "requirements.txt"
    req_text = read_requirements(reqs_path) if reqs_path.exists() else ""

    if scripts_dir.exists():
        imports: Set[str] = set()
        # Use rglob to recursively scan all Python files in scripts/
        for py_file in scripts_dir.rglob("*.py"):
            errors.extend(check_python_syntax(py_file))
            try:
                imports |= imported_top_levels(py_file)
            except Exception as exc:
                warnings.append(f"Could not analyze imports in {py_file.name}: {exc}")

        for mod, hint in COMMON_THIRD_PARTY.items():
            if mod in imports and hint not in req_text:
                warnings.append(f"Script imports '{mod}' but requirements.txt does not mention it (expected like: {hint})")

    return (len(errors) == 0), errors, warnings


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate an Agent Skill folder.")
    ap.add_argument("skill_dir", help="Path to the skill folder")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: require skill.spec.json and entry_point. Default validates only official Anthropic spec.",
    )
    args = ap.parse_args()

    ok, errors, warnings = validate_skill(Path(args.skill_dir), strict=args.strict)

    if errors:
        print("Skill validation failed:\n")
        for e in errors:
            print(f"- {e}")
        if warnings:
            print("\nWarnings:")
            for w in warnings:
                print(f"- {w}")
        raise SystemExit(1)

    print("Skill validation passed.")
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"- {w}")


if __name__ == "__main__":
    main()
