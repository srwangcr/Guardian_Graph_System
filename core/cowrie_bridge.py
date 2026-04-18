from __future__ import annotations

import json
from pathlib import Path

import requests

from utils.event_logger import log_event


def parse_cowrie_event(raw_line: str) -> dict:
    payload = json.loads(raw_line)
    summary = {
        "event_id": payload.get("eventid") or payload.get("event_id") or payload.get("event"),
        "src_ip": payload.get("src_ip") or payload.get("source_ip"),
        "username": payload.get("username") or payload.get("user"),
        "password": payload.get("password"),
        "command": payload.get("input") or payload.get("command"),
        "raw": payload,
    }
    return summary


def emit_cowrie_event(event: dict, log_path: str = "system_events.log", webhook_url: str | None = None) -> dict:
    event_id = event.get("event_id") or "cowrie_event"
    message = (
        f"Cowrie {event_id} from {event.get('src_ip') or 'unknown'} "
        f"user={event.get('username') or 'unknown'}"
    )
    log_event(
        message,
        event_type="cowrie",
        source="cowrie",
        log_path=log_path,
        src_ip=event.get("src_ip"),
        username=event.get("username"),
        command=event.get("command"),
    )

    if webhook_url:
        requests.post(webhook_url, json=event, timeout=3)

    return event


def ingest_cowrie_log(log_file: str, log_path: str = "system_events.log", webhook_url: str | None = None) -> int:
    path = Path(log_file)
    if not path.exists():
        return 0

    ingested = 0
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        event = parse_cowrie_event(raw_line)
        emit_cowrie_event(event, log_path=log_path, webhook_url=webhook_url)
        ingested += 1
    return ingested