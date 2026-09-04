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

- Fixed SSL verification error in `analyze_image`: internal FM Gateway (`fmgateway.proxem.dsone.3ds.com`) uses a self-signed/internal CA certificate. Added `verify=False` to `requests.post()` and suppressed `urllib3.InsecureRequestWarning` to prevent SSL handshake failures when calling the Vision LLM.

- Fixed `AGENTS.md` reset-on-startup issue: opencode was wiping the file because it was being placed in the `runtime\` directory which opencode owns and re-initialises. The correct global location is `%USERPROFILE%\.config\opencode\AGENTS.md`. Updated `run_server.bat` to auto-sync the project `AGENTS.md` to the correct global config directory on every MCP server start, keeping them in sync without manual intervention.

- Added `get_file_info(file_path)` tool: returns lightweight metadata (name, size, extension, created/modified dates) for any file on disk without ingesting it. For PDFs uses `pypdf` to also return page count, title, author, subject and creator. For PPTX/DOCX uses `python-pptx`/`python-docx` to return slide count, title, author, subject. Added `pypdf` to `requirements.txt`. Updated `AGENTS.md` with a rule to call `get_file_info` immediately when the user pastes a file path and asks basic metadata questions, rather than triggering a full ingest pipeline.

## [2026-09-04]
- **Bug Fix — Broken analyze_image pipeline (truncated base64):** `search_visual_knowledge_base` was returning `image_base64` truncated to 100 chars + `"...(truncated for display)"` for context efficiency. However, the agent was then passing this corrupted string directly to `analyze_image`, which caused the VLM to receive invalid image data. Fixed by replacing `image_base64` in search results with `file_path` (the on-disk JPEG path written during ingestion) and renaming the truncated field to `image_base64_preview` to make its display-only intent explicit. `analyze_image` already handles local file paths via `os.path.exists()`, so this requires no changes to the VLM call. Updated `search_visual_knowledge_base` docstring to instruct the agent to use `file_path`, not `image_base64_preview`.

- **Bug Fix — 404 from FM Gateway (wrong endpoint URL):** `analyze_image` was constructing the OpenAI-compatible endpoint with flawed logic that only handled the case where `FM_GATEWAY_URL` already ended in `/v1`. If the base URL was set to `https://fmgateway.proxem.dsone.3ds.com` (no `/v1`), the constructed endpoint became `.../chat/completions` (missing the `/v1` segment), resulting in a 404. Fixed by always stripping trailing slashes and any existing `/v1`, then always appending `/v1/chat/completions`. This makes the URL normalization deterministic regardless of how `FM_GATEWAY_URL` is set in `.env`.

- **Bug Fix — No server-side error logging for gateway failures:** 4xx/5xx errors from the FM Gateway were only returned as strings to the agent — `logger.error` was never called. Added explicit `logger.error()` calls in both `HTTPError` and generic `RequestException` handlers in `analyze_image`, including the resolved endpoint and model name for easy debugging. This is why the server log showed nothing on 404.

- **Bug Fix — Broken analyze_image pipeline (fragile file_path approach):** The Sep 4 fix that replaced `image_base64` with `file_path` in search results was incomplete. `file_path` points to a temp directory created at ingestion time (`/tmp/pdf_extract_XXXXX/`) — these files are deleted on reboot, making the pipeline fragile across sessions. More critically, documents indexed by older code versions had `file_path: null` in their Qdrant payload entirely. The correct fix: `search_visual_knowledge_base` now returns the full `image_base64` string directly from the Qdrant payload (where it has always been stored in full). The agent passes it directly to `analyze_image`. The broken `file_path` and `image_base64_preview` fields have been removed from all search result objects. `AGENTS.md` updated to instruct the agent to use `image_base64` directly.

- **Architecture — Stable file_path + ask-me fire-and-forget ingestion:**
  Root cause of the remaining fragility: base64 inline in search results causes opencode tool-output truncation (460KB+ per page). Final fix is a multi-part change:
  1. **`ask-me/ask_me/config.py`** — Added `image_store_dir` (`~/.ask_me_store/vision_pages`) and `status_dir` (`~/.ask_me_store/status`) settings.
  2. **`ask-me/ask_me/indexing/pipeline.py`** — `index_document_pages` now saves each page JPEG to `image_store_dir/<doc_name>/page_NNN.jpg` (stable, survives reboots) and stores `file_path` in the Qdrant payload alongside `image_base64` (kept as cold-storage fallback). Also added `from pathlib import Path` import at module level.
  3. **`ask-me/ask_me/main.py`** — Fixed `doc_name` to use `filepath.stem` (not `filepath.name`) to match `server.py`'s `Path.stem` convention. Added status file writing (`~/.ask_me_store/status/<doc_name>.json`) with states `running/done/error` and `pages_done` progress after each batch — enables MCP polling without GPU-usage heuristics.
  4. **`mcp_tools/server.py`** — `search_visual_knowledge_base` and fetch branch now return `file_path` (when valid) instead of inline `image_base64`. `image_base64` is returned only as fallback for legacy docs. Added two new MCP tools: `launch_ingestion` (fire-and-forget subprocess, returns PID immediately — no timeout risk) and `poll_ingestion_status` (reads status JSON, returns progress). Updated `AGENTS.md` Map-Reduce instructions to check `file_path` first.
  5. **`mcp_tools/backfill_file_paths.py`** — New one-time migration script. Scrolls all Qdrant points, decodes `image_base64`, writes stable JPEGs, patches `file_path` in payload. No re-embedding. Supports `--dry-run`. Run once to fix all existing indexed documents.

