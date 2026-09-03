# OpenCode CLI MCP Extensions

This repository contains a local MCP (Model Context Protocol) server designed to extend the capabilities of the `opencode-cli` running on your local machine.

Currently, it contains the following capabilities (with more to be added in the future):
- **Ask-Me (Knowledge Base)**: Tools to ingest data and ask questions.

## Setup Instructions (Windows)

1. Ensure you have **Python 3.10+** installed on your Windows machine.
2. Open Windows PowerShell or Command Prompt.
3. Navigate to the folder where you cloned this repository:
   ```powershell
   cd path\to\your_mcp
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

Add the following to the `"mcpServers"` block. **Make sure to replace `C:\\path\\to\\your_mcp` with the actual absolute path where you cloned this repo on your laptop.**

```json
{
  "mcpServers": {
    "opencode-local-extensions": {
      "command": "C:\\path\\to\\your_mcp\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\path\\to\\your_mcp\\server.py"
      ]
    }
  }
}
```

## Testing it

Once configured, restart your `opencode-cli` on Windows. You can then test it by asking the agent to use the new tools, for example:
- *"Use the ingest_data tool to save this information..."*
