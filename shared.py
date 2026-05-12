import logging
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    return default if value is None else value.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    return default if value is None else int(value)


@dataclass(frozen=True)
class Settings:
    web_base_url: str = os.getenv("WEB_BASE_URL", "http://localhost:3000").rstrip("/")
    api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:8080").rstrip("/")
    bff_base_url: str = os.getenv("BFF_BASE_URL", web_base_url).rstrip("/")
    auth_token: str = os.getenv("CYERA_AUTH_TOKEN", "fake-jwt-token")
    username: str = os.getenv("CYERA_USERNAME", "admin")
    password: str = os.getenv("CYERA_PASSWORD", "Aa123456")
    headless: bool = _bool_env("HEADLESS", False)
    slow_mo_ms: int = _int_env("SLOW_MO_MS", 0)
    default_timeout_ms: int = _int_env("DEFAULT_TIMEOUT_MS", 15_000)
    api_timeout_ms: int = _int_env("API_TIMEOUT_MS", 15_000)


class AlertStatus:
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    REMEDIATION_IN_PROGRESS = "Remediation In Progress"
    RESOLVED = "Resolved"


def wait_until(condition: Callable[[], Any], *, timeout_s: float, description: str) -> Any:
    logger = logging.getLogger(__name__)
    deadline = time.monotonic() + timeout_s
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            result = condition()
            if result:
                return result
        except Exception as exc:
            last_error = exc
        time.sleep(1)

    message = f"Timed out waiting for {description}"
    if last_error:
        logger.exception(message)
        raise AssertionError(message) from last_error
    logger.error(message)
    raise AssertionError(message)
