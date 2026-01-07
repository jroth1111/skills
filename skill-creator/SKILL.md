---
name: skill-creator
description: Create, scaffold, validate, and package Claude Code skills and SKILL.md/spec files. Use when building skill folders, tuning triggers, or packaging .skill files. Not for app features or incidents.
allowed-tools: Read Write Edit Grep Glob Bash
---

# Skill Creator

## Purpose

Provide a code-first workflow for authoring Agent Skills in Claude Code, including archetypes, filesystem pattern rules, specs, validation, and packaging.

## Skill Quality Targets

- Composable: can be chained together as part of larger workflows.
- Token-efficient: lightweight and focused, not bloated with unused tools or repeated instructions.
- Narrow and outcome-focused: single responsibility with a crisp success criterion.

## Conciseness and Degrees of Freedom

Keep only non-obvious information. Assume Claude is already capable and remove
background that does not change behavior.

Match strictness to task fragility:
- High freedom: text guidance when multiple approaches are valid.
- Medium freedom: pseudocode or parameterized scripts when a preferred pattern exists.
- Low freedom: fixed scripts and exact steps when operations are fragile or high-risk.

## Skill Types

- A workflow: step-by-step instructions (for example, navigate, capture, extract).
- Expertise: domain knowledge and conventions (for example, how your team implements a feature).
- Both: instructions plus tools and best practices bundled together.

## Quality-First Workflow

Creating an effective skill requires systematic attention to triggers, acceptance criteria, and testing. Follow this complete workflow:

Start by collecting 2-3 concrete example user requests. Use them to shape triggers and acceptance tests.

### Step 1: Scaffold with Quality Prompts
```bash
python {baseDir}/scripts/forge.py --interactive
```
Primary entry point. If the target folder exists, it stops unless you pass --force.
The wizard guides you through:
- Description building (what + when + boundaries)
- Concrete example user requests (aim for 2-3)
- 5 diverse trigger phrases
- 3 anti-trigger phrases
- 3 specific, observable acceptance tests

Non-interactive alternative (for automation):
```bash
python {baseDir}/scripts/forge.py --from-spec spec.json
```

### Step 2: Validate Structure
```bash
python {baseDir}/scripts/validate_skill.py path/to/skill-folder
```
Use `--strict` to require skill.spec.json and entry_point.

### Step 3: Test Trigger Matching
```bash
python {baseDir}/scripts/analyze_triggers.py path/to/skill-folder
```
Verifies triggers match description and anti-triggers don't cause false activations.
Note: analyze_triggers uses word-overlap heuristics with naive stemming; confirm activation with real usage.

### Step 4: Evaluate Effectiveness
```bash
python {baseDir}/scripts/evaluate_skill.py path/to/skill-folder
```
Interactive verification of acceptance tests and test cases.
Use --auto for static checks, or --non-interactive for CI-only runs.

### Step 5: Security Scan
```bash
python {baseDir}/scripts/security_scan.py path/to/skill-folder
```
Use `--exit-nonzero` for CI pipelines that should fail on findings.

### Step 6: Package
```bash
python {baseDir}/scripts/package_skill.py path/to/skill-folder [output-directory]
```
Add `--scan` to run the security scan before packaging.

### Bulk Operations
```bash
python {baseDir}/scripts/audit_skills.py --skills-dir ~/.claude/skills
```

## Description Formula

A good description determines when the skill activates. Follow this pattern:

```
[What it does]. Use when [trigger conditions]. Not for [boundaries].
```

**Example:**
```
Reviews pull requests for security and code quality. Use when reviewing PRs,
checking code changes, or giving feedback on diffs. Not for writing new code.
```

Activation depends on the frontmatter description. Do not rely on a "When to Use"
section in the body to trigger a skill.

**Key elements:**
1. **What**: Verb + object (third-person present)
2. **When**: Specific trigger conditions users might say
3. **Boundaries**: What the skill should NOT handle

**Keyword coverage checklist:**
- Symptoms and user phrasing (what they say)
- Error messages or failures (if applicable)
- Key tools, systems, or file types
- Common synonyms or variants

## Trigger Discovery

Triggers determine if the skill activates correctly. Collect diverse phrases:

**Good triggers (varied phrasing):**
- "Review this PR"
- "What do you think of these changes?"
- "Check my code"
- "Give feedback on this diff"
- "Look over my pull request"

**Bad triggers (too similar):**
- "Review this PR"
- "Review my PR"
- "Review the PR"
- "Can you review this PR?"
- "Please review my PR"

Analyze with: `python {baseDir}/scripts/analyze_triggers.py <skill-dir>`

## Acceptance Tests

Define observable, testable behaviors:

**Good (specific and verifiable):**
- "Mentions security issues before style issues"
- "Provides specific line numbers in feedback"
- "Asks for clarification when requirements are ambiguous"

