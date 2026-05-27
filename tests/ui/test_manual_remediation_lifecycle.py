import pytest
from playwright.sync_api import Page, expect

from src.core.shared import AlertStatus
from src.pages.alert_detail_drawer import AlertDetailDrawer
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
        self.alert_detail_drawer = AlertDetailDrawer(page)

    def test_open_alert_cannot_jump_to_resolved(self, api_client) -> None:
        alert = api_client.find_alert(statuses=[AlertStatus.OPEN], auto_remediate=False)
        self.alerts_list.open_alert(alert)

        self.alert_detail_drawer.open_status_dropdown()
        expect(self.alert_detail_drawer.status_option(AlertStatus.IN_PROGRESS)).to_be_visible()
        expect(self.alert_detail_drawer.status_option(AlertStatus.RESOLVED)).not_to_be_visible()

    @pytest.mark.e2e
    def test_manual_remediation_alert_lifecycle(self, api_client) -> None:
        alert = api_client.find_alert(statuses=[AlertStatus.OPEN], auto_remediate=False)
        self.alerts_list.open_alert(alert)

        self.alert_detail_drawer.set_status(AlertStatus.IN_PROGRESS)
        expect(self.alert_detail_drawer.status_button).to_contain_text(AlertStatus.IN_PROGRESS)

        self.alert_detail_drawer.assign(ASSIGNEE)
        expect(self.alert_detail_drawer.assign_button).to_contain_text(ASSIGNEE)

        self.alert_detail_drawer.add_remediation_notes(REMEDIATION_NOTES)
        self.alert_detail_drawer.remediate()
        expect(self.alert_detail_drawer.status_button).to_contain_text("Awaiting User Verification")

        self.alert_detail_drawer.set_status(AlertStatus.RESOLVED)
        self.alert_detail_drawer.add_comment(FINAL_COMMENT)

        expect(self.alert_detail_drawer.status_button).to_contain_text(AlertStatus.RESOLVED)
        expect(self.alert_detail_drawer.page.get_by_text(FINAL_COMMENT)).to_be_visible()

    def test_resolved_alert_can_be_reopened_and_moved_to_in_progress(self, api_client) -> None:
        alert = api_client.find_alert(statuses=[AlertStatus.OPEN], auto_remediate=False)
        self.alerts_list.open_alert(alert)

        self.alert_detail_drawer.set_status(AlertStatus.IN_PROGRESS)
        self.alert_detail_drawer.assign(ASSIGNEE)
        self.alert_detail_drawer.add_remediation_notes(REMEDIATION_NOTES)
        self.alert_detail_drawer.remediate()
        self.alert_detail_drawer.set_status(AlertStatus.RESOLVED)
        self.alert_detail_drawer.add_comment(FINAL_COMMENT)
        expect(self.alert_detail_drawer.status_button).to_contain_text(AlertStatus.RESOLVED)

        self.alert_detail_drawer.open_status_dropdown()
        self.alert_detail_drawer.status_option("Reopened").click()
        expect(self.alert_detail_drawer.status_button).to_contain_text("Reopened")

        self.alert_detail_drawer.open_status_dropdown()
        expect(self.alert_detail_drawer.status_option(AlertStatus.IN_PROGRESS)).to_be_visible()
        self.alert_detail_drawer.status_option(AlertStatus.IN_PROGRESS).click()
        expect(self.alert_detail_drawer.status_button).to_contain_text(AlertStatus.IN_PROGRESS)
