# MCP vs code (code-first rubric)

## Default rule
Code execution is the default. MCP is the special case.

## Decision table

Choose code-first wrappers when ALL are true:
- You can reach the system from the execution environment (network/CLI/files).
- There is a stable SDK/HTTP API/CLI.
- Auth can be handled without leaking secrets into prompts (env vars, secret store).
- The workflow benefits from local processing (filtering, joins, parsing, file generation).

Choose MCP when ANY are true:
1) Secret isolation requirement
2) Network boundary (sandbox cannot reach, MCP server can)
3) Cross-client interoperability
4) Non-API or messy integration
5) Huge tool surface + standard discovery

## Convert MCP to code-first pattern

Even when using MCP:
1) Wrap MCP calls behind local functions.
2) Orchestrate in code (loops/retries/batching).
3) Keep raw outputs on disk, surface summaries to the model.
4) Provide one script entrypoint.

Result: token efficiency, safer data handling, and simpler reasoning.
