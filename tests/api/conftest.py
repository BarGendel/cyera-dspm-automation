import pytest


@pytest.fixture(autouse=True)
def scanned_system(api_client, clean_system):
    api_client.start_scan()
