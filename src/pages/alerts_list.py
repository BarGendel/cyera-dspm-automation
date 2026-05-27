import logging
import re
from typing import Any

from playwright.sync_api import Page

from src.utils.ui_helpers import _click_first, _try_fill_first

logger = logging.getLogger(__name__)


class AlertsListPage:
    def __init__(self, page: Page):
        self.page = page
        self._search_field = [
            page.get_by_label(re.compile("search alerts", re.I)),
            page.get_by_placeholder(re.compile("search by policy", re.I)),
            page.locator("input[type='search']"),
        ]
        self._alert_dialog = page.get_by_role("dialog")

    def navigate(self) -> None:
        logger.info("Navigating to Alerts tab")
        self.page.goto(f"{self.page.base_url.rstrip('/')}/alerts", wait_until="networkidle")

    def open_alert(self, alert: Any) -> None:
        logger.info("Opening alert: %s", alert.search_text)
        self.navigate()
        _try_fill_first(self._search_field, alert.search_text, "alert search")
        _click_first(
            [
                self.page.locator("tr", has_text=re.compile(re.escape(alert.search_text), re.I)),
                self.page.get_by_role("row", name=re.compile(re.escape(alert.search_text), re.I)),
            ],
            "alert row",
        )
        self._alert_dialog.wait_for(state="visible", timeout=10_000)
