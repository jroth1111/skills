# Skill Creator Reference

This file is intentionally detailed. Keep SKILL.md short and link to reference material like this.

## Official Spec vs skill-creator Extensions

### Official Anthropic Specification (always valid)

Per the official Anthropic documentation, a valid skill requires only:

- **SKILL.md** with YAML frontmatter containing:
  - `name` (required): lowercase, hyphens, numbers, max 64 chars; tooling rejects reserved words "anthropic" and "claude"
  - `description` (required): max 1024 chars, describes what + when
  - `license` (optional): license name or reference
  - `compatibility` (optional): environment requirements (max 500 chars)
  - `metadata` (optional): key/value mapping
- `allowed-tools` (optional): space-delimited tool allowlist (experimental)

Everything in the SKILL.md body is instructions. Scripts, reference files, and additional structure are optional.
Note: validate_skill uses a lenient frontmatter parser by default; if PyYAML is installed, it uses strict YAML parsing.
If skill.spec.json includes `allowed_tools`, keep it in sync with `allowed-tools` in SKILL.md.

### skill-creator Extensions (recommended, not required)

This tooling adds helpful conventions beyond the official spec:

| Feature | Purpose | Required? |
|---------|---------|-----------|
| `skill.spec.json` | Machine-readable triggers, tests, metadata | No (use `--strict` to require) |
| Archetypes | Scaffolding patterns (basic, api-wrapper, mcp-bridge) | No |
| `scripts/` directory | Executable utilities | No |
| `workspace/` pattern | Token-efficient data handling | No |
| `references/` directory | Progressive disclosure of docs | No |
| Extra frontmatter fields (`model`, `dependencies`, `version`) | Claude Code-specific hints | No |

Minimal scaffolding is available via `{baseDir}/scripts/forge.py --minimal` (SKILL.md only).

### Validation Modes

- **Default mode**: Validates only official spec (SKILL.md with name + description)
- **Strict mode** (`--strict`): Also requires skill.spec.json and entry_point

Use default mode for simple instruction-only skills. Use strict mode for complex skills with scripts and automation.

## 1) The good Skill checklist

A Skill is good when it is:
- Discoverable: description says what + when with concrete triggers.
- Focused: one workflow, not a grab-bag.
- Composable: does not assume it is the only Skill in the world.
- Deterministic where it matters: scripts handle parsing, formatting, API calls, generation.
- Safe by default: least privilege tools, no secrets, explicit confirmation steps for risky actions.
- Tested: has trigger prompts, anti-triggers, and at least one smoke run.
- Effective: passes acceptance tests and produces intended outcomes.

## 1.5) Effectiveness criteria

An effective skill:
1. **Triggers correctly**: Activates when it should, doesn't when it shouldn't
2. **Produces intended outcomes**: Meets all acceptance tests
3. **Is testable**: Has verifiable, observable behaviors
4. **Collects feedback**: Asks user if outcome was satisfactory

### Measuring effectiveness

Run the evaluation tool:
```bash
python {baseDir}/scripts/evaluate_skill.py <skill-dir>
```

Minimum quality bar:
- 5 diverse trigger phrases (not just rephrased versions)
- 3 anti-trigger phrases (similar but different intent)
- 3 specific, observable acceptance tests
- All acceptance tests pass when evaluated

Rationale: five triggers capture common phrasing variants, three anti-triggers
set clear boundaries, and three acceptance tests cover the core outcomes.

### Common effectiveness problems

| Problem | Symptom | Fix |
|---------|---------|-----|
| Doesn't trigger | Skill never activates | Add trigger terms to description |
| Wrong trigger | Activates for wrong requests | Add anti-triggers, narrow description |
| Vague output | User doesn't know if it worked | Add specific acceptance tests |
| No feedback loop | Can't improve over time | Add "Did this help?" prompt |

## 1.6) Conciseness and degrees of freedom

Keep only non-obvious information. Assume Claude is capable and remove background
that does not change behavior.

