#!/usr/bin/env python3
"""Interactive skill scaffolding with quality-focused prompts."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import List

from _shared.templating import copy_template_tree

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ARCHETYPES = {
    "basic": {"title": "Basic Logic", "entry_point": "scripts/main.py"},
    "api-wrapper": {"title": "API Wrapper", "entry_point": "scripts/wrapper.py"},
    "mcp-bridge": {"title": "MCP Bridge", "entry_point": "scripts/bridge.py"},
}

# Minimum requirements for quality
MIN_TRIGGERS = 5
MIN_ANTI_TRIGGERS = 3
MIN_ACCEPTANCE_TESTS = 3
MIN_EXAMPLES = 1


def slugify(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-{2,}", "-", s)
    s = s.strip("-")
    return s[:64] if s else s


def ask(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"{prompt}{suffix}: ").strip()
    return val or (default or "")


def ask_list(prompt: str, min_items: int = 0, guidance: str = "") -> List[str]:
    if guidance:
        print(f"\n{guidance}")
    print(f"{prompt} (enter blank line to finish)")
    items: List[str] = []
    while True:
        remaining = min_items - len(items)
        if remaining > 0:
            line = input(f"[{remaining} more required] > ").strip()
        else:
            line = input("> ").strip()
        if not line:
            if len(items) < min_items:
                print(f"  Need at least {min_items} items. Keep going.")
                continue
            break
        items.append(line)
    return items


def format_bullets(items: List[str], fallback: str = "TODO") -> str:
    if not items:
        return f"- {fallback}"
    return "\n".join(f"- {item}" for item in items)


def format_commands(items: List[str], fallback: str = "TODO") -> str:
    return "\n".join(items) if items else fallback


def write_minimal_skill(skill_dir: Path, name: str, description: str) -> None:
    """Write a minimal SKILL.md only scaffold."""
    title = name.replace("-", " ").title()
    content = (
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        "---\n\n"
        f"# {title}\n\n"
        "Instructions for Claude go here.\n"
    )
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")


def pick_archetype(default: str = "basic") -> str:
    print("\nSelect archetype:")
    keys = list(ARCHETYPES.keys())
    for idx, key in enumerate(keys, start=1):
        title = ARCHETYPES[key]["title"]
        print(f"  {idx}) {title} ({key})")
    choice = ask("Choose archetype", default)
    if choice.isdigit():
        idx = int(choice)
        if 1 <= idx <= len(keys):
            return keys[idx - 1]
    if choice in ARCHETYPES:
        return choice
    return default


def collect_description_parts(quick: bool = False) -> str:
    """Guide user through building an effective description."""
    if not quick:
        print("\n" + "=" * 60)
        print("DESCRIPTION BUILDER")
        print("=" * 60)
        print("A good description has 3 parts:")
        print("  1. What it does (verb + object)")
        print("  2. When to use it (trigger conditions)")
        print("  3. Boundaries (what it's NOT for)")
        print()

    what = ask("What does this skill do?" if quick else "What does this skill do? (e.g., 'Reviews pull requests')")
    when = ask("When should it activate?" if quick else "When should it activate? (e.g., 'when reviewing code changes')")
    not_for = ask("What is it NOT for?" if quick else "What is it NOT for? (e.g., 'not for writing new code')", "")

    description = f"{what}. Use when {when}."
    if not_for:
        description += f" Not for {not_for}."

    print(f"\nGenerated description:\n  \"{description}\"")
    if ask("Accept this description? (y/n)", "y").lower() != "y":
        return ask("Enter your custom description")
    return description


def collect_examples(quick: bool = False) -> List[str]:
    """Collect concrete example user requests."""
    if not quick:
        print("\n" + "=" * 60)
        print("CONCRETE EXAMPLES")
        print("=" * 60)
        print("Provide short, realistic user requests that should trigger this skill.")
        print("These help shape triggers and acceptance tests.")
        print()
        print("Examples:")
        print("  - 'Write a commit message for my staged changes'")
        print("  - 'Summarize this diff into a PR review comment'")
        print("  - 'Extract tables from this PDF and save as CSV'")
        print()

    return ask_list(
        f"Enter {MIN_EXAMPLES} example user requests (aim for 2-3)",
        min_items=MIN_EXAMPLES,
    )


def collect_triggers(quick: bool = False) -> List[str]:
    """Guide user through systematic trigger discovery."""
    if not quick:
        print("\n" + "=" * 60)
        print("TRIGGER DISCOVERY")
        print("=" * 60)
        print("Think of DIFFERENT ways users might ask for this skill.")
        print("Vary the phrasing - don't just rephrase the same thing.")
        print()
        print("Examples of variety:")
        print("  - 'Review this PR'")
        print("  - 'What do you think of these changes?'")
        print("  - 'Check my code'")
        print("  - 'Give feedback on this diff'")
        print("  - 'Look over my pull request'")
        print()

    return ask_list(
        f"Enter {MIN_TRIGGERS} trigger phrases",
        min_items=MIN_TRIGGERS,
    )


def collect_anti_triggers(quick: bool = False) -> List[str]:
    """Guide user through anti-trigger discovery."""
    if not quick:
        print("\n" + "=" * 60)
        print("ANTI-TRIGGER DISCOVERY")
        print("=" * 60)
        print("What should NOT activate this skill?")
        print("Think of requests that sound similar but need different handling.")
        print()
        print("Examples:")
        print("  - If skill is 'review PR': anti-trigger might be 'write code for me'")
        print("  - If skill is 'generate tests': anti-trigger might be 'explain how tests work'")
        print()

    return ask_list(
        f"Enter {MIN_ANTI_TRIGGERS} anti-trigger phrases",
        min_items=MIN_ANTI_TRIGGERS,
    )


def collect_acceptance_tests(quick: bool = False) -> List[str]:
    """Guide user through defining testable acceptance criteria."""
    if not quick:
        print("\n" + "=" * 60)
        print("ACCEPTANCE TESTS")
        print("=" * 60)
        print("Define OBSERVABLE behaviors that prove the skill works.")
        print("Each test should be verifiable - you can look at output and check yes/no.")
        print()
        print("Good examples:")
        print("  - 'Mentions security concerns before style issues'")
        print("  - 'Provides specific line numbers in feedback'")
        print("  - 'Asks clarifying questions when requirements are ambiguous'")
        print()
        print("Bad examples (too vague):")
        print("  - 'Works well'")
        print("  - 'Gives good feedback'")
        print("  - 'Is helpful'")
        print()

    tests = ask_list(
        f"Enter {MIN_ACCEPTANCE_TESTS} acceptance tests",
        min_items=MIN_ACCEPTANCE_TESTS,
    )

    # Validate specificity (skip in quick mode)
    if not quick:
        vague_words = ["good", "well", "helpful", "nice", "proper", "correct", "appropriate"]
        for idx, test in enumerate(tests):
            if any(word in test.lower() for word in vague_words):
                print(f"\n  Warning: '{test}' may be too vague.")
                print("  Consider: What specific behavior would you observe?")
                replacement = ask("  Enter a more specific version (or press Enter to keep)")
                if replacement:
                    tests[idx] = replacement

    return tests


def collect_goals(quick: bool = False) -> List[str]:
    """Collect success criteria with guidance."""
    if not quick:
        print("\n" + "=" * 60)
        print("SUCCESS CRITERIA")
        print("=" * 60)
        print("What artifacts or outcomes does this skill produce?")
        print()
        print("Examples:")
        print("  - 'PR comment with structured feedback'")
        print("  - 'JSON file with extracted data in workspace/'")
        print("  - 'Commit message following conventional commits format'")
        print()

    return ask_list(
        "Enter success criteria",
        min_items=1,
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Scaffold a new Agent Skill folder with quality-focused prompts.")
    ap.add_argument("--name", help="Skill name (lowercase-hyphen). If omitted, interactive mode will ask.")
    ap.add_argument("--description", help="Skill description (what + when, third-person present).")
    ap.add_argument("--archetype", choices=list(ARCHETYPES.keys()), help="Archetype to generate.")
    ap.add_argument("--minimal", action="store_true", help="Create only SKILL.md (no spec or scripts).")
    ap.add_argument("--output-dir", default=".claude/skills", help="Where to create the skill folder")
    ap.add_argument("--templates-root", default=str(Path(__file__).parent.parent / "templates"), help="Templates root")
    ap.add_argument("--force", action="store_true", help="Overwrite existing folder if it exists")
    ap.add_argument("--interactive", action="store_true", help="Ask questions interactively (recommended)")
    ap.add_argument("--quick", action="store_true", help="Skip guidance text for experienced users")
    ap.add_argument(
        "--from-spec",
        metavar="FILE",
        help="Read skill spec from JSON file (non-interactive). JSON should contain: "
        "name, description, archetype, risk_level, triggers, anti_triggers, acceptance_tests, "
        "goals, inputs, dependencies (optional), install_commands (optional), "
        "verification_commands (optional), fallbacks (optional), examples (optional).",
    )
    args = ap.parse_args()

    # Handle --from-spec: read spec from file and populate args
    if args.from_spec:
        spec_path = Path(args.from_spec).expanduser().resolve()
        if not spec_path.exists():
            raise SystemExit(f"Spec file not found: {spec_path}")
        try:
            spec_data = json.loads(spec_path.read_text(encoding="utf-8"))
        except Exception as e:
            raise SystemExit(f"Failed to parse spec file: {e}")

        # Override args with spec data
        args.name = spec_data.get("name", args.name)
        args.description = spec_data.get("description", args.description)
        args.archetype = spec_data.get("archetype", args.archetype)
        # Store additional spec data for later use
        args._spec_data = spec_data

    # --from-spec bypasses interactive mode
    interactive = (
        not getattr(args, "_spec_data", None)
        and (
            args.interactive
            or (not args.name)
            or (not args.description)
            or ((not args.archetype) and not args.minimal)
        )
    )

    raw_name = args.name or ""
    description = args.description or ""
    archetype = args.archetype or ""
    examples: List[str] = []

    if interactive:
        print("=" * 60)
        print("SKILL CREATOR - Quality-Focused Scaffolding")
        print("=" * 60)
        print("\nThis wizard will guide you through creating an effective skill.")
        print("Take your time - quality inputs produce quality skills.\n")

        raw_name = ask("Skill name (lowercase-hyphen, e.g., 'reviewing-prs')", raw_name or "my-new-skill")

        # Use guided description builder
        if not description:
            description = collect_description_parts(quick=args.quick)
        else:
            print(f"\nUsing provided description: {description}")

        if not args.minimal:
            examples = collect_examples(quick=args.quick)
            archetype = pick_archetype(default=archetype or "basic")
        elif archetype:
            print("Note: --minimal ignores archetype selection.")

    name = raw_name.strip()
    if len(name) > 64 or not NAME_RE.match(name):
        name = slugify(name)

    if len(name) > 64 or not NAME_RE.match(name):
        raise SystemExit(
            "Invalid skill name after slugify. Use lowercase letters and numbers with single hyphens between words (max 64)."
        )

    if args.minimal:
        archetype = "minimal"
    elif not archetype:
        archetype = "basic"

    if archetype != "minimal" and archetype not in ARCHETYPES:
        raise SystemExit(f"Unknown archetype: {archetype}")

    output_dir = Path(args.output_dir).expanduser()
    skill_dir = (output_dir / name)

    if skill_dir.exists():
        if not args.force:
            raise SystemExit(f"Refusing to overwrite existing directory: {skill_dir} (use --force)")
        shutil.rmtree(skill_dir)

    skill_dir.mkdir(parents=True, exist_ok=True)

    if args.minimal:
        write_minimal_skill(skill_dir, name, description.strip())
        print("\n" + "=" * 60)
        print("SKILL CREATED SUCCESSFULLY")
        print("=" * 60)
        print(f"\nLocation: {skill_dir}")
        print("\nNext steps:")
        print(f"  1) Review and edit: {skill_dir / 'SKILL.md'}")
        print(f"  2) Validate structure: python scripts/validate_skill.py {skill_dir}")
        print("  3) Add skill.spec.json if you need triggers and acceptance tests.")
        return

    if interactive:
        risk = ask("\nRisk level (low/medium/high)", "low")
        if risk not in {"low", "medium", "high"}:
            risk = "low"

        # Use guided collection functions
        goals = collect_goals(quick=args.quick)
        triggers = collect_triggers(quick=args.quick)
        anti = collect_anti_triggers(quick=args.quick)
        acceptance = collect_acceptance_tests(quick=args.quick)

        inputs = ask_list(
            "\nRequired inputs (repo paths, services, APIs, schemas, flags)",
            min_items=1,
            guidance="What does this skill need to operate? Be specific about paths, services, etc.",
        )
        dependencies = ask_list("\nDependencies (packages/tools)", min_items=0)
        install_cmds = ask_list("\nInstall commands for dependencies", min_items=0) if dependencies else []
        verification = ask_list(
            "\nVerification commands to run after skill completes",
            min_items=1,
            guidance="What commands prove the skill worked? (e.g., 'cat workspace/output.json')",
        )
        fallbacks = ask_list("\nFallbacks / rollback steps if something fails", min_items=0)
    else:
        # Use spec data if available (--from-spec), otherwise use placeholders
        spec_data = getattr(args, "_spec_data", {})
        risk = spec_data.get("risk_level", "low")
        goals = spec_data.get("goals", ["TODO: Define success criteria"])
        triggers = spec_data.get("triggers", [f"TODO trigger {i}" for i in range(1, MIN_TRIGGERS + 1)])
        anti = spec_data.get("anti_triggers", [f"TODO anti-trigger {i}" for i in range(1, MIN_ANTI_TRIGGERS + 1)])
        acceptance = spec_data.get("acceptance_tests", [f"TODO acceptance test {i}" for i in range(1, MIN_ACCEPTANCE_TESTS + 1)])
        inputs = spec_data.get("inputs", ["TODO: Define required inputs"])
        dependencies = spec_data.get("dependencies", [])
        install_cmds = spec_data.get("install_commands", [])
        verification = spec_data.get("verification_commands", ["TODO: Define verification commands"])
        fallbacks = spec_data.get("fallbacks", [])
        examples = spec_data.get("examples", [])

    allowed_tools = ["Read", "Write", "Edit", "Grep", "Glob", "Bash"]
    entry_point = ARCHETYPES[archetype]["entry_point"]

    variables = {
        "SKILL_NAME": name,
        "SKILL_TITLE": name.replace("-", " ").title(),
        "DESCRIPTION": description.strip(),
        "ALLOWED_TOOLS": " ".join(allowed_tools),
        "ALLOWED_TOOLS_JSON": json.dumps(allowed_tools),
        "MODEL": "",
        "DEPENDENCIES": ", ".join(dependencies),
        "VERSION": "",
        "LICENSE": "",
        "ARCHETYPE": archetype,
        "ENTRY_POINT": entry_point,
        "RISK_LEVEL": risk,
        "INPUTS": format_bullets(inputs),
        "INPUTS_JSON": json.dumps(
            {inp.replace(" ", "_"): "" for inp in inputs[:5]} if inputs else {"input": ""},
            indent=2,
        ),
        "DEPENDENCIES_BODY": format_bullets(dependencies, fallback="(none)"),
        "INSTALL_COMMANDS": format_commands(install_cmds, fallback="(none)"),
        "SUCCESS_CRITERIA": format_bullets(goals),
        "VERIFICATION_COMMANDS": format_commands(verification),
        "FALLBACKS": format_bullets(fallbacks, fallback="(none)"),
        # Trigger and acceptance test examples for template
        "TRIGGER_EXAMPLES": format_bullets(triggers[:3], fallback="TODO: Add trigger scenarios"),
        "ANTI_TRIGGER_EXAMPLES": format_bullets(anti[:3], fallback="TODO: Add anti-trigger scenarios"),
        "ACCEPTANCE_TESTS_LIST": format_bullets(acceptance, fallback="TODO: Add acceptance tests"),
    }

    template_dir = Path(args.templates_root) / archetype
    if not template_dir.exists():
        raise SystemExit(f"Template directory not found: {template_dir}")
    copy_template_tree(template_dir, skill_dir, variables)

    spec = {
        "name": name,
        "title": variables["SKILL_TITLE"],
        "description": description.strip(),
        "archetype": archetype,
        "risk_level": risk,
        "entry_point": entry_point,
        "triggers": triggers,
        "anti_triggers": anti,
        "acceptance_tests": acceptance,
        "goals": goals,
        "inputs": inputs,
    }
    (skill_dir / "skill.spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")

    print("\n" + "=" * 60)
    print("SKILL CREATED SUCCESSFULLY")
    print("=" * 60)
    print(f"\nLocation: {skill_dir}")
    print("\nNext steps:")
    print(f"  1) Review and edit: {skill_dir / 'SKILL.md'}")
    print(f"  2) Validate structure: python scripts/validate_skill.py {skill_dir}")
    print(f"  3) Analyze triggers: python scripts/analyze_triggers.py {skill_dir}")
    print(f"  4) Evaluate effectiveness: python scripts/evaluate_skill.py {skill_dir}")
    print(f"  5) Security scan: python scripts/security_scan.py {skill_dir}")
    print(f"  6) Package: python scripts/package_skill.py {skill_dir}")

    if examples:
        # Write examples to smoke_prompts.md
        smoke_prompts_path = skill_dir / "tests" / "smoke_prompts.md"
        if smoke_prompts_path.exists():
            existing = smoke_prompts_path.read_text(encoding="utf-8")
            # Append examples as a section
            examples_section = "\n\n## Example User Requests\n\n"
            examples_section += "\n".join(f"- {ex}" for ex in examples)
            smoke_prompts_path.write_text(existing + examples_section, encoding="utf-8")
            print(f"\nExample user requests added to: {smoke_prompts_path}")
        else:
            print("\nExample user requests (add to SKILL.md if useful):")
            for ex in examples:
                print(f"  - {ex}")


if __name__ == "__main__":
    main()
