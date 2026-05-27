import pytest

from src.core.shared import AlertStatus

FINAL_COMMENT = "Remediation verified successfully and issue is resolved"


@pytest.mark.api
@pytest.mark.e2e
@pytest.mark.known_issue
def test_auto_remediation_rescan_does_not_recreate_identical_alert(api_client):
    # Pick an auto-remediation alert; this is the alert the product should fix automatically.
    original_alert = api_client.find_alert(
        statuses=[AlertStatus.OPEN, AlertStatus.REMEDIATION_IN_PROGRESS],
        auto_remediate=True,
    )

    # Wait until auto-remediation reaches the customer verification state, then close the alert.
    api_client.wait_for_remediation_completion(original_alert.id, timeout_s=90)
    api_client.resolve_alert_with_comment(original_alert.id, FINAL_COMMENT)

    # Run a new scan and check whether the same issue was detected again.
    api_client.start_scan()
    duplicates = api_client.find_identical_alerts(original_alert)

    # This assertion is expected to fail: the assignment says the app recreates the alert on purpose.
    assert not duplicates, (
        "Rescan recreated an identical alert after remediation. "
        f"original_alert={original_alert.id}, duplicate_ids={[alert.id for alert in duplicates]}"
    )
