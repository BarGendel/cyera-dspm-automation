import pytest
from playwright.sync_api import Page, expect

from src.core.shared import AlertStatus
from src.pages.alert_detail import AlertDetailPage
from src.pages.alerts_list import AlertsListPage
from src.pages.login_page import LoginPage

FINAL_COMMENT = "Remediation verified successfully and issue is resolved"
REMEDIATION_NOTES = "Manual remediation was executed by automation and is ready for verification"
ASSIGNEE = "Security Analyst"


@pytest.mark.ui
@pytest.mark.requires_scan
class TestManualRemediationLifecycle:
    @pytest.fixture(autouse=True)
    def setup(self, page: Page) -> None:
        self.login_page = LoginPage(page)
        self.alerts_list = AlertsListPage(page)
        self.alert_detail = AlertDetailPage(page)


    @pytest.mark.e2e
    def test_manual_remediation_alert_lifecycle(self, api_client) -> None:
        alert = api_client.find_alert(statuses=[AlertStatus.OPEN], auto_remediate=False)
        self.alerts_list.open_alert(alert)

        self.alert_detail.set_status(AlertStatus.IN_PROGRESS)
        expect(self.alert_detail.status_button).to_contain_text(AlertStatus.IN_PROGRESS)

        self.alert_detail.assign(ASSIGNEE)
        expect(self.alert_detail.assign_button).to_contain_text(ASSIGNEE)

        self.alert_detail.add_remediation_notes(REMEDIATION_NOTES)
        self.alert_detail.remediate()
        expect(self.alert_detail.status_button).to_contain_text("Awaiting User Verification")

        self.alert_detail.set_status(AlertStatus.RESOLVED)
        self.alert_detail.add_comment(FINAL_COMMENT)

        expect(self.alert_detail.status_button).to_contain_text(AlertStatus.RESOLVED)
        expect(self.alert_detail.page.get_by_text(FINAL_COMMENT)).to_be_visible()