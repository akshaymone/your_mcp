# OpenCode CLI MCP Extensions — Vision-RAG

This repository is a local MCP (Model Context Protocol) server that gives `opencode-cli` the ability to read, understand, and answer questions about your documents using a fully offline **Multimodal Vision-RAG** pipeline (ColPali + Qdrant).

---

## One-Time Setup

Complete these steps once on a new machine.

### Prerequisites

1. **Docker Desktop** — Install and ensure it is running.
2. **Microsoft Office** — Word and PowerPoint must be installed (used for DOCX/PPTX → PDF conversion).
3. **Poppler** — Required for slicing PDFs into page images.
   - Download the Windows binaries from [poppler releases](https://github.com/oschwartz10612/poppler-windows/releases).
   - Extract to a folder, e.g. `C:\poppler`.
   - Add `C:\poppler\bin` to your system `PATH` environment variable.

### Install the Server

4. Clone or pull the latest code and open a terminal in the `mcp_tools` directory:
   ```bash
   git pull origin main
   ```

5. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

6. Activate it:
   ```bash
   # Windows Command Prompt / PowerShell
   .venv\Scripts\activate

   # Mac / Linux
   source .venv/bin/activate
   ```

7. Install all dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   > **Note:** The first time you start the server, it will download the `vidore/colSmol-500M` visual embedding model (~1 GB) from HuggingFace. This is a one-time download cached locally.

### Configure Secrets

8. Copy the environment template:
   ```bash
   # Windows Command Prompt
   copy .env.example .env

   # PowerShell / Mac / Linux
   cp .env.example .env
   ```

9. Open `.env` and fill in your values:
   ```env
   QDRANT_HOST=127.0.0.1
   QDRANT_PORT=6333
   FM_GATEWAY_URL=https://fmgateway.proxem.dsone.3ds.com
   FM_GATEWAY_TOKEN=your_auth_token_here
   VLM_MODEL=google/gemma-4-31B-it
   VISION_RETRIEVER_MODEL=vidore/colSmol-500M
   ```

### Configure opencode-cli

10. Add the following to your `opencode.json` (or `mcp_config.json`) under `mcpServers`:
    ```json
    {
      "mcpServers": {
        "OpenCode-Vision-RAG": {
          "type": "remote",
          "url": "http://127.0.0.1:8000/sse"
        }
      }
    }
    ```

---

## Ongoing Usage (Each Session)

1. Open a terminal in the `mcp_tools` directory.

2. Activate the virtual environment:
   ```bash
   # Windows
   .venv\Scripts\activate

   # Mac / Linux
   source .venv/bin/activate
   ```

3. Start the MCP server (it will auto-start Qdrant via Docker if not already running):
   ```bash
   python server.py
   ```
   *(Windows shortcut: double-click `run_server.bat`)*

4. Leave the server running. Open a **new terminal window** and start `opencode-cli`.

---

## How to Use

The agent handles everything automatically — just talk to it naturally.

### Asking about a document
Simply mention the file path and your question together. The agent will:
- **Check** if the document is already indexed.
- **Ingest it automatically** (with progress updates) if not.
- **Answer your question** using the visual knowledge base.

```
"Check C:\path\to\report.pptx — what does the architecture flowchart show?"
```

```
"What are the key KPIs on the executive summary page of C:\reports\Q3_review.pptx?"
```

### Deleting documents from the knowledge base

Delete a specific document:
```
"Delete report from my knowledge base."
"Remove Q3_review.pptx from the knowledge base."
```

Wipe everything and start fresh:
```
"Delete all documents from my local knowledge base."
"Clear the knowledge base."
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Qdrant not reachable` | Ensure Docker Desktop is running, then run `docker compose up -d` in this directory. |
| `Poppler not found` | Add `C:\poppler\bin` to your system PATH and restart your terminal. |
| Server hangs on first run | It is downloading the ColPali model (~1 GB). Wait for it to complete. |
| `FM_GATEWAY_URL` or `VLM_MODEL` error | Ensure `.env` is filled in correctly (copy from `.env.example`). |
