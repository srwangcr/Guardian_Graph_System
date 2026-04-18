from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
import os

from utils.telemetry import record_event


_LOGGER_CACHE: dict[str, logging.Logger] = {}


class StructuredJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "message": record.getMessage(),
            "event_type": getattr(record, "event_type", "general"),
            "source": getattr(record, "source", "guardian_graph"),
            "context": getattr(record, "context", {}),
        }
        return json.dumps(payload, ensure_ascii=False)


def _get_logger(log_path: str) -> logging.Logger:
    log_path_abs = os.path.abspath(log_path)
    logger = _LOGGER_CACHE.get(log_path_abs)
    if logger is not None:
        return logger

    logger = logging.getLogger(f"guardian_graph.{log_path_abs}")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not any(
        isinstance(handler, logging.FileHandler) and os.path.abspath(handler.baseFilename) == log_path_abs
        for handler in logger.handlers
    ):
        file_handler = logging.FileHandler(log_path_abs, encoding="utf-8")
        file_handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(file_handler)

    _LOGGER_CACHE[log_path_abs] = logger
    return logger


def log_event(message, level="info", log_path="system_events.log", event_type="general", source="guardian_graph", **context):
    logger = _get_logger(log_path)

    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    level_name = level.lower()
    log_level = level_map.get(level_name, logging.INFO)

    logger.log(
        log_level,
        message,
        extra={"event_type": event_type, "source": source, "context": context},
    )

    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.flush()

    record_event(level_name, event_type, source=source)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {level_name.upper()} {event_type}: {message}"
    print(formatted)
    return {
        "timestamp": timestamp,
        "level": level_name,
        "message": message,
        "event_type": event_type,
        "source": source,
        "context": context,
    }
