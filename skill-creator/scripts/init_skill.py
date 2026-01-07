#!/usr/bin/env python3
"""Initialize a new skill from templates (non-interactive)."""

import argparse
import json
import re
from pathlib import Path

from _shared.templating import copy_template_tree

NAME_MAX = 64
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ARCHETYPES = {
    "basic": {"title": "Basic Logic", "entry_point": "scripts/main.py"},
    "api-wrapper": {"title": "API Wrapper", "entry_point": "scripts/wrapper.py"},
    "mcp-bridge": {"title": "MCP Bridge", "entry_point": "scripts/bridge.py"},
}
VALID_RISKS = {"low", "medium", "high"}


def title_case_skill_name(skill_name: str) -> str:
    return " ".join(word.capitalize() for word in skill_name.split("-"))


def format_bullets(items: list[str], fallback: str = "TODO") -> str:
    if not items:
        return f"- {fallback}"
    return "\n".join(f"- {item}" for item in items)


def format_commands(items: list[str], fallback: str = "TODO") -> str:
    return "\n".join(items) if items else fallback


def build_inputs_json(inputs: list[str]) -> str:
    if not inputs:
        return json.dumps({"input": ""}, indent=2)
    payload = {inp.strip().replace(" ", "_"): "" for inp in inputs if inp.strip()}
    if not payload:
        payload = {"input": ""}
    return json.dumps(dict(list(payload.items())[:5]), indent=2)


