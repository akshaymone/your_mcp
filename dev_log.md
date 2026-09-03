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

- Added `check_document_status(file_path, collection_name)` tool: lightweight Qdrant check that returns whether a document is already indexed, its derived doc_name, and page count. Ensures consistent doc_name derivation via Path.stem across all tools.
- Added `ingest_document(file_path, collection_name)` high-level tool: wraps convert → extract → index pipeline end-to-end with step-by-step progress strings ([1/3], [2/3], [3/3]) returned to the agent.
- Added Protocol 0 (Smart Document Handling) to AGENTS.md: agent must always call check_document_status first when a file path is mentioned, then either ingest (with user notification) or query directly.

- Added `delete_document(doc_name_or_path, collection_name)` tool: deletes all Qdrant points for a specific document (accepts file path, filename, or bare name — resolved via Path.stem) or wipes the entire collection when passed "all" / "everything" / "*". AGENTS.md updated to handle natural language delete prompts like "delete xyz" and "delete all documents from my knowledge base".

- Added missing `docker-compose.yml` (Qdrant persistent volume on ports 6333/6334) — was missing from repo, causing server auto-start to silently fail.
- Rewrote `README.md`: fixed one-time vs ongoing step split, added venv activation to setup, moved `pip install` to one-time setup, updated test prompts to reflect new natural-language UX (no need to specify tool names), replaced Docker reset instructions with `delete_document` tool usage examples, added first-run model download note (~1GB), added Troubleshooting table.

