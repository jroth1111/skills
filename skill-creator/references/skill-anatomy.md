# Skill anatomy

A code-first skill is a self-contained folder with this structure:

```
my-skill/
|-- SKILL.md
|-- skill.spec.json
|-- requirements.txt        # if needed
|-- scripts/
|   |-- main.py             # or wrapper.py / bridge.py
|   `-- _fs.py
|-- tests/
|   `-- smoke_prompts.md
`-- workspace/              # runtime artifacts (gitignored)
```

Notes:
- SKILL.md contains frontmatter and usage instructions
- skill.spec.json is the contract for triggers and entry points
- workspace/ holds raw data and artifacts, never committed
