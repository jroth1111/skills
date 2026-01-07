#!/usr/bin/env python3
"""Unit tests for analyze_triggers.py."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyze_triggers import tokenize, calculate_match_score, analyze_triggers, naive_stem


class TestNaiveStem:
    """Tests for the naive_stem function."""

    def test_strips_s(self):
        """Should strip trailing 's' from plurals."""
        assert naive_stem("reviews") == "review"
        assert naive_stem("requests") == "request"
        assert naive_stem("changes") == "change"

    def test_strips_es(self):
        """Should strip 'es' from words ending in es."""
        assert naive_stem("boxes") == "box"
        assert naive_stem("matches") == "match"

    def test_strips_ed(self):
        """Should strip 'ed' from past tense."""
        assert naive_stem("reviewed") == "review"
        assert naive_stem("changed") == "chang"  # Not perfect, but close enough

    def test_strips_ing(self):
        """Should strip 'ing' from gerunds."""
        assert naive_stem("reviewing") == "review"
        assert naive_stem("checking") == "check"

    def test_preserves_short_words(self):
        """Should not stem very short words."""
        assert naive_stem("run") == "run"
        assert naive_stem("the") == "the"

    def test_ies_to_y(self):
        """Should convert 'ies' to 'y'."""
        assert naive_stem("policies") == "policy"


class TestTokenize:
    """Tests for the tokenize function."""

    def test_filters_stopwords(self):
        """Common stopwords should be filtered out."""
        tokens = tokenize("the quick brown fox")
        assert "the" not in tokens
        assert "quick" in tokens
        assert "brown" in tokens
        assert "fox" in tokens

    def test_lowercase(self):
        """All tokens should be lowercase."""
        tokens = tokenize("The QUICK Brown FOX")
        assert all(t.islower() for t in tokens)
        assert "quick" in tokens

    def test_filters_short_words(self):
        """Words with 2 or fewer chars should be filtered."""
        tokens = tokenize("I am a go to be")
        assert "am" not in tokens
        assert "go" not in tokens

    def test_extracts_significant_terms(self):
        """Should extract significant terms from realistic text with stemming."""
        tokens = tokenize("Reviews pull requests for code quality")
        # "reviews" stems to "review", "requests" stems to "request"
        assert "review" in tokens
        assert "pull" in tokens
        assert "request" in tokens
        assert "code" in tokens
        assert "quality" in tokens
        # 'for' is a stopword
        assert "for" not in tokens

    def test_preserves_abbreviations(self):
        """Should preserve common abbreviations like PR, CI, API."""
        tokens = tokenize("Review this PR and check the CI pipeline")
        assert "pr" in tokens
        assert "ci" in tokens
        assert "review" in tokens


class TestCalculateMatchScore:
    """Tests for the calculate_match_score function."""

    def test_perfect_match(self):
        """Identical meaningful words should score 1.0."""
        score, matches = calculate_match_score(
            "review code",
            "review code"
        )
        assert score == 1.0
        assert "review" in matches
        assert "code" in matches

    def test_partial_match(self):
        """Partial overlap should give score between 0 and 1."""
        score, matches = calculate_match_score(
            "review my code",
            "analyze your code"
        )
        # Only "code" matches
        assert 0 < score < 1
        assert "code" in matches

    def test_no_match(self):
        """No overlap should score 0."""
        score, matches = calculate_match_score(
            "write tests",
            "deploy servers"
        )
        assert score == 0.0
        assert len(matches) == 0

    def test_empty_phrase(self):
        """Empty phrase (after filtering) should score 0."""
        score, matches = calculate_match_score(
            "the a an",  # All stopwords
            "some description"
        )
        assert score == 0.0

    def test_realistic_trigger(self):
        """With stemming, inflections like 'review'/'reviews' should match."""
        score, matches = calculate_match_score(
            "review my PR",
            "Reviews pull requests for code quality. Use when reviewing PRs or checking code changes."
        )
        # "review" stems to "review", "reviews"/"reviewing" stem to "review"
        # "PR" is preserved as abbreviation
        assert score > 0.5  # Should have good match now
        assert "review" in matches or "pr" in matches


class TestAnalyzeTriggers:
    """Tests for the analyze_triggers function."""

    def test_returns_expected_structure(self):
        """Result should have expected keys."""
        result = analyze_triggers(
            description="Test skill description",
            triggers=["trigger one"],
            anti_triggers=["anti trigger one"],
        )
        assert "description" in result
        assert "trigger_results" in result
        assert "anti_trigger_results" in result
        assert "issues" in result
        assert "suggestions" in result

    def test_scores_triggers(self):
        """Each trigger should get a score and status."""
        result = analyze_triggers(
            description="Reviews code for quality issues",
            triggers=["review my code", "check code quality"],
            anti_triggers=[],
        )
        assert len(result["trigger_results"]) == 2
        for tr in result["trigger_results"]:
            assert "phrase" in tr
            assert "score" in tr
            assert "status" in tr
            assert tr["status"] in ("STRONG", "WEAK", "POOR")

    def test_warns_on_high_anti_trigger_score(self):
        """Anti-triggers with high match scores should generate issues."""
        result = analyze_triggers(
            description="Reviews pull requests",
            triggers=["review PR"],
            anti_triggers=["review pull request"],  # High overlap - with stemming, all 3 words match
        )
        # With stemming: "review" matches "review", "pull" matches "pull", "request" matches "request"
        # Score should be 1.0 (100% match) which triggers DANGER status
        danger_count = sum(
            1 for a in result["anti_trigger_results"]
            if a["status"] == "DANGER"
        )
        assert danger_count > 0, f"Expected DANGER status, got: {result['anti_trigger_results']}"
        assert len(result["issues"]) > 0, f"Expected issues, got: {result['issues']}"

    def test_detects_similar_triggers(self):
        """Similar triggers should generate an issue."""
        result = analyze_triggers(
            description="Reviews code",
            triggers=[
                "review this code",
                "review my code",
                "review the code",
            ],
            anti_triggers=[],
        )
        # Should detect similarity
        similar_issue = any("similar" in issue.lower() for issue in result["issues"])
        assert similar_issue or len(result["issues"]) > 0


if __name__ == "__main__":
    # Run basic tests
    import pytest
    pytest.main([__file__, "-v"])
