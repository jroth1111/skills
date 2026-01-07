# skill.spec.json

A small, machine-readable contract so you do not ship vague Skills.

Minimal schema:
```json
{
  "name": "my-skill-name",
  "title": "Human Title",
  "description": "What + when",
  "archetype": "api-wrapper|basic|mcp-bridge",
  "risk_level": "low|medium|high",
  "entry_point": "scripts/main.py",
  "triggers": ["..."],
  "anti_triggers": ["..."],
  "acceptance_tests": ["..."]
}
```

Keep it short and reviewable in under 30 seconds.
