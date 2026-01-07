# Decision rubric (archetype selection)

Golden rule: code execution is the default. MCP is the special case.

Quick decision tree:

Is this local processing (files, transforms, codegen)?
- YES -> basic
- NO -> Can you reach the system via HTTP/SDK?
  - YES -> api-wrapper
  - NO -> Is MCP required and you still need orchestration?
    - YES -> mcp-bridge
    - NO -> reconsider basic or api-wrapper

Archetype summary:
- basic: local transforms, scripts/main.py
- api-wrapper: HTTP/SDK wrappers, scripts/wrapper.py
- mcp-bridge: MCP stdio bridge, scripts/bridge.py
