import logging
import re

from playwright.sync_api import Locator, Page, expect

from src.core.shared import wait_until
from src.utils.ui_helpers import _click_first, _fill_first

logger = logging.getLogger(__name__)


class AlertDetailDrawer:
    def __init__(self, page: Page):
        self.page = page

        # Public locators — use in tests with expect()
        self.status_button = page.get_by_role("button", name=re.compile(r"^Change alert status$", re.I))
        self.assign_button = page.get_by_role("button", name=re.compile(r"^Assign alert$", re.I))

        # Private locators
        self._status_listbox = page.get_by_role("listbox", name=re.compile(r"^Change alert status$", re.I))
        self._assign_listbox = page.get_by_role("listbox", name=re.compile(r"^Assign alert$", re.I))
        self._remediation_toggle = page.get_by_role("button", name=re.compile(r"^Remediation", re.I)).first
        self._remediate_btn = page.get_by_role("button", name=re.compile(r"^\s*Remediate\s*$", re.I))
        self._remediation_notes_field = [
            page.get_by_label(re.compile("remediation note", re.I)),
            page.get_by_placeholder(re.compile("remediation", re.I)),
            page.locator("textarea").last,
        ]
        self._comment_field = [
            page.get_by_label(re.compile("comment message", re.I)),
            page.get_by_placeholder(re.compile("add a comment", re.I)),
            page.locator("textarea").last,
        ]
        self._post_comment_btn = [
            page.get_by_role("button", name=re.compile(r"^\s*Post Comment\s*$", re.I)),
            page.locator("[data-testid*='comment' i] button"),
        ]

    def status_option(self, status: str) -> Locator:
        return self._status_listbox.get_by_role("option", name=re.compile(f"^{re.escape(status)}$", re.I))

    def open_status_dropdown(self) -> None:
        self.status_button.click()

    def _expand_remediation(self) -> None:
        if self._remediation_toggle.get_attribute("aria-expanded") != "true":
            self._remediation_toggle.click(timeout=5_000)

    def set_status(self, status: str) -> None:
        logger.info("Setting status to %s", status)
        self.status_button.click()
        self.status_option(status).click()
        expect(self.status_button.get_by_text(re.compile(re.escape(status), re.I))).to_be_visible()

    def assign(self, assignee: str) -> None:
        logger.info("Assigning to %s", assignee)
        item = re.compile(f"^{re.escape(assignee)}$", re.I)
        self.assign_button.click()
        self._assign_listbox.get_by_role("option", name=item).click()
        expect(self.assign_button.get_by_text(re.compile(re.escape(assignee), re.I))).to_be_visible()

    def add_remediation_notes(self, notes: str) -> None:
        logger.info("Adding remediation notes")
        self._expand_remediation()
        _fill_first(self._remediation_notes_field, notes, "remediation notes")

    def remediate(self) -> None:
        logger.info("Clicking Remediate")
        self._expand_remediation()
        _click_first(
            [self._remediate_btn, self.page.locator("[data-testid*='remediate' i]")],
            "Remediate",
        )
        # Status transitions Open→Remediation In Progress then live-updates to
        # "Awaiting User Verification" before Resolved becomes available.
        wait_until(
            lambda: "awaiting" in (self.status_button.inner_text(timeout=500) or "").lower(),
            timeout_s=60,
            description="status 'Awaiting User Verification' after remediation",
        )

    def add_comment(self, comment: str) -> None:
        logger.info("Adding comment")
        _fill_first(self._comment_field, comment, "comment")
        _click_first(self._post_comment_btn, "Post Comment")
