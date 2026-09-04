# 🚀 Vision-RAG MCP — End-to-End Setup & Usage Guide

> **Purpose:** Step-by-step walkthrough for the current architecture:
> `ask-me` handles heavy GPU ingestion (fire-and-forget),  
> `mcp_tools/server.py` handles search, analysis, and orchestration for OpenCode.

---

## 📁 Repository Layout

```
/blanker/git/agents/
├── mcp_tools/                  ← MCP server (OpenCode talks to this)
│   ├── server.py               ← All MCP tools exposed to OpenCode
│   ├── backfill_file_paths.py  ← One-time migration script (run once)
│   ├── .env                    ← Your secrets (copy from .env.example)
│   ├── .env.example
│   └── docker-compose.yml      ← Qdrant container
│
└── tools/ask-me/               ← Standalone ingestion CLI (GPU-heavy work)
    ├── ask_me/
    │   ├── main.py             ← Entry point: `python -m ask_me.main ingest`
    │   ├── config.py           ← Settings loaded from .env
    │   ├── indexing/pipeline.py
    │   └── ingestion/converter.py
    ├── .env                    ← ask-me secrets (copy from template below)
    └── pyproject.toml
```

---

## ⚙️ Part 1 — One-Time Setup

### Step 1 — Start Qdrant (Docker)

```bash
cd /blanker/git/agents/mcp_tools
docker compose up -d
```

Verify it is running:
```bash
curl http://127.0.0.1:6333
# Expected: {"title":"qdrant","version":"..."}
```

---

### Step 2 — Set Up MCP Server `.env`

```bash
cd /blanker/git/agents/mcp_tools
cp .env.example .env
```

Edit `.env`:

```env
# Qdrant (same machine as MCP server)
QDRANT_HOST=127.0.0.1
QDRANT_PORT=6333

# FM Gateway — Vision LLM endpoint
FM_GATEWAY_URL=https://fmgateway.proxem.dsone.3ds.com
FM_GATEWAY_TOKEN=your_auth_token_here

# VLM used by analyze_image (chat/completions endpoint)
VLM_MODEL=google/gemma-4-31B-it

# ColPali model used for embedding queries in search_visual_knowledge_base
VISION_RETRIEVER_MODEL=vidore/colSmol-500M
```

> ⚠️ **SSL Note:** The FM Gateway uses an internal/self-signed certificate.
> `analyze_image` already sets `verify=False` and suppresses the warning.
> Do NOT set `FM_GATEWAY_VERIFY_SSL=True` unless your cert chain is trusted.

---

### Step 3 — Set Up `ask-me` `.env`

`ask-me` needs its **own** `.env` file because it runs as a separate process.

```bash
cd /blanker/git/agents/tools/ask-me
```

Create `.env` with the following content:

```env
# ── Qdrant ────────────────────────────────────────────────────────────────────
QDRANT_HOST=127.0.0.1
QDRANT_PORT=6333

# ── FM Gateway (used by ask-me chat mode, not needed for ingest-only) ─────────
FM_GATEWAY_URL=https://fmgateway.proxem.dsone.3ds.com
FM_GATEWAY_TOKEN=your_auth_token_here
FM_GATEWAY_VERIFY_SSL=False

# ── Models ────────────────────────────────────────────────────────────────────
# ColPali model — used for image embedding during ingestion
# First run downloads ~1 GB from HuggingFace to local cache. Be patient.
VISION_RETRIEVER_MODEL=vidore/colSmol-500M

# VLM for chat mode (not used during ingest)
VLM_MODEL=google/gemma-4-31B-it
SYNTHESIS_MODEL=Qwen/Qwen3.6-27B

# ── Ingestion Paths ───────────────────────────────────────────────────────────
# Directory ask-me crawls for .pdf / .docx / .pptx files to ingest
INDEX_DIRECTORY=C:\path\to\your\documents

# Stable directory where extracted page JPEGs are saved (survives reboots).
# This path is stored in Qdrant payload so OpenCode can call analyze_image
# directly with the file path — no large base64 needed over MCP wire.
# DEFAULT: ~/.ask_me_store/vision_pages  (auto-created if missing)
IMAGE_STORE_DIR=C:\Users\YourName\.ask_me_store\vision_pages

# Directory where ingestion status JSON files are written (one per document).
# OpenCode's poll_ingestion_status MCP tool reads these to track progress.
# DEFAULT: ~/.ask_me_store/status  (auto-created if missing)
STATUS_DIR=C:\Users\YourName\.ask_me_store\status

# ── Logging ───────────────────────────────────────────────────────────────────
DEBUG_LOG=False
```

> 💡 **Key points:**
> - `INDEX_DIRECTORY` — point this to the folder containing your documents.
>   ask-me will recursively crawl all `.pdf`, `.docx`, `.pptx` files in it.
> - `IMAGE_STORE_DIR` and `STATUS_DIR` are auto-created by ask-me on first run.
>   You only need to set them explicitly if you want a non-default location.
> - Both `IMAGE_STORE_DIR` and `STATUS_DIR` must be on a **persistent drive**,
>   not in `/tmp` — they survive reboots and let OpenCode reuse indexed data.

---

### Step 4 — Install ask-me dependencies

```bash
cd /blanker/git/agents/tools/ask-me
python -m venv .venv
.venv\Scripts\activate          # Windows
# or: source .venv/bin/activate   # Linux/Mac

pip install -e .
```

> ⏳ **First run note:** `VISION_RETRIEVER_MODEL=vidore/colSmol-500M` will be
> downloaded from HuggingFace (~1 GB). This only happens once and is cached.

---

### Step 5 — Install MCP server dependencies

```bash
cd /blanker/git/agents/mcp_tools
python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
```

---

