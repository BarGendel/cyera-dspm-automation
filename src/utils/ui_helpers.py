import logging
import re
from collections.abc import Iterable

from playwright.sync_api import Locator, Page, expect

from src.core.shared import Settings

logger = logging.getLogger(__name__)


def _click_first(locators: Iterable[Locator], action: str) -> None:
    last_error: Exception | None = None
    for locator in locators:
        try:
            locator.first.click(timeout=2_500)
            logger.info("Clicked %s", action)
            return
        except Exception as exc:
            last_error = exc
    logger.error("Could not click %s: %s", action, last_error)
    raise AssertionError(f"Could not click {action}: {last_error}")


def _fill_first(locators: Iterable[Locator], value: str, action: str) -> None:
    last_error: Exception | None = None
    for locator in locators:
        try:
            locator.first.fill(value, timeout=2_500)
            logger.info("Filled %s", action)
            return
        except Exception as exc:
            last_error = exc
    logger.error("Could not fill %s: %s", action, last_error)
    raise AssertionError(f"Could not fill {action}: {last_error}")


def _try_fill_first(locators: Iterable[Locator], value: str, action: str) -> bool:
    last_error: Exception | None = None
    for locator in locators:
        try:
            locator.first.fill(value, timeout=5_000)
            logger.info("Filled %s", action)
            return True
        except Exception as exc:
            last_error = exc
    logger.warning("Could not fill %s, continuing without filtering: %s", action, last_error)
    return False


def login(page: Page, settings: Settings) -> None:
    logger.info("Logging into web UI")
    last_error: Exception | None = None
    for attempt in range(1, 3):
        page.goto(settings.web_base_url, wait_until="networkidle")
        _fill_first([page.get_by_label(re.compile("username|email", re.I)), page.locator("input[type='text']")], settings.username, "username")
        _fill_first([page.get_by_label(re.compile("password", re.I)), page.locator("input[type='password']")], settings.password, "password")
        _click_first([page.get_by_role("button", name=re.compile("login|sign in", re.I)), page.locator("button[type='submit']")], "login")
        try:
            expect(page.get_by_role("button", name=re.compile(r"sign out", re.I))).to_be_visible(timeout=10_000)
            return
        except AssertionError as exc:
            last_error = exc
            if attempt == 2:
                break
            logger.warning("Login did not reach signed-in state; retrying")
            page.context.clear_cookies()
            try:
                page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
            except Exception:
                logger.debug("Could not clear browser storage before login retry")
    raise AssertionError("Login did not reach signed-in state") from last_error
