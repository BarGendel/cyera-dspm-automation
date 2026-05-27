# Cyera DSPM Automation

Python + Pytest + Playwright project

## Project Structure

```text
src/
  api/         # REST API client actions and alert parsing
  core/        # settings, alert statuses, polling helper
  pages/       # Playwright page objects
  utils/       # shared UI helper functions
tests/
  api/         # API tests and API-specific fixtures
  ui/          # UI tests and UI-specific fixtures
conftest.py   # global pytest fixtures, logging, JSON reporting
```

## Requirements

- Python 3.10+
- Node.js 20+ with `npx` for Playwright MCP
- Docker app running locally
- Playwright Chromium browser

Default local URLs and credentials:

```text
Web UI: http://localhost:3000
API:    http://localhost:8080
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m playwright install chromium
node -v
npx -v
```

Optional environment overrides are documented in `.env.example`.

## Playwright MCP

This project also includes a repo-local MCP configuration in `.mcp.json`:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest", "--output-dir", ".artifacts/playwright-mcp"]
    }
  }
}
```

Use this with an MCP-capable client such as VS Code, Cursor, Claude Code, Claude Desktop, or similar. Playwright MCP is for AI-assisted browser exploration and debugging; it does not replace the pytest tests in this repo.

Requirements:

- Node.js 20+ with `npx`
- An MCP-capable client

If your client does not auto-detect `.mcp.json`, copy the `mcpServers` block into that client's MCP settings.

## Run

Run commands from the project root, the folder that contains `pyproject.toml`, `src/`, and `tests/`.

Quick check:

```bash
pwd
ls tests/ui
```

Then run:

```bash
python -m pytest --collect-only -q
python -m pytest tests/ui -m ui -q
python -m pytest tests/api -m api -q
```

The API test is expected to fail because the assignment says the rescan intentionally recreates an identical alert.

## Claude Code Skills

Claude Code project policy lives in `CLAUDE.md`, and reusable project skills live in `.claude/skills/`.

Use these in Claude Code:

```text
/add-ui-test add a negative status-transition UI test
/flaky-debug analyze the latest UI failure
/qa-report summarize the latest UI run
```

## Interview Workflow

Use Playwright CLI to explore or record a new flow:

```bash
python -m playwright codegen --target=python-pytest -o /tmp/new_flow_codegen.py http://localhost:3000
```

Then convert the useful selectors and flow into clean pytest code that uses the existing helpers.

Run the UI suite in headed mode:

```bash
HEADLESS=false SLOW_MO_MS=500 python -m pytest tests/ui -m ui -q
```

Run the UI suite and generate the AI QA report:

```bash
GENERATE_AI_REPORT=true HEADLESS=false SLOW_MO_MS=500 python -m pytest tests/ui -m ui -q
```

## Logging And Reporting

Generated automatically on test runs:

```text
.artifacts/logs/automation.log
.artifacts/reports/session-summary.json
.artifacts/reports/qa-execution-report.md  # only when GENERATE_AI_REPORT=true
```

Logs include normal operations and exceptional events. The JSON report includes each test result, markers, duration, and failure details.

Override the generated artifact root if needed:

```bash
ARTIFACTS_DIR=/tmp/cyera-artifacts python -m pytest tests/ui -m ui -q
```

Claude Code behavior is documented in `CLAUDE.md`.
