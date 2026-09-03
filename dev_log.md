# Development Log

## [2026-09-03]
- Upgraded `FastMCP` to `MCPServer` in `server.py` to fix compatibility issues with MCP 2.x API.
- Added `.gitignore` to prevent tracking the `.venv` directory.
- Debugged silent failures with `opencode-cli` on Windows attempting to run `server.py` over `stdio`.
- Switched `server.py` to use Server-Sent Events (SSE) HTTP transport on port 8000.
- Updated `opencode.json` configuration to `"type": "remote"` pointing to `http://127.0.0.1:8000/sse`, successfully exposing `ask_question` and `ingest_data` tools to the CLI.
