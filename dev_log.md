# Development Log

## [2026-09-03]
- Upgraded `FastMCP` to `MCPServer` in `server.py` to fix compatibility issues with MCP 2.x API.
- Added `.gitignore` to prevent tracking the `.venv` directory.
- Debugged silent failures with `opencode-cli` on Windows attempting to run `server.py` over `stdio`.
- Switched `server.py` to use Server-Sent Events (SSE) HTTP transport on port 8000.
- Updated `opencode.json` configuration to `"type": "remote"` pointing to `http://127.0.0.1:8000/sse`, successfully exposing `ask_question` and `ingest_data` tools to the CLI.

- Replaced monolithic `ingest_data` and `ask_question` with 5 atomic tools: `convert_office_to_pdf`, `extract_pdf_pages`, `index_images_to_qdrant`, `search_visual_knowledge_base`, and `analyze_image`.
- Implemented Vision-RAG ColPali embeddings and Qdrant multi-vector payload storage.
- Added `fetch_doc` and `fetch_page` support to `search_visual_knowledge_base` to support exact `<FETCH_PAGE>` requirements.
- Configured `.env` and `config.yaml` for tool parameterization and secret management.
- Re-validated against `REQUIREMENTS.md`. All dependencies and agent orchestrator rules are aligned.
- Replaced mock placeholder in analyze_image with actual live HTTP calls to FM Gateway.
- Removed all hardcoded model and URL fallbacks in server.py, strictly enforcing configuration via .env variables (FM_GATEWAY_URL, VLM_MODEL, VISION_RETRIEVER_MODEL).
