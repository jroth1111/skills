# Discipline Skill Testing

Use this when a skill enforces rules that are costly or tempting to bypass
(for example, TDD, verification-before-completion, security checks).

## Why this matters

If you did not watch an agent fail without the skill, you do not know whether
the skill prevents the right failure modes.

## Minimal loop (TDD-style)

1) Baseline (RED): run a pressure scenario without the skill.
2) Capture: record the exact rationalizations or shortcuts.
3) Write minimal guidance: address those specific failures.
4) Re-test (GREEN): run the same scenario with the skill.
5) Refine (REFACTOR): plug new loopholes and re-test.

## Pressure scenario checklist

- Force a concrete choice (A/B/C), not an essay.
- Combine 2-3 pressures: time, sunk cost, authority, fatigue.
- Make it realistic and specific (paths, deadlines, stakes).

## Output artifacts

- A short list of rationalizations to explicitly counter.
- Updated rules that forbid the specific shortcuts.
- A re-test log that shows the skill now holds under pressure.
