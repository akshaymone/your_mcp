# AskMe MCP Server

This is a local MCP (Model Context Protocol) server designed to be plugged into `opencode-cli` to provide custom data ingestion and Q&A capabilities.

## Setup Instructions (Windows)

1. Ensure you have **Python 3.10+** installed on your Windows machine.
2. Open Windows PowerShell or Command Prompt.
3. Navigate to the folder where you cloned/copied this repository:
   ```powershell
   cd path\to\mcp_tools
   ```
4. Create a virtual environment:
   ```powershell
   python -m venv .venv
   ```
5. Activate the virtual environment:
   ```powershell
   .venv\Scripts\activate
   ```
6. Install the required dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

## Configuring opencode-cli

To connect your CLI to this local server, you need to update your `opencode.json` file (typically located in your `user_profile/opencode/runtime` folder).

Add the following to the `"mcpServers"` block. **Make sure to replace `C:\\path\\to\\mcp_tools` with the actual absolute path where you placed this folder on your laptop.**

```json
{
  "mcpServers": {
    "ask-me-local": {
      "command": "C:\\path\\to\\mcp_tools\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\path\\to\\mcp_tools\\server.py"
      ]
    }
  }
}
```

## Testing it

Once configured, restart your `opencode-cli` on Windows. You can then test it by asking the agent:
1. *"Use the ask-me tool to ingest this sentence: 'The project codename is Apollo'."*
2. *"Ask the ask-me tool what the project codename is."*