**Bad (vague):**
- "Works well"
- "Gives good feedback"
- "Is helpful"

Test with: `python {baseDir}/scripts/evaluate_skill.py <skill-dir>`

## Runtime and Placement (see reference)

See references/reference.md for how skills load, where they live, and CLI automation details.

## Minimal Valid Skill

Per the official Anthropic specification, a valid skill only requires SKILL.md with YAML frontmatter containing `name` and `description`. Everything else is optional.

```yaml
---
name: my-skill
description: Does X. Use when Y.
---

# My Skill

Instructions for Claude go here.
```

See examples/minimal-instruction-skill/ for a complete example without scripts or spec file.
Use {baseDir}/scripts/forge.py --minimal to scaffold a minimal SKILL.md-only skill.

## Archetypes (choose one)

1) basic (local-only)
- Entry point: scripts/main.py
- Use for parsing, transforms, and codegen

2) api-wrapper (HTTP/SDK)
- Entry point: scripts/wrapper.py
- Use when you can reach a stable API from code

3) mcp-bridge (special case)
- Entry point: scripts/bridge.py
- Use when MCP is required but you still want orchestration in code

Archetypes are scaffolded from templates under templates/.
See references/decision-rubric.md for how to choose.

## Filesystem Pattern (recommended)

For skills that process data, follow this pattern to minimize token usage:

- Save raw data to workspace/
- Print only summaries and small previews to stdout (cap at ~1KB)
- Never dump large payloads into the conversation
- Use scripts/_fs.py helpers for JSON/text output

See references/filesystem-pattern.md.

## Spec File (recommended for complex skills)

For skills with scripts, triggers, and acceptance tests, add skill.spec.json with these fields:
- name, title, description
- archetype, risk_level, entry_point
- triggers, anti_triggers, acceptance_tests

See references/skill-spec.md.
See references/skill-anatomy.md for the expected folder layout.

## Frontmatter Rules

- SKILL.md must start with YAML frontmatter on line 1 and end the frontmatter with ---.
- Required fields: name, description.
- Optional fields (spec): license, compatibility, metadata, allowed-tools.
- Extensions supported here: model, dependencies, version. Other keys are allowed but prefer metadata for custom fields.
- Frontmatter parsing is lenient by default; if PyYAML is installed, validation uses it for stricter YAML parsing.
- name: lowercase letters and numbers with single hyphens between words; max 64 characters; must match the directory name; must not contain reserved words "anthropic" or "claude".
- description: max 1024 characters; recommended under ~200; write in third-person present; include trigger terms and boundaries.
- allowed-tools is space-delimited and supports scoped patterns like Bash(git:*) or Bash(python:*).
- If the Skill requires external packages, list them in the description and dependencies.

## Skill Body Guidelines

- Use imperative language and make inputs explicit and structured (JSON snippets, bullet lists, or tables).
- Prefer structured fields over long prose when describing APIs or data models.
- Document required inputs: repo path, services involved, APIs, schemas, feature flags, and constraints.
- Design skills around a single responsibility (for example, implement a typed React UI for an existing endpoint), not "build the whole feature."
- Use {baseDir} for portable file paths in commands and references; avoid Windows-style backslashes.
- List required packages and install commands; keep dependencies explicit.
- For security-sensitive workflows, include explicit "never do" constraints and escalation conditions.
- Encode team conventions and guardrails: testing, observability, rollout requirements.
- Reference existing AGENTS.md, runbooks, or design docs instead of inlining everything.
- Require proof artifacts where relevant: tests, screenshots, log queries, or dashboard links.
- Assume large monorepos, multiple services, and layered approvals; be explicit about directories Droids may touch, languages/frameworks in-bounds, and cross-team dependency handling.
- Avoid extra docs like README/CHANGELOG; keep only files that directly support the skill.
- For workflow sequencing or branching, see [references/workflows.md](references/workflows.md). For output templates or examples, see [references/output-patterns.md](references/output-patterns.md).
- Use flowcharts only for non-obvious decision points; avoid them for linear steps or code.
- For data-processing skills, an optional outline is: Capabilities, Input Requirements, Output Formats, and Limitations.

## Composability and Idempotency

- Prefer several small skills composed by a Droid/agent over one giant "do everything" skill.
- Prefer idempotent steps; safe to rerun on the same branch/PR.
- Produce machine-parseable output when possible (for example, a short summary block other skills can consume).
- Keep skills stateless beyond the current branch; avoid hidden assumptions about prior runs.

## Verification Requirements

- Always include a "Verification" section listing commands Droids must run before completing the skill.
- Include fallbacks when verification fails (rollback steps, feature flags, canary paths).
- For production-adjacent skills, require opening PRs and never merging without human review.
- For discipline-enforcing skills, test with pressure scenarios; see [references/discipline-testing.md](references/discipline-testing.md).

