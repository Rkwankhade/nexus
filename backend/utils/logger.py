"""
Structured JSON logging for NEXUS backend.

Provides a single `get_logger(name)` factory used across routers, services,
and tool wrappers so log lines are consistently formatted and easy to ship
to a log aggregator (ELK, Loki, etc).
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Optional

_CONFIGURED = False


class JSONFormatter(logging.Formatter):
    """Renders log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # Allow callers to pass structured extras: logger.info("msg", extra={"extra_fields": {...}})
        extra_fields = getattr(record, "extra_fields", None)
        if isinstance(extra_fields, dict):
            payload.update(extra_fields)

        for attr in ("request_id", "user_id", "job_id", "scan_id", "target_id"):
            value = getattr(record, attr, None)
            if value is not None:
                payload[attr] = value

        return json.dumps(payload, default=str)


class ContextLoggerAdapter(logging.LoggerAdapter):
    """
    LoggerAdapter that lets call sites pass structured fields directly:

        log = get_logger(__name__)
        log.info("scan started", extra_fields={"scan_id": str(scan.id)})
    """

    def process(self, msg, kwargs):
        return msg, kwargs


def _configure_root(level: int) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    root = logging.getLogger()
    root.setLevel(level)

    # Remove any pre-existing handlers (e.g. uvicorn defaults) to avoid dupes
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root.addHandler(handler)

    # Tame noisy third-party loggers
    for noisy in ("uvicorn.access", "httpx", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Return a configured logger. Safe to call repeatedly (idempotent root setup).

    Usage:
        log = get_logger(__name__)
        log.info("nmap scan completed", extra={"extra_fields": {"scan_id": scan_id}})
    """
    _configure_root(level if level is not None else logging.INFO)
    return logging.getLogger(name)


def log_event(
    logger: logging.Logger,
    level: str,
    message: str,
    **fields: Any,
) -> None:
    """
    Convenience helper for one-off structured log lines without constructing
    the `extra={"extra_fields": {...}}` dict manually.

        log_event(log, "info", "job finished", job_id=job.id, duration_ms=42)
    """
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(message, extra={"extra_fields": fields})
