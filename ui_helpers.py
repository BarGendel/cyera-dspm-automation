import logging
import re
from collections.abc import Iterable

from playwright.sync_api import Locator, Page, expect

from shared import Settings, wait_until

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


def login(page: Page, settings: Settings) -> None:
    logger.info("Logging into web UI")
    page.goto(settings.web_base_url, wait_until="networkidle")
    _fill_first([page.get_by_label(re.compile("username|email", re.I)), page.locator("input[type='text']")], settings.username, "username")
    _fill_first([page.get_by_label(re.compile("password", re.I)), page.locator("input[type='password']")], settings.password, "password")
    _click_first([page.get_by_role("button", name=re.compile("login|sign in", re.I)), page.locator("button[type='submit']")], "login")
    page.wait_for_load_state("networkidle")


def open_alerts_tab(page: Page, base_url: str) -> None:
    logger.info("Opening Alerts tab")
    page.goto(base_url, wait_until="networkidle")
    _click_first(
        [
            page.get_by_role("link", name=re.compile(r"^\s*Alerts\s*$", re.I)),
            page.get_by_role("button", name=re.compile(r"^\s*Alerts\s*$", re.I)),
        ],
        "Alerts tab",
    )
    page.wait_for_load_state("networkidle")


def open_alert(page: Page, search_text: str) -> None:
    logger.info("Opening alert by search text: %s", search_text)
    _fill_first([page.locator("#alert-search"), page.get_by_label(re.compile("search alerts", re.I))], search_text, "alert search")
    _click_first([page.locator("tr", has_text=re.compile(re.escape(search_text), re.I))], "alert row")
    page.wait_for_load_state("networkidle")


def select_alert_option(page: Page, button_name: str, option: str) -> None:
    logger.info("Selecting %s -> %s", button_name, option)
    button = re.compile(f"^{re.escape(button_name)}$", re.I)
    item = re.compile(f"^{re.escape(option)}$", re.I)
    page.get_by_role("button", name=button).click()
    page.get_by_role("listbox", name=button).get_by_role("option", name=item).click()
    page.wait_for_load_state("networkidle")


def add_remediation_notes(page: Page, notes: str) -> None:
    logger.info("Adding remediation notes")
    expand_section(page, "Remediation")
    _fill_first(
        [
            page.get_by_label(re.compile("remediation note", re.I)),
            page.get_by_placeholder(re.compile("remediation", re.I)),
            page.locator("textarea").last,
        ],
        notes,
        "remediation notes",
    )


def click_remediate(page: Page) -> None:
    logger.info("Clicking Remediate")
    expand_section(page, "Remediation")
    _click_first(
        [page.get_by_role("button", name=re.compile(r"^\s*Remediate\s*$", re.I)), page.locator("[data-testid*='remediate' i]")],
        "Remediate",
    )
    page.wait_for_load_state("networkidle")
    wait_until(
        lambda: page.get_by_role("button", name=re.compile("^Change alert status$", re.I)).is_visible(timeout=500),
        timeout_s=60,
        description="status control after remediation",
    )


def add_comment(page: Page, comment: str) -> None:
    logger.info("Adding comment")
    _fill_first(
        [page.get_by_label(re.compile("comment message", re.I)), page.get_by_placeholder(re.compile("add a comment", re.I)), page.locator("textarea").last],
        comment,
        "comment",
    )
    _click_first(
        [page.get_by_role("button", name=re.compile(r"^\s*Post Comment\s*$", re.I)), page.locator("[data-testid*='comment' i] button")],
        "Post Comment",
    )


def expand_section(page: Page, section_name: str) -> None:
    logger.info("Expanding %s section", section_name)
    section_id = f"section-{section_name.lower().replace(' ', '-')}"
    if page.locator(f"#{section_id}").is_visible(timeout=1_000):
        return
    _click_first([page.get_by_role("button", name=re.compile(f"^{re.escape(section_name)}", re.I))], section_name)


def expect_text(page: Page, text: str) -> None:
    logger.info("Expecting visible text: %s", text)
    expect(page.get_by_text(re.compile(re.escape(text), re.I)).first).to_be_visible()