## Validation and Security

- Validate: `python {baseDir}/scripts/validate_skill.py <skill-dir>`
- Security scan: `python {baseDir}/scripts/security_scan.py <skill-dir>`
- Keep SKILL.md under 500 lines; move details into references/
- Before packaging, remove caches and temporary files (for example, __pycache__/, *.pyc, *.tmp).
- Workspace cleanup: `python {baseDir}/scripts/clean_workspace.py --skill-dir <skill-dir>` (use --dry-run to preview).

See references/validation-pipeline.md and references/security.md.

## Verification

Run these commands before finishing a skill:

```bash
python {baseDir}/scripts/validate_skill.py <skill-dir> --strict
python {baseDir}/scripts/security_scan.py <skill-dir>
python {baseDir}/scripts/analyze_triggers.py <skill-dir>
python {baseDir}/scripts/evaluate_skill.py <skill-dir>
```

For a fast frontmatter sanity check only:
```bash
python {baseDir}/scripts/quick_validate.py <skill-dir>
```

## Scaffolding Options

- `{baseDir}/scripts/forge.py`: primary entry point; interactive scaffold with archetypes and spec generation (refuses to overwrite unless --force)
- `{baseDir}/scripts/forge.py --minimal`: minimal scaffold with SKILL.md only (no spec or scripts)
- `{baseDir}/scripts/forge.py --from-spec spec.json`: non-interactive scaffold from JSON spec file
- `{baseDir}/scripts/init_skill.py`: non-interactive scaffold (pass --archetype; add --trigger/--anti-trigger/--acceptance-test for a complete spec)
- `{baseDir}/scripts/quick_validate.py`: fast frontmatter sanity check (no spec enforcement)
Archetype options: basic, api-wrapper, mcp-bridge.

## Progressive Disclosure and Supporting Files

Use supporting files to keep the main SKILL.md focused.

- scripts/: executable utilities that can run without loading their contents into context
- references/: detailed documentation or specifications (link directly from SKILL.md)
- assets/: templates, boilerplate projects, fonts, images, or other files used in outputs
- tests/: smoke prompts or deterministic fixtures for quick validation (for example, sample_input.json and expected_output.json)
- workspace/: runtime artifacts (always gitignored)

For deeper guidance, see references/reference.md.

## Subagents

To preload Skills for custom subagents, list them in .claude/agents/<agent>/AGENT.md under skills:. Built-in agents do not automatically load Skills.

## Sharing and Security

- Treat Skills like code: version control, review, and keep scopes focused.
- Only install Skills from trusted sources; avoid hardcoding secrets.

## Intent Router

Common user requests and how to handle them:

**"Create a new skill"**
1. Collect skill name, description, and 2-3 example user requests
2. Run `python {baseDir}/scripts/forge.py --interactive` (or use `--from-spec` with JSON)
3. Run `python {baseDir}/scripts/validate_skill.py <skill-dir> --strict`
4. Run `python {baseDir}/scripts/analyze_triggers.py <skill-dir>`
5. Summarize results and suggest description/trigger edits if needed

**"My skill isn't activating"**
1. Read the skill's SKILL.md frontmatter and skill.spec.json
2. Run `python {baseDir}/scripts/analyze_triggers.py <skill-dir>`
3. Identify weak triggers and missing keywords
4. Propose specific edits to strengthen the description

**"Package this skill for sharing"**
1. Run `python {baseDir}/scripts/validate_skill.py <skill-dir> --strict`
2. Run `python {baseDir}/scripts/security_scan.py <skill-dir>`
3. Run `python {baseDir}/scripts/package_skill.py <skill-dir>`
4. Report the .skill file path

**"Review my skill for quality"**
1. Run all validation commands (validate, security, analyze, evaluate)
2. Summarize findings: structure issues, trigger quality, acceptance test coverage
3. Propose specific improvements

## Never Do

- Never overwrite an existing skill directory without explicit `--force` flag
- Never package files containing secrets (.env, .pem, private keys)
- Never include workspace/ artifacts or .git/ in packaged skills
- Never commit secrets or credentials to skill repositories
- Never execute untrusted user-provided scripts without review
- Never skip validation before packaging

## Troubleshooting

- Skill not triggering: Strengthen the description with specific capabilities and trigger terms.
- Skill not loading: Verify the path and SKILL.md filename, check YAML syntax, and run claude --debug.
- Scripts failing: Ensure execute permissions and dependencies are installed.
- Validation fails: Fix reported issues and re-run validate_skill.py --strict; use quick_validate.py for a quick frontmatter check.
- Plugin Skills not appearing: Clear ~/.claude/plugins/cache, reinstall the plugin, and verify skills/<skill-name>/SKILL.md exists at the plugin root.
