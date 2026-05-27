import pytest
from playwright.sync_api import Page

from src.pages.login_page import LoginPage


@pytest.mark.ui
@pytest.mark.login_via_ui
class TestLogin:
    @pytest.fixture(autouse=True)
    def setup(self, page: Page) -> None:
        self.login_page = LoginPage(page)

    def test_valid_login(self) -> None:
        self.login_page.login_via_ui()
