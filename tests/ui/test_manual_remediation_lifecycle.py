import pytest

from shared import AlertStatus
from ui_helpers import (
    add_comment,
    add_remediation_notes,
    click_remediate,
    expect_text,
    login,
    open_alert,
    open_alerts_tab,
    select_alert_option,
)

FINAL_COMMENT = "Remediation verified successfully and issue is resolved"
REMEDIATION_NOTES = "Manual remediation was executed by automation and is ready for verification"
ASSIGNEE = "Security Analyst"


@pytest.mark.ui
@pytest.mark.e2e
def test_manual_remediation_alert_lifecycle(page, settings, api_client, clean_system):
    # Use API setup so the UI test starts with a known manual-remediation alert.
    api_client.start_scan()
    alert = api_client.find_alert(statuses=[AlertStatus.OPEN], auto_remediate=False)

    # From this point, execute the requested lifecycle through the frontend.
    login(page, settings)

    # Open the alert from the Alerts tab, then perform the manual remediation steps.
    open_alerts_tab(page, settings.web_base_url)
    open_alert(page, alert.search_text)
    select_alert_option(page, "Change alert status", AlertStatus.IN_PROGRESS)
    select_alert_option(page, "Assign alert", ASSIGNEE)
    add_remediation_notes(page, REMEDIATION_NOTES)
    click_remediate(page)
    select_alert_option(page, "Change alert status", AlertStatus.RESOLVED)
    add_comment(page, FINAL_COMMENT)

    # Final user-visible business state.
    expect_text(page, AlertStatus.RESOLVED)
    expect_text(page, FINAL_COMMENT)