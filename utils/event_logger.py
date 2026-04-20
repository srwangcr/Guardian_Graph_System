from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
import os
from typing import Any

import requests

from utils.telemetry import record_event


_LOGGER_CACHE: dict[str, logging.Logger] = {}
_SIEM_CONFIG: dict[str, Any] | None = None


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


def _load_siem_config() -> dict[str, Any]:
    global _SIEM_CONFIG
    if _SIEM_CONFIG is not None:
        return _SIEM_CONFIG

    config_path = os.getenv("GGS_CONFIG_PATH", "config.yaml")
    if not os.path.exists(config_path):
        _SIEM_CONFIG = {}
        return _SIEM_CONFIG

    try:
        import yaml

        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        _SIEM_CONFIG = cfg.get("siem", {}) or {}
    except Exception:
        _SIEM_CONFIG = {}
    return _SIEM_CONFIG


def _forward_to_elasticsearch(payload: dict[str, Any], config: dict[str, Any]) -> None:
    endpoint = config.get("endpoint")
    if not endpoint:
        return

    index_name = config.get("index", "guardian-events")
    url = f"{endpoint.rstrip('/')}/{index_name}/_doc"
    headers = {"Content-Type": "application/json"}
    api_key = config.get("api_key")
    if api_key:
        headers["Authorization"] = f"ApiKey {api_key}"

    requests.post(url, headers=headers, json=payload, timeout=2)


def _forward_to_splunk(payload: dict[str, Any], config: dict[str, Any]) -> None:
    endpoint = config.get("endpoint")
    token = config.get("hec_token")
    if not endpoint or not token:
        return

    headers = {
        "Authorization": f"Splunk {token}",
        "Content-Type": "application/json",
    }
    body = {
        "event": payload,
        "source": payload.get("source", "guardian_graph"),
        "sourcetype": "guardian:json",
    }
    requests.post(endpoint, headers=headers, json=body, timeout=2)


def _forward_to_siem(payload: dict[str, Any]) -> None:
    config = _load_siem_config()
    if not config or not config.get("enabled", False):
        return

    backend = (config.get("backend") or "").lower()
    backend_config = config.get(backend, {}) if isinstance(config.get(backend), dict) else {}
    try:
        if backend == "elasticsearch":
            _forward_to_elasticsearch(payload, backend_config)
        elif backend == "splunk":
            _forward_to_splunk(payload, backend_config)
    except Exception:
        # Never block local detection pipeline because of SIEM egress failures.
        pass


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
    payload = {
        "timestamp": timestamp,
        "level": level_name,
        "message": message,
        "event_type": event_type,
        "source": source,
        "context": context,
    }
    _forward_to_siem(payload)

    print(formatted)
    return payload
