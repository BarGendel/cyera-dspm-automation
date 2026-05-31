import pytest

from src.utils.auth_helpers import login_via_session


@pytest.fixture(autouse=True)
def session_login(page, settings, request):
    if request.node.get_closest_marker("login_via_ui"):
        return
    login_via_session(page, settings, "valid")


@pytest.fixture(autouse=True)
def scanned_system(api_client, request):
    if not request.node.get_closest_marker("requires_scan"):
        return
    request.getfixturevalue("clean_system")
    api_client.start_scan()
