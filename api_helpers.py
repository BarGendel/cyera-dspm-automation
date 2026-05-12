import logging
from dataclasses import dataclass
from typing import Any

from playwright.sync_api import APIRequestContext

from shared import AlertStatus, Settings, wait_until

logger = logging.getLogger(__name__)


STATUS_ALIASES = {
    "OPEN": AlertStatus.OPEN,
    "IN PROGRESS": AlertStatus.IN_PROGRESS,
    "REMEDIATION IN PROGRESS": AlertStatus.REMEDIATION_IN_PROGRESS,
    "AWAITING CUSTOMER": "Awaiting Customer",
    "AWAITING USER VERIFICATION": "Awaiting Customer",
    "REMEDIATED WAITING FOR CUSTOMER": "Awaiting Customer",
    "RESOLVED": AlertStatus.RESOLVED,
}


def normalize_status(value: Any) -> str:
    key = " ".join(str(value or "").replace("_", " ").replace("-", " ").upper().split())
    return STATUS_ALIASES.get(key, str(value or ""))


def _pick(payload: dict[str, Any], *paths: str) -> Any:
    for path in paths:
        value: Any = payload
        for part in path.split("."):
            if not isinstance(value, dict) or part not in value:
                break
            value = value[part]
        else:
            if value is not None:
                return value
    return None


def _as_bool(value: Any) -> bool | None:
    if value is None or isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "yes", "on", "enabled", "1"}


@dataclass(frozen=True)
class Alert:
    id: str
    status: str
    auto_remediate: bool | None
    title: str
    policy: str
    asset_id: str
    asset_name: str
    severity: str

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "Alert":
        alert_id = _pick(payload, "id", "alertId")
        if not alert_id:
            raise AssertionError(f"Alert payload is missing id: {payload}")

        return cls(
            id=str(alert_id),
            status=normalize_status(_pick(payload, "status", "state")),
            auto_remediate=_as_bool(
                _pick(payload, "remediation.autoRemediate", "policySnapshot.autoRemediate", "autoRemediate")
            ),
            title=str(_pick(payload, "description", "name", "title") or ""),
            policy=str(_pick(payload, "policyName", "policyId", "policy") or ""),
            asset_id=str(_pick(payload, "assetId", "asset.id") or ""),
            asset_name=str(_pick(payload, "assetDisplayName", "asset.metadata.name", "asset.name") or ""),
            severity=str(_pick(payload, "severity", "createdSeverity") or ""),
        )

    @property
    def search_text(self) -> str:
        return self.asset_name or self.title or self.id

    def identity(self) -> tuple[str, str, str, str]:
        return self.title, self.policy, self.asset_id, self.severity


class DspmApiClient:
    def __init__(self, request: APIRequestContext, settings: Settings):
        self.request = request
        self.settings = settings
        self.headers = {"Authorization": f"Bearer {settings.auth_token}"} if settings.auth_token else None

    def _expect(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        expected: tuple[int, ...] = (200,),
    ) -> Any:
        logger.debug("API %s %s", method, path)
        try:
            response = self.request.fetch(
                path,
                method=method,
                data=body,
                headers=self.headers,
                timeout=self.settings.api_timeout_ms,
            )
        except Exception as exc:
            logger.exception("API transport failed: %s %s", method, path)
            raise AssertionError(f"{method} {path} transport failed: {exc}") from exc

        try:
            response_body = response.json()
        except Exception:
            response_body = response.text() if response.status != 204 else None

        if response.status not in expected:
            logger.error("API %s %s returned %s: %s", method, path, response.status, response_body)
            raise AssertionError(f"{method} {path} returned {response.status}: {response_body}")
        logger.debug("API %s %s returned %s", method, path, response.status)
        return response_body

    def reset_data(self) -> None:
        logger.info("Resetting test data")
        self._expect("POST", f"{self.settings.bff_base_url}/api/admin/reset", expected=(200, 201, 202, 204))

    def start_scan(self) -> None:
        logger.info("Starting scan")
        current_count = len(self.list_alerts())
        self._expect("POST", "/api/scans", body={}, expected=(200, 201, 202))
        alerts = wait_until(
            lambda: alerts if len(alerts := self.list_alerts()) > current_count else None,
            timeout_s=90,
            description=f"alert count greater than {current_count}",
        )
        logger.info("Scan completed with %s alerts", len(alerts))

    def list_alerts(self) -> list[Alert]:
        payload = self._expect("GET", "/api/alerts")
        items = payload if isinstance(payload, list) else payload.get("alerts", [])
        alerts = [Alert.from_payload(item) for item in items]
        logger.debug("Found %s alerts", len(alerts))
        return alerts

    def find_alert(self, *, statuses: list[str], auto_remediate: bool, timeout_s: float = 30) -> Alert:
        wanted_statuses = {normalize_status(status) for status in statuses}

        def match() -> Alert | None:
            for alert in self.list_alerts():
                if normalize_status(alert.status) in wanted_statuses and alert.auto_remediate == auto_remediate:
                    logger.info("Matched alert %s: status=%s auto_remediate=%s", alert.id, alert.status, alert.auto_remediate)
                    return alert
            return None

        return wait_until(
            match,
            timeout_s=timeout_s,
            description=f"alert with statuses={statuses} auto_remediate={auto_remediate}",
        )

    def wait_for_remediation_completion(self, alert_id: str, *, timeout_s: float) -> Alert:
        logger.info("Waiting for auto-remediation completion for %s", alert_id)
        completed = {"Awaiting Customer", AlertStatus.RESOLVED}
        alert = wait_until(
            lambda: next(
                (
                    alert
                    for alert in self.list_alerts()
                    if alert.id == alert_id and normalize_status(alert.status) in completed
                ),
                None,
            ),
            timeout_s=timeout_s,
            description=f"auto-remediation completion for {alert_id}",
        )
        logger.info("Auto-remediation completed for %s with status %s", alert_id, alert.status)
        return alert

    def resolve_alert_with_comment(self, alert_id: str, comment: str) -> None:
        logger.info("Resolving alert %s with verification comment", alert_id)
        self._expect("PATCH", f"/api/alerts/{alert_id}", body={"status": "RESOLVED"}, expected=(200, 201, 202, 204))
        self._expect("PATCH", f"/api/alerts/{alert_id}", body={"comment": comment}, expected=(200, 201, 202, 204))

    def find_identical_alerts(self, original: Alert) -> list[Alert]:
        duplicates = [alert for alert in self.list_alerts() if alert.id != original.id and alert.identity() == original.identity()]
        logger.info("Identical alerts for %s: %s", original.id, [alert.id for alert in duplicates])
        return duplicates
