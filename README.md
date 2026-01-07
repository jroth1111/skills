# Skills

This repository contains a standalone, enhanced packaging of the `skill-creator` skill.

## How this differs from upstream

Upstream skill: https://github.com/anthropics/skills/tree/main/skills/skill-creator

This repo extends the upstream skill with a larger, code-first toolchain and supporting
assets. Key additions include:

- Guided scaffolding wizard (`skill-creator/scripts/forge.py`) with quality prompts,
  trigger/anti-trigger collection, acceptance tests, and `--from-spec` automation.
- Full validation pipeline (`skill-creator/scripts/validate_skill.py`) that checks
  frontmatter rules, spec fields, allowed-tools syntax, broken links, symlinks,
  Python syntax, and structural expectations.
- Trigger analysis (`skill-creator/scripts/analyze_triggers.py`) with stemming,
  synonym expansion, overlap scoring, and diversity checks.
- Manual effectiveness evaluation (`skill-creator/scripts/evaluate_skill.py`) with
  interactive checklists, auto checks, and optional test case coverage.
- Security and hygiene tooling (`skill-creator/scripts/security_scan.py`,
  `skill-creator/scripts/clean_workspace.py`, `skill-creator/scripts/audit_skills.py`).
- Archetype templates (`skill-creator/templates/`) for `basic`, `api-wrapper`, and
  `mcp-bridge`, plus example skills under `skill-creator/examples/` and tests under
  `skill-creator/tests/`.
- Extended reference library (`skill-creator/references/`) covering spec anatomy,
  validation pipeline, security guidance, filesystem patterns, workflows, and
  decision rubrics.
- A full `skill-creator/skill.spec.json` with triggers, acceptance tests, goals, and
  non-goals for higher-fidelity scaffolding and evaluation.

If you only need the canonical instructions, use upstream. If you want an opinionated,
production-focused toolkit for creating, validating, and packaging skills, use this repo.

## Quick start

```bash
cd skill-creator
python scripts/forge.py --interactive
```
