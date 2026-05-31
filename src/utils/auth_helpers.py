import json

from playwright.sync_api import Page

from src.core.shared import Settings


def login_via_session(page: Page, settings: Settings, user_type: str = "valid") -> None:
    credentials = settings.get_user(user_type)
    state = {
        "token": credentials.auth_token,
        "username": credentials.username,
    }

    page.add_init_script(
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
