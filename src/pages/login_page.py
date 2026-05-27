import json
import re

from playwright.sync_api import Page, expect

from src.core.shared import Settings


class LoginPage:
    def __init__(self, page: Page, settings: Settings | None = None):
        self.page = page
        self.settings = settings or Settings()
        self.username_input = page.get_by_label(re.compile("username|email", re.I))
        self.password_input = page.get_by_label(re.compile("password", re.I))
        self.sign_in_button = page.get_by_role("button", name=re.compile("login|sign in", re.I))
        self.sign_out_button = page.get_by_role("button", name=re.compile("sign out", re.I))

    def login_via_session(self, user_type: str = "valid") -> None:
        credentials = self.settings.get_user(user_type)
        state = {
            "token": credentials.auth_token,
            "username": credentials.username,
        }
        self.page.add_init_script(
            f"""
            (() => {{
                const state = {json.dumps(state)};
                localStorage.setItem("token", state.token);
                localStorage.setItem("user", JSON.stringify({{
                    username: state.username,
                    name: state.username,
                    role: "admin"
                }}));
            }})();
            """
        )
        self.page.base_url = self.settings.web_base_url

    def authenticate_as(self, user_type: str = "valid") -> None:
        self.login_via_session(user_type)

    def login_via_ui(self, username: str | None = None, password: str | None = None) -> None:
        self.page.base_url = self.settings.web_base_url
        self.page.goto(f"{self.settings.web_base_url}/login", wait_until="networkidle")
        self.username_input.fill(username or self.settings.username)
        self.password_input.fill(password or self.settings.password)
        self.sign_in_button.click()
        expect(self.sign_out_button).to_be_visible(timeout=10_000)
