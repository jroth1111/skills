#!/usr/bin/env python3
"""Analyze trigger phrases against skill description for activation likelihood.

DISCLAIMER: This is a PREPARATION tool, not a testing tool.

It analyzes trigger phrases using word overlap heuristics. It CANNOT:
- Predict how Claude will interpret triggers
- Test actual skill activation
- Guarantee the skill will work

Use this to catch obvious issues before deployment, then verify
behavior through actual use with Claude.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import List, Set, Tuple


# Common abbreviations to preserve (matched case-insensitively in original text)
ABBREVIATIONS = {"pr", "ci", "ui", "db", "api", "sdk", "cli", "url", "id", "io", "ok"}
SYNONYM_MAP = {
    "pr": {"pull", "request"},
    "pull": {"pr"},
    "request": {"pr"},
    "pkg": {"package"},
    "package": {"pkg"},
    "scaffold": {"generate"},
    "generate": {"scaffold"},
    "ci": {"pipeline"},
    "pipeline": {"ci"},
}


def naive_stem(word: str) -> str:
    """Apply naive stemming by stripping common suffixes.

    This is intentionally simple to avoid external dependencies.
    Handles common inflections: reviews→review, requests→request, etc.
    """
    if len(word) <= 3:
        return word
    # Order matters: check longer suffixes first
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("ing") and len(word) > 4:
        # running → run (remove doubled consonant)
        base = word[:-3]
        if len(base) >= 2 and base[-1] == base[-2] and base[-1] not in "aeiou":
            return base[:-1]
        return base
    if word.endswith("ed") and len(word) > 3:
        base = word[:-2]
        if len(base) >= 2 and base[-1] == base[-2] and base[-1] not in "aeiou":
            return base[:-1]
        return base
    if word.endswith("es") and len(word) > 3:
        return word[:-2]
    if word.endswith("s") and len(word) > 3 and not word.endswith("ss"):
        return word[:-1]
    return word


def tokenize(text: str) -> Set[str]:
    """Extract lowercase words from text with naive stemming."""
    # First, find abbreviations (uppercase 2-3 letter sequences)
    abbrevs = set(re.findall(r"\b[A-Z]{2,4}\b", text))
    abbrevs = {a.lower() for a in abbrevs if a.lower() in ABBREVIATIONS}

    words = re.findall(r"[a-z]+", text.lower())
    # Filter out very common words
    stopwords = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "need", "dare",
        "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
        "from", "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "under", "again", "further", "then", "once", "here",
        "there", "when", "where", "why", "how", "all", "each", "few", "more",
        "most", "other", "some", "such", "no", "nor", "not", "only", "own",
        "same", "so", "than", "too", "very", "just", "and", "but", "if", "or",
        "because", "until", "while", "although", "though", "after", "before",
        "this", "that", "these", "those", "i", "me", "my", "myself", "we",
        "our", "you", "your", "he", "him", "his", "she", "her", "it", "its",
        "they", "them", "their", "what", "which", "who", "whom", "use",
    }
    # Apply stemming and filter
    tokens = set()
    for w in words:
        if w in stopwords:
            continue
        # Keep abbreviations as-is (even if 2 chars)
        if w in ABBREVIATIONS:
            tokens.add(w)
        elif len(w) > 2:
            tokens.add(naive_stem(w))
    # Add any abbreviations found in original text
    tokens |= abbrevs
    expanded = set(tokens)
    for token in tokens:
        expanded |= SYNONYM_MAP.get(token, set())
    return expanded


def calculate_match_score(phrase: str, description: str) -> Tuple[float, List[str]]:
    """Calculate how well a phrase matches the description.

    Returns (score 0-1, list of matching terms).
    """
    phrase_tokens = tokenize(phrase)
    desc_tokens = tokenize(description)

    if not phrase_tokens:
        return 0.0, []

    matching = phrase_tokens & desc_tokens
    score = len(matching) / len(phrase_tokens)

    return score, sorted(matching)


def analyze_triggers(
    description: str,
    triggers: List[str],
    anti_triggers: List[str],
) -> dict:
    """Analyze trigger and anti-trigger effectiveness."""
    results = {
        "description": description,
        "trigger_results": [],
        "anti_trigger_results": [],
        "issues": [],
        "suggestions": [],
    }

    desc_tokens = tokenize(description)

    # Analyze triggers
    for trigger in triggers:
        score, matches = calculate_match_score(trigger, description)
        status = "STRONG" if score >= 0.5 else "WEAK" if score >= 0.2 else "POOR"
        results["trigger_results"].append({
            "phrase": trigger,
            "score": round(score, 2),
            "status": status,
            "matching_terms": matches,
        })

        if status == "POOR":
            trigger_tokens = tokenize(trigger)
            missing = trigger_tokens - desc_tokens
            if missing:
                results["suggestions"].append(
                    f"Trigger '{trigger}' uses terms not in description: {missing}. "
                    f"Consider adding these to description."
                )

    # Analyze anti-triggers
    for anti in anti_triggers:
        score, matches = calculate_match_score(anti, description)
        # For anti-triggers, we WANT low scores
        if score >= 0.4:
            status = "DANGER"
            results["issues"].append(
                f"Anti-trigger '{anti}' has high match score ({score:.2f}). "
                f"May incorrectly activate. Matching terms: {matches}"
            )
        elif score >= 0.2:
            status = "WARNING"
        else:
            status = "GOOD"

        results["anti_trigger_results"].append({
            "phrase": anti,
            "score": round(score, 2),
            "status": status,
            "matching_terms": matches,
        })

    # Check for trigger coverage
    all_trigger_tokens: Set[str] = set()
    for trigger in triggers:
        all_trigger_tokens |= tokenize(trigger)

    # Find important terms in description not covered by triggers
    uncovered = desc_tokens - all_trigger_tokens
    important_uncovered = {t for t in uncovered if len(t) > 4}
    if important_uncovered:
        results["suggestions"].append(
            f"Description contains terms not in any trigger: {important_uncovered}. "
            f"Consider adding triggers that use these terms."
        )

    # Check trigger diversity
    trigger_overlap = []
    for i, t1 in enumerate(triggers):
        for t2 in triggers[i + 1:]:
            t1_tokens = tokenize(t1)
            t2_tokens = tokenize(t2)
            if t1_tokens and t2_tokens:
                overlap = len(t1_tokens & t2_tokens) / max(len(t1_tokens), len(t2_tokens))
                if overlap > 0.7:
                    trigger_overlap.append((t1, t2, overlap))

    if trigger_overlap:
        results["issues"].append(
            f"Some triggers are too similar: {[(t1, t2) for t1, t2, _ in trigger_overlap]}. "
            f"Diversify trigger phrasing."
        )

    return results


def print_disclaimer() -> None:
    """Print disclaimer about tool limitations."""
    print("\n" + "-" * 60)
    print("NOTE: This tool uses word overlap heuristics, not semantic")
    print("matching. Results are approximate. Always verify skill")
    print("behavior with actual Claude usage.")
    print("-" * 60)


def print_results(results: dict) -> None:
    """Print analysis results in a readable format."""
    print_disclaimer()
    print("\n" + "=" * 60)
    print("TRIGGER ANALYSIS RESULTS")
    print("=" * 60)

    print(f"\nDescription: \"{results['description'][:100]}...\""
          if len(results['description']) > 100
          else f"\nDescription: \"{results['description']}\"")

    print("\n--- TRIGGER PHRASES ---")
    for tr in results["trigger_results"]:
        icon = "✓" if tr["status"] == "STRONG" else "⚠" if tr["status"] == "WEAK" else "✗"
        print(f"{icon} [{tr['status']:6}] (score: {tr['score']:.2f}) \"{tr['phrase']}\"")
        if tr["matching_terms"]:
            print(f"          Matching: {tr['matching_terms']}")

    print("\n--- ANTI-TRIGGER PHRASES ---")
    for ar in results["anti_trigger_results"]:
        icon = "✓" if ar["status"] == "GOOD" else "⚠" if ar["status"] == "WARNING" else "✗"
        print(f"{icon} [{ar['status']:7}] (score: {ar['score']:.2f}) \"{ar['phrase']}\"")
        if ar["matching_terms"] and ar["status"] != "GOOD":
            print(f"          Matching: {ar['matching_terms']}")

    if results["issues"]:
        print("\n--- ISSUES ---")
        for issue in results["issues"]:
            print(f"⚠ {issue}")

    if results["suggestions"]:
        print("\n--- SUGGESTIONS ---")
        for sug in results["suggestions"]:
            print(f"→ {sug}")

    # Summary
    strong = sum(1 for t in results["trigger_results"] if t["status"] == "STRONG")
    weak = sum(1 for t in results["trigger_results"] if t["status"] == "WEAK")
    poor = sum(1 for t in results["trigger_results"] if t["status"] == "POOR")

    print("\n--- SUMMARY ---")
    print(f"Triggers: {strong} strong, {weak} weak, {poor} poor")

    danger = sum(1 for a in results["anti_trigger_results"] if a["status"] == "DANGER")
    if danger:
        print(f"⚠ {danger} anti-trigger(s) may cause false activations!")

    if poor == 0 and danger == 0 and not results["issues"]:
        print("✓ Trigger configuration looks good!")
    else:
        print("Consider addressing the issues and suggestions above.")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Test skill triggers against description for activation likelihood."
    )
    ap.add_argument("skill_dir", help="Path to the skill folder")
    ap.add_argument("--json", action="store_true", help="Output results as JSON")
    args = ap.parse_args()

    skill_dir = Path(args.skill_dir).expanduser().resolve()
    spec_path = skill_dir / "skill.spec.json"

    description = ""
    triggers = []
    anti_triggers = []

    if spec_path.exists():
        try:
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            description = spec.get("description", "")
            triggers = spec.get("triggers", [])
            anti_triggers = spec.get("anti_triggers", [])
        except Exception as e:
            print(f"Error reading spec: {e}")
            raise SystemExit(1)
    else:
        print(f"No skill.spec.json found at {spec_path}")
        print("This tool requires skill.spec.json with triggers and anti_triggers.")
        raise SystemExit(1)

    if not triggers:
        print("No triggers defined in skill.spec.json")
        raise SystemExit(1)

    if not description:
        print("Error: skill.spec.json must include 'description' field.")
        print("The description is required for trigger analysis.")
        raise SystemExit(1)

    results = analyze_triggers(description, triggers, anti_triggers)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_results(results)


if __name__ == "__main__":
    main()