Match strictness to task fragility:
- High freedom: text guidance when multiple approaches are valid.
- Medium freedom: pseudocode or parameterized scripts when a preferred pattern exists.
- Low freedom: fixed scripts and exact steps when operations are fragile or high-risk.

## 2) Description formula

A good description contains:
1) Verb + object: "Generate release notes from git history"
2) When clause: "Use when the user mentions changelogs, releases, or version bumps"
3) Concrete triggers: file extensions, domain terms, system names
4) Boundaries: "Not for marketing copy" / "Read-only" / "No external posting"

Example:
"Generate concise commit messages from staged git diffs. Use when writing commits or reviewing staged changes in git. Not for rewriting history or force-pushing."

Why this matters: the model decides to load a Skill primarily from description.
Do not rely on the SKILL.md body to trigger activation; the body is loaded only
after the skill is selected.

### Keyword coverage checklist

- Symptoms and user phrasing
- Error messages (if applicable)
- Tools, systems, or file types
- Common synonyms or variants

## 3) Archetypes

- basic: local transforms, parsing, codegen
- api-wrapper: HTTP/SDK calls you can reach from code
- mcp-bridge: MCP required with orchestration in code

See references/decision-rubric.md for how to choose.

## 3.1) How Skills Work in Claude Code

Skills are model-invoked. No explicit call is required.

1. Discovery: Load only skill names and descriptions at startup.
2. Activation: Match requests to descriptions and ask for confirmation before loading SKILL.md.
3. Execution: Follow SKILL.md instructions and load or run supporting files as needed.
4. Composition: Claude may activate multiple relevant Skills in one session.

## 3.2) When to Use Skills vs Other Options

- Skills: Add specialized knowledge or standards that Claude applies automatically.
- Slash commands: Reusable prompts you invoke explicitly.
- CLAUDE.md: Project-wide instructions loaded into every conversation.
- Subagents: Separate context with their own tools and optional preloaded Skills.
- Hooks: Run scripts on tool or lifecycle events.
- MCP servers: Provide external tools or data sources; Skills describe how to use them.

## 3.3) Where Skills Live and Precedence

- Enterprise: Managed settings for the organization.
- Personal: ~/.claude/skills/
- Project: .claude/skills/
- Plugin: skills/ at the plugin root

If two Skills share the same name, precedence is enterprise > personal > project > plugin.

## 3.4) Automation (CLI)

- One-shot runs: claude -p "<prompt>" (or --print).
- Permission modes: --permission-mode acceptEdits or bypassPermissions for automation.
- Tool whitelisting: --allowedTools "Read,Write,Edit,Bash(npm test)".
- Structured output: --output-format json or stream-json.
- Multi-turn: --continue or --resume <session_id>.

## 3.5) Deployment and installation

**Local use (Claude Code):**
- Place the skill folder in `~/.claude/skills/` (personal) or `.claude/skills/` (project).
- Restart or reload skills to pick up changes.

**Plugin distribution (optional):**
- Only needed when bundling multiple skills as a plugin.
- If you bundle, include `.claude-plugin/marketplace.json` at the plugin root.
- Install via your environment’s plugin command (for example, `/plugin marketplace add <path>` in Claude Code).

**Packaged .skill files:**
- `{baseDir}/scripts/package_skill.py` creates a `.skill` (zip) for distribution (add `--scan` to run security scan first).
- Install/upload depends on the target platform; keep the unzipped folder for local use.

## 4) Skill anatomy

See references/skill-anatomy.md for the expected folder structure.

## 4.5) Keep skill files lean

Only include files that directly support the skill. Avoid extra docs like
README.md, CHANGELOG.md, or setup guides unless they are required for execution.
Put detailed reference material under references/ instead of expanding SKILL.md.

## 4.6) Optional structure for data-processing skills

A helpful, optional outline for data-processing skills:
- Capabilities
- Input requirements
- Output formats
- Limitations

