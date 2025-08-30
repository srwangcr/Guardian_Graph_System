from utils.event_logger import log_event
import os

def test_log_event_creates_entry():
    log_path = "test_system_events.log"
    if os.path.exists(log_path):
        os.remove(log_path)

    # Usar log_path explícito desde el inicio
    log_event("Prueba de evento", log_path=log_path)
    assert os.path.exists(log_path)

    with open(log_path, "r") as f:
        content = f.read()
    assert "Prueba de evento" in content
def test_log_event_creates_entry(tmp_path):
    log_path = tmp_path / "test_system_events.log"
    log_event("Prueba de evento", log_path=str(log_path))
    assert log_path.exists()
    assert "Prueba de evento" in log_path.read_text()
