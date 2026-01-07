# Validation pipeline (cheap to expensive)

1) Structure validation (mandatory)
- frontmatter keys, name/description, link checks
- skill.spec.json and entry_point required only with --strict
Tool: python {baseDir}/scripts/validate_skill.py <skill-dir> [--strict]
Note: validate_skill.py only syntax-checks Python files under scripts/. For other languages,
run the appropriate linters or compilers manually.

2) Static safety scan (mandatory)
- secrets, injection strings, dangerous commands
Tool: python {baseDir}/scripts/security_scan.py <skill-dir>

3) Smoke tests (recommended)
- run the main script on fixtures

4) Judge pass (optional but smart)
- separate reviewer checks spec vs behavior

5) Differential/property tests (optional)
- golden outputs, property checks

Discipline-enforcing skills: add pressure scenarios and re-test to ensure compliance
under time, authority, or sunk-cost pressure. See references/discipline-testing.md.
