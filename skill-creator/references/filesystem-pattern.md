# Filesystem pattern

Problem: tools and MCP servers can return huge payloads. Dumping them into the conversation:
- burns tokens
- hurts reasoning quality
- creates poor UX

Solution: treat the filesystem as long-term memory and the context window as working memory.

Rules:
1. Never print data > 1KB to stdout
2. Always save raw data to workspace/
3. Print only summaries, artifact paths, and tiny previews

Example (bad):
```python
response = api.fetch_all_items()
print(json.dumps(response, indent=2))  # Could be megabytes
```

Example (good):
```python
from _fs import write_json, safe_preview_json

response = api.fetch_all_items()
path = write_json("items.json", response)

print(f"Saved {len(response['items'])} items to {path}")
print(f"Preview: {safe_preview_json(response['items'][:2], max_bytes=512)}")
```

workspace/ rules:
- must be gitignored
- scripts should create it (use _fs.py)
- never read/write outside unless explicitly required
