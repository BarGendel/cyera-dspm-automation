import pytest

from src.pages.login_page import LoginPage


@pytest.fixture(autouse=True)
def session_login(page, request):
    if request.node.get_closest_marker("login_via_ui"):
        return
    LoginPage(page).login_via_session("valid")


@pytest.fixture(autouse=True)
def scanned_system(api_client, request):
    if not request.node.get_closest_marker("requires_scan"):
        return
    request.getfixturevalue("clean_system")
    api_client.start_scan()