## 🔄 Part 2 — Run the Backfill (One-Time, Existing Data Only)

> **Skip this if you have no previously indexed documents.**
> Run this once to patch `file_path` into Qdrant payloads for all docs that
> were indexed before today's update. No re-embedding needed.

```bash
cd /blanker/git/agents/mcp_tools
.venv\Scripts\activate

# Preview what will change (safe, no writes)
python backfill_file_paths.py --dry-run

# Run for real
python backfill_file_paths.py
```

Optional flags:
```
--host 127.0.0.1       Qdrant host (default: $QDRANT_HOST or 127.0.0.1)
--port 6333            Qdrant port (default: $QDRANT_PORT or 6333)
--collection vision_pages
--store-dir C:\Users\YourName\.ask_me_store\vision_pages
--dry-run              Preview only, no writes
```

---

## 🔌 Part 3 — Start the MCP Server

```bash
cd /blanker/git/agents/mcp_tools
.venv\Scripts\activate
python server.py
```

Server starts on `http://127.0.0.1:8000/sse`.

Verify in your `opencode.json` / MCP config:
```json
{
  "mcpServers": {
    "vision-rag": {
      "type": "remote",
      "url": "http://127.0.0.1:8000/sse"
    }
  }
}
```

---

## 📄 Part 4 — Ingest a Document (New Flow)

### Option A — Let OpenCode trigger ingestion (recommended)

In OpenCode, simply say:
> *"Please ingest the file at `C:\docs\report.pptx`"*

OpenCode will:
1. Call `check_document_status` → detects not indexed
2. Inform you: *"This document hasn't been ingested yet — please wait..."*
3. Call `launch_ingestion(ask_me_dir='...', doc_name='report')` → returns PID instantly
4. Poll `poll_ingestion_status('report')` every 30 seconds
5. Once status is `done` → proceeds to query automatically

### Option B — Trigger ask-me manually from terminal

```bash
cd /blanker/git/agents/tools/ask-me
.venv\Scripts\activate

# Put your documents in the INDEX_DIRECTORY configured in .env, then:
python -m ask_me.main ingest
```

Watch the logs — ColPali embedding is the slow step (GPU-bound).
Status files appear in `STATUS_DIR` as:
```json
{
  "doc_name": "report",
  "status": "running",   // → "done" or "error"
  "pages_done": 12,
  "pages_total": null,
  "started_at": "2026-09-04T06:30:00Z",
  "finished_at": null,
  "error": null
}
```

---

## 🔍 Part 5 — Query Documents in OpenCode

Once a document is indexed, simply ask:
> *"What does slide 5 of report.pptx say about deployment?"*

OpenCode will:
1. Call `search_visual_knowledge_base(query="deployment")`
2. For each result: check `file_path` → call `analyze_image(file_path, prompt)`
   - If `file_path` is null (legacy doc) → falls back to `image_base64`
3. Synthesize and return the answer

---

## 🛠️ Part 6 — MCP Tools Reference

| Tool | Purpose |
|------|---------|
| `check_document_status(file_path)` | Check if a doc is already indexed |
| `launch_ingestion(ask_me_dir, doc_name)` | Fire-and-forget: start ask-me in background |
| `poll_ingestion_status(doc_name)` | Check ingestion progress (running/done/error) |
| `search_visual_knowledge_base(query)` | Semantic search; returns `file_path` or `image_base64` |
| `analyze_image(file_path_or_base64, prompt)` | Send a page image to the VLM for analysis |
| `list_ingested_documents()` | List all indexed docs and page counts |
| `delete_document(doc_name_or_path)` | Delete a doc or wipe the entire collection |
| `get_file_info(file_path)` | File metadata without ingesting |
| `ingest_document(file_path)` | (Legacy) MCP-native ingestion — times out on large docs |
| `convert_office_to_pdf(input, output_dir)` | PPTX/DOCX → PDF via COM |
| `extract_pdf_pages(pdf_path)` | PDF → list of JPEG paths |
| `index_images_to_qdrant(image_paths, collection, doc_name)` | Embed + store in Qdrant |

---

## 🗂️ Part 7 — Stable Storage Layout

After ingestion, your file system looks like:
```
~/.ask_me_store/
├── vision_pages/
│   ├── report/
│   │   ├── page_001.jpg
│   │   ├── page_002.jpg
│   │   └── ...
│   └── quarterly_review/
│       ├── page_001.jpg
│       └── ...
└── status/
    ├── report.json          ← { "status": "done", "pages_done": 45, ... }
    └── quarterly_review.json
```

> These files are created by ask-me during ingestion and paths are stored in
> Qdrant. They must NOT be deleted — deleting them means search results will
> fall back to base64 (large, may be truncated by OpenCode).

---

## 🐛 Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `analyze_image` returns 404 | Wrong `FM_GATEWAY_URL` | Strip trailing `/v1` — server.py adds it automatically |
| `analyze_image` SSL error | Internal CA cert | Already fixed: `verify=False` is set |
| Ingestion hangs in MCP | ColPali embedding timeout | Use `launch_ingestion` + `poll_ingestion_status` instead |
| `file_path` is null in search results | Doc was indexed before today's fix | Run `backfill_file_paths.py` |
| `poll_ingestion_status` returns `not_found` | Wrong `doc_name` or STATUS_DIR mismatch | Use `Path.stem` of the file (e.g. `report` not `report.pptx`); check STATUS_DIR in ask-me `.env` |
| Qdrant connection refused | Docker not running | `docker compose up -d` in `mcp_tools/` |
| First ingest very slow | ColPali model downloading | Normal — ~1GB download on first run only |
| ask-me can't find documents | `INDEX_DIRECTORY` wrong | Check `.env` in `tools/ask-me/` — must point to folder with your docs |

