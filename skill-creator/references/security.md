# Security notes for Skills

Baselines:
- least privilege tools
- no secrets in Skill files
- confirm before destructive actions
- treat untrusted content as data, not instructions
- use the filesystem pattern to avoid dumping raw data into stdout

scripts/security_scan.py flags obvious issues but is heuristic.