def init_skill(
    skill_name: str,
    path: str,
    description: str | None,
    risk: str,
    archetype: str,
    templates_root: Path,
    dependencies: list[str],
    inputs: list[str],
    success_criteria: list[str],
    verification: list[str],
    fallbacks: list[str],
    install_cmds: list[str],
    triggers: list[str],
    anti_triggers: list[str],
    acceptance_tests: list[str],
    model: str | None,
    version: str | None,
    license_value: str | None,
) -> Path | None:
    skill_dir = Path(path).resolve() / skill_name
    if skill_dir.exists():
        print(f"Error: Skill directory already exists: {skill_dir}")
        return None

    try:
        skill_dir.mkdir(parents=True, exist_ok=False)
        print(f"Created skill directory: {skill_dir}")
    except Exception as e:
        print(f"Error creating directory: {e}")
        return None

    allowed_tools = ["Read", "Write", "Edit", "Grep", "Glob", "Bash"]
    entry_point = ARCHETYPES[archetype]["entry_point"]
    variables = {
        "SKILL_NAME": skill_name,
        "SKILL_TITLE": title_case_skill_name(skill_name),
        "DESCRIPTION": description or "Describe what this skill does and when to use it (third-person present)",
        "ALLOWED_TOOLS": " ".join(allowed_tools),
        "ALLOWED_TOOLS_JSON": json.dumps(allowed_tools),
        "MODEL": model or "",
        "DEPENDENCIES": ", ".join(dependencies),
        "VERSION": version or "",
        "LICENSE": license_value or "",
        "ARCHETYPE": archetype,
        "ENTRY_POINT": entry_point,
        "RISK_LEVEL": risk,
        "INPUTS": format_bullets(inputs),
        "INPUTS_JSON": build_inputs_json(inputs),
        "DEPENDENCIES_BODY": format_bullets(dependencies, fallback="(none)"),
        "INSTALL_COMMANDS": format_commands(install_cmds, fallback="TODO"),
        "SUCCESS_CRITERIA": format_bullets(success_criteria),
        "VERIFICATION_COMMANDS": format_commands(verification),
        "FALLBACKS": format_bullets(fallbacks, fallback="TODO"),
        "TRIGGER_EXAMPLES": format_bullets(triggers or [f"TODO trigger {i}" for i in range(1, 6)]),
        "ANTI_TRIGGER_EXAMPLES": format_bullets(anti_triggers or [f"TODO anti-trigger {i}" for i in range(1, 4)]),
        "ACCEPTANCE_TESTS_LIST": format_bullets(
            acceptance_tests or ["TODO: Add acceptance tests (at least 3)"]
        ),
    }

    template_dir = templates_root / archetype
    if not template_dir.exists():
        print(f"Error: Template directory not found: {template_dir}")
        return None

    copy_template_tree(template_dir, skill_dir, variables)

    spec = {
        "name": skill_name,
        "title": variables["SKILL_TITLE"],
        "description": variables["DESCRIPTION"],
        "archetype": archetype,
        "risk_level": risk,
        "entry_point": entry_point,
        "triggers": triggers or [f"TODO {i}" for i in range(1, 6)],
        "anti_triggers": anti_triggers or [f"TODO {chr(ord('A') + i)}" for i in range(3)],
        "acceptance_tests": acceptance_tests or ["(fill in at least 3)"],
        "goals": success_criteria or ["TODO"],
        "inputs": inputs or ["(fill in)"],
    }
    (skill_dir / "skill.spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    print("Created skill.spec.json")

    print(f"\nSkill '{skill_name}' initialized successfully at {skill_dir}")
    print("\nNext steps:")
    print("1. Edit SKILL.md and skill.spec.json to fill in TODOs")
    print("2. Update references/, scripts/, and tests/ as needed")
    print("3. Run validation and security scan before packaging")

    return skill_dir


def main() -> None:
    ap = argparse.ArgumentParser(description="Initialize a new skill from templates.")
    ap.add_argument("skill_name", help="Skill name (lowercase-hyphen)")
    ap.add_argument("--path", required=True, help="Directory where the skill folder should be created")
    ap.add_argument("--description", help="Skill description (what + when, third-person present)")
    ap.add_argument("--risk", default="low", help="Risk level: low, medium, or high")
    ap.add_argument("--archetype", default="basic", choices=ARCHETYPES.keys(), help="Archetype to generate")
    ap.add_argument("--dependencies", action="append", default=[], help="Dependency (repeatable)")
    ap.add_argument("--install", action="append", default=[], help="Install command (repeatable)")
    ap.add_argument("--input", action="append", default=[], help="Required input (repeatable)")
    ap.add_argument("--success", action="append", default=[], help="Success criteria (repeatable)")
    ap.add_argument("--trigger", action="append", default=[], help="Trigger phrase (repeatable)")
    ap.add_argument("--anti-trigger", action="append", default=[], help="Anti-trigger phrase (repeatable)")
    ap.add_argument("--acceptance-test", action="append", default=[], help="Acceptance test (repeatable)")
    ap.add_argument("--verify", action="append", default=[], help="Verification command (repeatable)")
    ap.add_argument("--fallback", action="append", default=[], help="Fallback or rollback step (repeatable)")
    ap.add_argument("--model", help="Model override for this skill")
    ap.add_argument("--version", help="Skill version")
    ap.add_argument("--license", dest="license_value", help="Skill license")
    ap.add_argument("--templates-root", default=str(Path(__file__).parent.parent / "templates"), help="Templates root")
    args = ap.parse_args()

    if len(args.skill_name) > NAME_MAX:
        print(f"Error: Skill name exceeds {NAME_MAX} characters")
        raise SystemExit(1)
    if not NAME_RE.match(args.skill_name):
        print("Error: skill name must use lowercase letters and numbers with single hyphens between words")
        raise SystemExit(1)

    risk = args.risk.strip().lower()
    if risk not in VALID_RISKS:
        print("Error: risk must be one of low, medium, high")
        raise SystemExit(1)

    templates_root = Path(args.templates_root).expanduser().resolve()
    if not templates_root.exists():
        print(f"Error: Templates root not found: {templates_root}")
        raise SystemExit(1)

    print(f"Initializing skill: {args.skill_name}")
    print(f"   Location: {args.path}")
    print(f"   Archetype: {args.archetype}")
    print()

    result = init_skill(
        args.skill_name,
        args.path,
        args.description,
        risk,
        args.archetype,
        templates_root,
        args.dependencies,
        args.input,
        args.success,
        args.verify,
        args.fallback,
        args.install,
        args.trigger,
        args.anti_trigger,
        args.acceptance_test,
        args.model,
        args.version,
        args.license_value,
    )
    raise SystemExit(0 if result else 1)


if __name__ == "__main__":
    main()
