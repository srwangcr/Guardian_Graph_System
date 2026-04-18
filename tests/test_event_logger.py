import json

from utils.event_logger import log_event


def test_log_event_creates_structured_entry(tmp_path):
    log_path = tmp_path / "test_system_events.log"

    log_event("Prueba de evento", log_path=str(log_path), event_type="unit_test", source="tests")

    assert log_path.exists()
    content = log_path.read_text(encoding="utf-8").strip()
    payload = json.loads(content)
    assert payload["message"] == "Prueba de evento"
    assert payload["event_type"] == "unit_test"
    assert payload["source"] == "tests"