## 5) Filesystem pattern

Treat the filesystem as long-term memory and the context window as working memory:
- Save raw data to workspace/
- Print only summaries and small previews to stdout
- Never dump large payloads into the conversation

See references/filesystem-pattern.md.

## 5.1) Pattern guides

- For workflow sequencing and branching, see [references/workflows.md](references/workflows.md).
- For output templates and examples, see [references/output-patterns.md](references/output-patterns.md).

## 5.2) Flowchart usage

Use flowcharts only for non-obvious decision points. Prefer lists for linear
steps and code blocks for examples.

## 6) Validation ladder (cheap to expensive)

1. Structure: frontmatter, required fields (name, description), naming rules
2. Spec checks (strict mode): skill.spec.json, entry_point exists
3. Static scan: secrets, dangerous shell patterns, path traversal
4. Smoke tests: run the main script on fixtures
5. Judge pass: separate reviewer checks spec vs behavior
6. Differential/property tests (optional): golden outputs, property checks

See references/validation-pipeline.md.
For discipline-enforcing skills, run pressure scenarios; see
[references/discipline-testing.md](references/discipline-testing.md).

## 6.1) Fixtures and hygiene (optional)

- For code-first skills, add tiny fixtures under tests/ (for example,
  sample_input.json and expected_output.json) to smoke-test scripts.
- Before packaging, remove caches and temporary files (for example, __pycache__/,
  *.pyc, *.tmp).
- For workspace cleanup, use python {baseDir}/scripts/clean_workspace.py --skill-dir <skill-dir> (add --dry-run to preview).

## 7) Prompt-injection defense notes

Treat Skill files like code:
- Keep instructions explicit and short.
- Never embed untrusted text as instructions.
- Do not auto-run commands generated from untrusted inputs.
- Scan for obvious injection strings and secrets.

See references/security.md.

## 8) Tool Limitations

The skill-creator tools help prepare and organize skills, but they are not substitutes for actual testing with Claude. Understanding their limitations is critical.

### analyze_triggers.py

This is a **preparation tool**, not a testing tool. It uses word overlap heuristics.

**What it CAN do:**
- Find obvious mismatches between triggers and description
- Detect triggers that are too similar to each other
- Warn when anti-triggers might falsely activate
- Suggest terms to add to descriptions

**What it CANNOT do:**
- Predict how Claude will actually interpret triggers
- Test semantic similarity (only word overlap)
- Guarantee that triggers will work
- Handle synonyms ("PR" vs "pull request" won't match)

**Interpreting scores:**
- A score of 0 doesn't mean the trigger won't work - it just means no words overlap
- A score of 1.0 doesn't guarantee activation - Claude uses semantic understanding

### evaluate_skill.py

This is a **manual verification checklist**, not automated testing.

**What it CAN do:**
- Guide you through systematic verification of acceptance tests
- Track evaluation results over time
- Generate test case templates

**Automation assist**:
- `--auto` runs static checks (strict validation + trigger analysis + case coverage)
- `--non-interactive` skips prompts (useful for CI), but still does not run live Claude tests

**What it CANNOT do:**
- Automatically run skills
- Verify behavior without human observation
- Replace actual usage testing with Claude

### Recommended Workflow

1. **Preparation phase** (use tools):
   - Use `forge.py` to scaffold with quality prompts
   - Use `analyze_triggers.py` to catch obvious issues
   - Use `validate_skill.py` to check structure

2. **Testing phase** (use Claude):
   - Deploy skill and test with real prompts
   - Try all trigger phrases manually
   - Verify anti-triggers don't activate

3. **Verification phase** (use tools + judgment):
   - Use `evaluate_skill.py` to systematically check results
   - Record what worked and what didn't
   - Collect user feedback

4. **Iteration**:
   - Update skill based on actual behavior, not tool predictions
   - Re-run preparation tools after significant changes
   - Track improvement over evaluation sessions
