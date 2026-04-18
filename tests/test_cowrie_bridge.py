from core.cowrie_bridge import emit_cowrie_event, parse_cowrie_event


def test_parse_cowrie_event_extracts_key_fields():
    payload = '{"eventid":"cowrie.login.failed","src_ip":"192.0.2.10","username":"root","password":"toor","input":"ssh root@host"}'

    event = parse_cowrie_event(payload)

    assert event["event_id"] == "cowrie.login.failed"
    assert event["src_ip"] == "192.0.2.10"
    assert event["username"] == "root"


def test_emit_cowrie_event_writes_structured_log(tmp_path):
    log_path = tmp_path / "system_events.log"
    event = {
        "event_id": "cowrie.login.failed",
        "src_ip": "192.0.2.10",
        "username": "root",
        "command": "ssh root@host",
    }

    emit_cowrie_event(event, log_path=str(log_path))

    content = log_path.read_text(encoding="utf-8")
    assert "cowrie.login.failed" in content
    assert "192.0.2.10" in content