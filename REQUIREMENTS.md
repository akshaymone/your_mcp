# OpenCode MCP Extensions: Vision-RAG Requirements

## 1. Overview
This document outlines the detailed requirements and architectural decisions for building the `OpenCode-MCP-Extensions` server. The goal is to provide the `opencode-cli` agent with advanced, offline, and secure document ingestion and querying capabilities by adapting the Multimodal Vision-RAG architecture from the `ask-me` project.

All processing, embedding, and inference must occur entirely within the office network (local or internal cloud) to ensure strict data privacy.

## 2. Architectural Strategy
Rather than using traditional text-extraction RAG (which loses formatting, tables, and diagrams), the system will use a **Multimodal Vision-RAG** approach:
*   Documents are rendered as images.
*   **ColPali** (`colSmol-500M`) embeds the full visual pages.
*   **Qdrant** stores the multi-vectors and base64 image payloads.
*   **Gemma** (Vision LLM) and **Qwen** (Synthesis LLM) perform Map-Reduce generation to answer complex queries across multiple pages.

## 3. Tool Design Philosophy: Atomic Orchestration
To maximize the flexibility of the `opencode-cli` agent, the MCP server will **not** expose a monolithic "black box" pipeline. Instead, it will expose atomic, composable tools. The agent will act as the orchestrator, deciding when to convert, index, search, and analyze.

### Proposed MCP Tools
1.  `convert_office_to_pdf(input_path: str, output_dir: str)`
    *   **Function:** Uses `win32com` to convert DOCX/PPTX to PDF silently.
2.  `extract_pdf_pages(pdf_path: str, output_dir: str = None)`
    *   **Function:** Uses `pdf2image` to slice PDFs into batched JPEG images. If `output_dir` is omitted, it uses a temporary OS directory.
3.  `index_images_to_qdrant(image_paths: list[str], collection_name: str)`
    *   **Function:** Embeds images via ColPali and stores them in Qdrant along with metadata (hash, modified timestamp).
4.  `search_visual_knowledge_base(query: str, collection_name: str, limit: int = 5)`
    *   **Function:** Embeds text queries, searches Qdrant, and returns matching image base64 payloads and metadata. Includes support for `<FETCH_PAGE>` exact-match fetching.
5.  `analyze_image(image_path_or_base64: str, prompt: str)`
    *   **Function:** Passes an image and a prompt to the Vision LLM (Gemma) to extract specific visual data or answer questions.

## 4. Infrastructure & Error Handling
*   **Auto-Start Dependencies:** On startup (`__init__`), the MCP server will ping Qdrant (`localhost:6333`). If unreachable, it will spawn a `subprocess` to execute `docker compose up -d` to spin up the database.
*   **Agent-Friendly Error Reporting:** Python exceptions (like missing Docker or failed conversion) will be caught and returned as human-readable strings. Example: *"Error: Docker is not installed. Please instruct the user to install Docker Desktop to start the database."* The LLM will relay these instructions naturally to the user.
*   **Temporary File Cleanup:** Transient files (like intermediate JPEGs from PDF rendering) will be written using Python's `tempfile.TemporaryDirectory()`. This delegates cleanup to the OS automatically when the process closes.

## 5. Configuration & State Management
Configurations will be tiered to separate secrets, preferences, and state:
1.  **Secrets & APIs (`.env`):**
    *   Loaded via `python-dotenv`.
    *   Stores `LLM_API_KEY`, internal API endpoints (e.g., DevAssistant URL), and `QDRANT_HOST`.
2.  **User Preferences (`config.yaml`):**
    *   Stores non-sensitive defaults (e.g., `default_ingest_dir`, `default_collection`).
    *   *Future Enhancement:* Expose an `update_setting` MCP tool so the agent can modify preferences dynamically.
3.  **Incremental Ingestion State (Qdrant Metadata):**
    *   To prevent redundant processing, Qdrant will serve as the state tracker.
    *   Every ingested page will store `file_path`, `file_hash` (MD5), and `last_modified` in its payload.
    *   Before ingestion, the system checks `is_document_indexed`. Unchanged files are skipped; modified files are purged and re-ingested.

## 6. Generation Strategy & Agent Prompting
Because the tools are atomic, the `opencode-cli` agent is responsible for orchestrating the Map-Reduce flow. To ensure the agent strictly follows this procedure, we will use a multi-layered prompting strategy:

1.  **Workspace Rules (`AGENTS.md`):** A persistent `AGENTS.md` file will be placed in the project root alongside `opencode.js`. This file acts as an Antigravity customization rule, automatically injecting detailed behavioral instructions into the agent's context. It will explicitly define:
    *   **Map:** Agent searches Qdrant, retrieves top N pages, and calls `analyze_image` (Gemma) on each to extract data.
    *   **Reduce:** Agent reads all extractions in its own context window (Qwen, 256K limit) and synthesizes the final answer.
    *   **Fallback:** If a technical term is undefined in the visual context, the agent is instructed to use its pre-trained knowledge but must label it explicitly as `[General Knowledge]`.
2.  **MCP Tool Descriptions:** The `search_visual_knowledge_base` tool's docstring will also reinforce this Map-Reduce instruction, ensuring compatibility and compliance even if the tools are accessed via a different MCP client.
