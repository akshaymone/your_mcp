@echo off
set PYTHONIOENCODING=utf-8

REM ── Sync AGENTS.md to the correct opencode global config directory ─────────
REM    opencode reads AGENTS.md from ~/.config/opencode/ (global) or the
REM    project root folder. The runtime\ dir is opencode-owned and gets reset.
set AGENTS_SRC=%~dp0AGENTS.md
set AGENTS_DST=%USERPROFILE%\.config\opencode\AGENTS.md

if not exist "%USERPROFILE%\.config\opencode" mkdir "%USERPROFILE%\.config\opencode"
copy /Y "%AGENTS_SRC%" "%AGENTS_DST%" >nul
echo [MCP] AGENTS.md synced to global opencode config.

REM ── Start the MCP server ──
"D:\work_dsi\Projects\korea\git\mcp_tools\.venv\Scripts\python.exe" -u "D:\work_dsi\Projects\korea\git\mcp_tools\server.py" 2> "D:\work_dsi\Projects\korea\git\mcp_tools\mcp_error.log"
