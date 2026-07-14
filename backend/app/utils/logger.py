"""
logger.py — Structured logging setup for PRISM backend.

WHY THIS EXISTS:
A single logger setup means consistent log format across all modules.
In development, logs are human-readable console output.
In production, logs are JSON lines for log aggregation tools.

Library: logging (stdlib, no license needed). No external dependencies.
"""

import logging
import json
import sys
from datetime import datetime, timezone
from app.config import settings


class _JSONFormatter(logging.Formatter):
    """Formats log records as JSON lines for production log aggregators."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


class _ConsoleFormatter(logging.Formatter):
    """Human-readable formatter for development."""
    FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    DATE_FORMAT = "%H:%M:%S"

    def format(self, record: logging.LogRecord) -> str:
        formatter = logging.Formatter(self.FORMAT, datefmt=self.DATE_FORMAT)
        return formatter.format(record)


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger for the given module name.
    Call as: logger = get_logger(__name__)
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # Already configured — avoid duplicate handlers

    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if settings.environment == "production":
        handler.setFormatter(_JSONFormatter())
    else:
        handler.setFormatter(_ConsoleFormatter())

    logger.addHandler(handler)
    logger.propagate = False
    return logger
