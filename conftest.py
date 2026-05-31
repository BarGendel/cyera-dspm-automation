import json
import logging
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from src.api.api_helpers import DspmApiClient
from src.core.shared import Settings

RESULTS: list[dict[str, object]] = []
ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", ".artifacts"))
LOGS_DIR = ARTIFACTS_DIR / "logs"
REPORTS_DIR = ARTIFACTS_DIR / "reports"


def _env_enabled(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _tail_file(path: Path, max_lines: int) -> str:
    if not path.exists():
        return ""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-max_lines:])


def _read_current_test_sources() -> str:
    chunks: list[str] = []
    test_files = sorted({str(result["nodeid"]).split("::", 1)[0] for result in RESULTS})
    for test_file in test_files:
        path = Path(test_file)
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if len(text) > 20_000:
            text = text[:20_000] + "\n# ... truncated ..."
        chunks.append(f"File: {test_file}\n```python\n{text}\n```")
    return "\n\n".join(chunks)


def _generate_ai_report(summary_json: str, test_sources: str) -> None:
    if not _env_enabled("GENERATE_AI_REPORT"):
        return

    if not shutil.which("claude"):
        logging.warning("GENERATE_AI_REPORT=true, but Claude Code was not found in PATH")
        return

    prompt = f"""
You are acting as a QA automation engineer.

Create a concise Markdown QA execution report.
Return only the Markdown report content.

Use only the provided current-run pytest session summary, current-run automation log excerpt, and executed test source.
Use the test source to identify actual assertions.
Use the automation log for execution evidence and timestamps.
Be conservative: describe what the tests executed and asserted, not broader product requirements.
Do not claim that a step is required unless the test explicitly asserts that behavior.
Do not call an assertion implicit if it is explicit in the executed test source.
Do not label timestamps as UTC unless UTC is explicitly present in the provided data; use "local run time" if needed.
If the session summary has zero failures, do not report failures from prior runs.
Only mention risks that appear in the current-run summary or current-run log excerpt.
Do not ask follow-up questions.
Do not include secrets, tokens, or full stack traces.
Do not suggest changing source files as part of this report.

Required sections:
- Test Run Summary
- Coverage
- Key Business Assertions
- Failures Or Risks
- Recommended Next Tests
- Evidence

Pytest session summary JSON:
```json
{summary_json}
```

Automation log excerpt:
```text
{_tail_file(LOGS_DIR / "automation.log", max_lines=120)}
```

Executed test source:
{test_sources}
""".strip()

    try:
        timeout_seconds = int(os.getenv("AI_REPORT_TIMEOUT_SECONDS", "180"))
        result = subprocess.run(
            [
                "claude",
                "--strict-mcp-config",
                "--mcp-config",
                '{"mcpServers":{}}',
                "-p",
                prompt,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        logging.warning("Claude QA report generation timed out")
        return
    except OSError as exc:
        logging.warning("Claude QA report generation could not start: %s", exc)
        return

    if result.returncode != 0:
        logging.warning("Claude QA report generation failed: %s", (result.stderr or result.stdout)[-2000:])
        return

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "qa-execution-report.md").write_text(result.stdout.strip() + "\n", encoding="utf-8")
    logging.info("Wrote %s", REPORTS_DIR / "qa-execution-report.md")


def pytest_configure(config):
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger()
    logger.handlers.clear()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    console = logging.StreamHandler()
    file = logging.FileHandler(LOGS_DIR / "automation.log", mode="w", encoding="utf-8")
    console.setLevel(logging.WARNING)
    file.setLevel(logging.INFO)
    console.setFormatter(formatter)
    file.setFormatter(formatter)
    logger.addHandler(console)
    logger.addHandler(file)

    logging.info("Logging configured")


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings()


@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser(playwright_instance, settings: Settings):
    browser = playwright_instance.chromium.launch(headless=settings.headless, slow_mo=settings.slow_mo_ms)
    yield browser
    browser.close()


@pytest.fixture
def page(browser, settings: Settings):
    context = browser.new_context(base_url=settings.web_base_url, viewport={"width": 1440, "height": 1000})
    page = context.new_page()
    page.set_default_timeout(settings.default_timeout_ms)
    yield page
    context.close()


@pytest.fixture
def api_context(playwright_instance, settings: Settings):
    context = playwright_instance.request.new_context(base_url=settings.api_base_url, ignore_https_errors=True)
    yield context
    context.dispose()


@pytest.fixture
def api_client(api_context, settings: Settings) -> DspmApiClient:
    return DspmApiClient(api_context, settings)


@pytest.fixture
def clean_system(api_client: DspmApiClient):
    api_client.reset_data()
    yield
    api_client.reset_data()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

    if report.when == "call":
        result = {
            "nodeid": item.nodeid,
            "outcome": report.outcome,
            "duration_seconds": round(report.duration, 3),
            "markers": [marker.name for marker in item.iter_markers()],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        if report.longrepr:
            result["error"] = str(report.longrepr)[:2000]
        RESULTS.append(result)


def pytest_runtest_setup(item):
    logging.info("START TEST: %s", item.nodeid)


def pytest_runtest_teardown(item):
    logging.info("END TEST: %s", item.nodeid)


def pytest_sessionfinish(session, exitstatus):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    passed = sum(result["outcome"] == "passed" for result in RESULTS)
    failed = sum(result["outcome"] == "failed" for result in RESULTS)
    skipped = sum(result["outcome"] == "skipped" for result in RESULTS)
    ran = passed + failed
    report = {
        "exitstatus": exitstatus,
        "total": len(RESULTS),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "success_rate": round(passed / ran * 100, 2) if ran > 0 else 0,
        "tests": RESULTS,
    }
    summary_json = json.dumps(report, indent=2)
    (REPORTS_DIR / "session-summary.json").write_text(summary_json, encoding="utf-8")
    logging.info("Wrote %s", REPORTS_DIR / "session-summary.json")
    _generate_ai_report(summary_json, _read_current_test_sources())
    logging.info("Test session finished")
