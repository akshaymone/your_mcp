# OpenCode CLI MCP Extensions

This repository contains a local MCP (Model Context Protocol) server designed to extend the capabilities of the `opencode-cli` running on your local machine using a Multimodal Vision-RAG architecture.

## One-Time Setup Steps

1. Install **Docker Desktop** and ensure it is running.
2. Install **Microsoft Office** (Word and PowerPoint) on your machine.
3. Download **Poppler** binaries, extract them (e.g., to `C:\poppler`), and add `C:\poppler\bin` to your system `PATH` environment variable.
4. Clone or pull the repository and open your terminal in the `mcp_tools` directory:
   ```bash
   git pull origin main
   ```
5. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```
6. Copy the environment variables template:
   ```bash
   # Windows Command Prompt
   copy .env.example .env
   
   # Mac/Linux/PowerShell
   cp .env.example .env
   ```
7. Open `.env` and set the following variables:
   ```env
   QDRANT_HOST=127.0.0.1
   QDRANT_PORT=6333
   FM_GATEWAY_URL=https://fmgateway.proxem.dsone.3ds.com
   FM_GATEWAY_TOKEN=your_auth_token_here
   VLM_MODEL=google/gemma-4-31B-it
   VISION_RETRIEVER_MODEL=vidore/colSmol-500M
   ```
8. Update your `opencode-cli` configuration file (e.g., `opencode.json` or `mcp_config.json`) to point to the remote server:
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

## Ongoing Steps (Running & Testing)

1. Open your terminal in the `mcp_tools` directory.
2. Activate the virtual environment:
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # Mac/Linux
   source .venv/bin/activate
   ```
3. Install or update dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the MCP server:
   ```bash
   python server.py
   ```
5. Leave the server running. Open a new terminal window and start your `opencode-cli`.
6. **Test Ingestion Flow** by asking the agent:
   > "I have a presentation at C:\path\to\your\presentation.pptx. Please ingest it into the visual knowledge base."
7. **Test Query Flow** by asking the agent:
   > "Based on the document we just ingested, what does the flowchart on the architecture page describe?"
8. *(Optional)* To clear all ingested data and start from scratch, run:
   ```bash
   docker compose down -v
   docker compose up -d
   ```
