#!/usr/bin/env python3
"""Evaluate skill effectiveness against acceptance tests and test cases.

DISCLAIMER: This is a MANUAL VERIFICATION checklist, not automated testing.

It guides you through checking acceptance criteria after running the skill.
The actual testing happens when you use the skill with Claude - this tool
just helps you systematically verify the results.

Workflow:
1. Run the skill with a trigger phrase in Claude
2. Use this tool to verify the skill exhibited expected behaviors
3. Record results for tracking improvement over time
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from analyze_triggers import analyze_triggers
from validate_skill import validate_skill


def load_spec(skill_dir: Path) -> dict:
    """Load skill.spec.json."""
    spec_path = skill_dir / "skill.spec.json"
    if not spec_path.exists():
        raise FileNotFoundError(f"No skill.spec.json found at {spec_path}")
    return json.loads(spec_path.read_text(encoding="utf-8"))


def load_test_cases(skill_dir: Path) -> List[dict]:
    """Load test cases from tests/cases.json if it exists."""
    cases_path = skill_dir / "tests" / "cases.json"
    if cases_path.exists():
        return json.loads(cases_path.read_text(encoding="utf-8"))
    return []


def run_auto_checks(skill_dir: Path, spec: dict, test_cases: List[dict]) -> List[dict]:
    """Run automated checks that do not require live Claude usage."""
    checks = []

    ok, errors, warnings = validate_skill(skill_dir, strict=True)
    checks.append({
        "name": "strict_validation",
        "passed": ok,
        "errors": errors,
        "warnings": warnings,
    })

    description = spec.get("description", "")
    triggers = spec.get("triggers", [])
    anti_triggers = spec.get("anti_triggers", [])
    trigger_report = analyze_triggers(description, triggers, anti_triggers)
    issues = trigger_report.get("issues", [])
    trigger_statuses = [t.get("status") for t in trigger_report.get("trigger_results", [])]
    checks.append({
        "name": "trigger_analysis",
        "passed": len(issues) == 0,
        "issues": issues,
        "suggestions": trigger_report.get("suggestions", []),
        "summary": {
            "strong": trigger_statuses.count("STRONG"),
            "weak": trigger_statuses.count("WEAK"),
            "poor": trigger_statuses.count("POOR"),
        },
    })

    case_coverage_ok = len(test_cases) >= len(triggers) if triggers else True
    checks.append({
        "name": "test_case_coverage",
        "passed": case_coverage_ok,
        "details": {
            "triggers": len(triggers),
            "test_cases": len(test_cases),
        },
    })

    return checks


def print_disclaimer() -> None:
    """Print disclaimer about tool limitations."""
    print("\n" + "-" * 60)
    print("NOTE: This is a MANUAL verification checklist.")
    print("You must run the skill in Claude first, then use this tool")
    print("to record whether it exhibited the expected behaviors.")
    print("-" * 60)


def interactive_evaluation(
    spec: dict,
    test_cases: List[dict],
    *,
    auto: bool = False,
    interactive: bool = True,
    skill_dir: Optional[Path] = None,
) -> dict:
    """Run evaluation session (interactive or auto-assisted)."""
    results = {
        "skill_name": spec.get("name", "unknown"),
        "evaluated_at": datetime.now().isoformat(),
        "acceptance_tests": [],
        "test_case_results": [],
        "auto_checks": [],
        "overall_score": 0.0,
        "issues": [],
        "recommendations": [],
    }

    if interactive:
        print_disclaimer()
    print("\n" + "=" * 60)
    print("SKILL EFFECTIVENESS EVALUATION")
    print("=" * 60)
    print(f"\nEvaluating: {spec.get('name', 'unknown')}")
    print(f"Description: {spec.get('description', 'N/A')[:80]}...")

    if auto and skill_dir:
        results["auto_checks"] = run_auto_checks(skill_dir, spec, test_cases)
        for check in results["auto_checks"]:
            if not check.get("passed", False):
                results["recommendations"].append(
                    f"Auto check failed: {check['name']}. Review details."
                )

    # Evaluate acceptance tests
    print("\n" + "-" * 40)
    print("ACCEPTANCE TEST VERIFICATION")
    print("-" * 40)
    if interactive:
        print("\nFor each acceptance test, run the skill and verify the behavior.")
        print("Answer 'y' if the skill exhibits this behavior, 'n' if not, 's' to skip.\n")

    acceptance_tests = spec.get("acceptance_tests", [])
    passed = 0
    failed = 0
    skipped = 0

    if interactive:
        for i, test in enumerate(acceptance_tests, 1):
            print(f"\n[{i}/{len(acceptance_tests)}] {test}")
            while True:
                response = input("  Does the skill exhibit this behavior? (y/n/s): ").strip().lower()
                if response in ("y", "yes"):
                    results["acceptance_tests"].append({"test": test, "result": "PASS"})
                    passed += 1
                    print("  ✓ PASS")
                    break
                elif response in ("n", "no"):
                    results["acceptance_tests"].append({"test": test, "result": "FAIL"})
                    failed += 1
                    note = input("  What went wrong? (optional): ").strip()
                    if note:
                        results["issues"].append(f"Acceptance test failed: '{test}' - {note}")
                    print("  ✗ FAIL")
                    break
                elif response in ("s", "skip"):
                    results["acceptance_tests"].append({"test": test, "result": "SKIP"})
                    skipped += 1
                    print("  - SKIPPED")
                    break
                else:
                    print("  Please enter 'y', 'n', or 's'")
    else:
        for test in acceptance_tests:
            results["acceptance_tests"].append({"test": test, "result": "SKIP"})
            skipped += 1

    # Evaluate test cases if available
    if test_cases and interactive:
        print("\n" + "-" * 40)
        print("TEST CASE EVALUATION")
        print("-" * 40)

        for i, case in enumerate(test_cases, 1):
            print(f"\n[Test Case {i}]")
            print(f"Input: {case.get('input', 'N/A')}")
            if case.get("expected_behaviors"):
                print("Expected behaviors:")
                for behavior in case["expected_behaviors"]:
                    print(f"  - {behavior}")

            case_passed = 0
            case_total = len(case.get("expected_behaviors", []))

            for behavior in case.get("expected_behaviors", []):
                response = input(f"  Did skill exhibit: '{behavior}'? (y/n): ").strip().lower()
                if response in ("y", "yes"):
                    case_passed += 1

            case_score = case_passed / case_total if case_total > 0 else 0
            results["test_case_results"].append({
                "input": case.get("input"),
                "passed": case_passed,
                "total": case_total,
                "score": round(case_score, 2),
            })
            print(f"  Score: {case_passed}/{case_total} ({case_score:.0%})")
    elif test_cases and not interactive:
        results["recommendations"].append(
            "Test cases present but skipped due to --non-interactive. Run interactively to score behaviors."
        )

    # Calculate overall score
    total_tests = passed + failed
    if total_tests > 0:
        results["overall_score"] = round(passed / total_tests, 2)

    # Generate recommendations
    if failed > 0:
        results["recommendations"].append(
            f"{failed} acceptance test(s) failed. Review SKILL.md instructions "
            "to ensure they clearly guide toward these behaviors."
        )

    if skipped > 0:
        results["recommendations"].append(
            f"{skipped} test(s) skipped. Consider running these later to complete evaluation."
        )

    # Check for test coverage
    triggers = spec.get("triggers", [])
    if len(test_cases) < len(triggers):
        results["recommendations"].append(
            f"Only {len(test_cases)} test cases for {len(triggers)} triggers. "
            "Consider adding test cases for each trigger scenario."
        )

    return results


def print_summary(results: dict) -> None:
    """Print evaluation summary."""
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for t in results["acceptance_tests"] if t["result"] == "PASS")
    failed = sum(1 for t in results["acceptance_tests"] if t["result"] == "FAIL")
    skipped = sum(1 for t in results["acceptance_tests"] if t["result"] == "SKIP")

    print(f"\nAcceptance Tests: {passed} passed, {failed} failed, {skipped} skipped")
    print(f"Overall Score: {results['overall_score']:.0%}")

    if results["test_case_results"]:
        avg_case_score = sum(c["score"] for c in results["test_case_results"]) / len(results["test_case_results"])
        print(f"Test Case Average: {avg_case_score:.0%}")

    if results.get("auto_checks"):
        print("\nAuto Checks:")
        for check in results["auto_checks"]:
            status = "✅ PASS" if check.get("passed") else "❌ FAIL"
            print(f"{status}: {check.get('name')}")

    if results["issues"]:
        print("\nIssues Found:")
        for issue in results["issues"]:
            print(f"  ✗ {issue}")

    if results["recommendations"]:
        print("\nRecommendations:")
        for rec in results["recommendations"]:
            print(f"  → {rec}")

    if results["overall_score"] >= 0.8 and failed == 0:
        print("\n✓ Skill appears to be effective!")
    elif results["overall_score"] >= 0.6:
        print("\n⚠ Skill needs improvement in some areas.")
    else:
        print("\n✗ Skill needs significant work. Review the issues above.")


def create_test_cases_template(skill_dir: Path, spec: dict, case_limit: int | None) -> None:
    """Create a template test cases file."""
    tests_dir = skill_dir / "tests"
    tests_dir.mkdir(exist_ok=True)

    cases_path = tests_dir / "cases.json"
    if cases_path.exists():
        print(f"Test cases already exist at {cases_path}")
        return

    # Generate template based on triggers
    triggers = spec.get("triggers", [])
    if case_limit and case_limit > 0:
        triggers = triggers[:case_limit]
    acceptance = spec.get("acceptance_tests", [])

    cases = []
    for i, trigger in enumerate(triggers, 1):
        cases.append({
            "id": f"case_{i}",
            "input": trigger,
            "context": "TODO: Add any context needed for this test",
            "expected_behaviors": acceptance[:2] if acceptance else ["TODO: Define expected behaviors"],
        })

    cases_path.write_text(json.dumps(cases, indent=2), encoding="utf-8")
    print(f"Created test cases template at {cases_path}")
    print("Edit this file to add specific test scenarios.")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Evaluate skill effectiveness against acceptance tests."
    )
    ap.add_argument("skill_dir", help="Path to the skill folder")
    ap.add_argument(
        "--create-cases",
        action="store_true",
        help="Create a template test cases file",
    )
    ap.add_argument(
        "--case-limit",
        type=int,
        default=0,
        help="Limit number of triggers when creating cases (default: all)",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    ap.add_argument(
        "--output",
        help="Save results to file",
    )
    ap.add_argument(
        "--auto",
        action="store_true",
        help="Run automated checks (strict validation, trigger analysis, coverage).",
    )
    ap.add_argument(
        "--non-interactive",
        action="store_true",
        help="Skip prompts; useful for CI. Implies --auto.",
    )
    ap.add_argument(
        "--no-workspace-save",
        action="store_true",
        help="Skip saving evaluation results to workspace/",
    )
    args = ap.parse_args()

    skill_dir = Path(args.skill_dir).expanduser().resolve()

    try:
        spec = load_spec(skill_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Run 'python scripts/forge.py' to create a skill with spec file.")
        raise SystemExit(1)

    if args.create_cases:
        create_test_cases_template(skill_dir, spec, args.case_limit or None)
        return

    test_cases = load_test_cases(skill_dir)

    if not spec.get("acceptance_tests"):
        print("Warning: No acceptance tests defined in skill.spec.json")
        print("Run 'python scripts/forge.py --interactive' to add acceptance tests.")

    if args.non_interactive:
        args.auto = True
    results = interactive_evaluation(
        spec,
        test_cases,
        auto=args.auto,
        interactive=not args.non_interactive,
        skill_dir=skill_dir,
    )

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_summary(results)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"\nResults saved to {output_path}")

    # Save to workspace for tracking
    if not args.no_workspace_save:
        workspace = skill_dir / "workspace"
        workspace.mkdir(exist_ok=True)
        eval_path = workspace / f"evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        eval_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"Evaluation saved to {eval_path}")


if __name__ == "__main__":
    main()
