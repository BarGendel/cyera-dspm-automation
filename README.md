# Cyera DSPM Automation

Minimal Python + Pytest + Playwright project for the Cyera DSPM assignment.

## Project Structure

```text
shared.py      # settings, alert statuses, polling helper
api_helpers.py # REST API actions and alert parsing
ui_helpers.py  # Playwright UI actions
conftest.py    # pytest fixtures, logging, JSON reporting
tests/api/     # auto-remediation + rescan verification test
tests/ui/      # manual remediation lifecycle UI test
```

## Requirements

- Python 3.10+
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
```

Optional environment overrides are documented in `.env.example`.

## Run

```bash
pytest --collect-only -q
pytest tests/ui -m ui
pytest tests/api -m api
```

The API test is expected to fail because the assignment says the rescan intentionally recreates an identical alert.

## Logging And Reporting

Generated automatically on test runs:

```text
logs/automation.log
reports/session-summary.json
```

Logs include normal operations and exceptional events. The JSON report includes each test result, markers, duration, and failure details.
