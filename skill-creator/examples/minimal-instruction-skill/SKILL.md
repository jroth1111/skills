---
name: minimal-instruction-skill
description: Demonstrates a minimal valid skill with only SKILL.md. Use when learning the simplest skill structure or creating instruction-only skills.
---

# Minimal Instruction Skill

This example shows the simplest valid skill structure per the official Anthropic specification.

## What Makes This Valid

A valid skill only requires:
1. A SKILL.md file
2. YAML frontmatter with `name` and `description`
3. Instructions in the body

Everything else (scripts, spec files, references) is optional.

## When to Use This Pattern

Use instruction-only skills when:
- You want to encode expertise or conventions without code
- The skill provides guidance rather than automation
- You're teaching Claude a specific workflow or style

## Example Instructions

When reviewing code:
1. Check for security issues first
2. Look for performance problems
3. Suggest improvements to readability
4. Note any missing tests

## See Also

For skills with scripts and automation, see the `generating-commit-messages` example.
