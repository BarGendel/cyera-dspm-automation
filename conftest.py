import json
import logging
import time
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from api_helpers import DspmApiClient
from shared import Settings

RESULTS: list[dict[str, object]] = []


def pytest_configure(config):
    Path("logs").mkdir(exist_ok=True)
    logger = logging.getLogger()
    logger.handlers.clear()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    console = logging.StreamHandler()
    file = logging.FileHandler("logs/automation.log", encoding="utf-8")
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
    context = browser.new_context(viewport={"width": 1440, "height": 1000})
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
    Path("reports").mkdir(exist_ok=True)
    report = {
        "exitstatus": exitstatus,
        "total": len(RESULTS),
        "passed": sum(result["outcome"] == "passed" for result in RESULTS),
        "failed": sum(result["outcome"] == "failed" for result in RESULTS),
        "skipped": sum(result["outcome"] == "skipped" for result in RESULTS),
        "tests": RESULTS,
    }
    Path("reports/session-summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    logging.info("Wrote reports/session-summary.json")
    logging.info("Test session finished")
