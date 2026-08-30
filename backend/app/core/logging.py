import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from app.core.request_id import get_request_id

# Fields that must never be emitted to logs (defense in depth; see 05-SECURITY.md §7).
_REDACTED_KEYS = frozenset(
    {
        "authorization",
        "api_key",
        "apikey",
        "secret",
        "password",
        "signing_key",
        "private_key",
        "token",
    }
)


class JsonFormatter(logging.Formatter):
    """Emit structured JSON log lines with a correlation ID, never secrets."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = get_request_id()
        if request_id is not None:
            payload["request_id"] = request_id

        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            for key, value in extra.items():
                if key.lower() in _REDACTED_KEYS:
                    continue
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str) -> None:
    """Install the JSON formatter on the root logger (idempotent)."""

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
