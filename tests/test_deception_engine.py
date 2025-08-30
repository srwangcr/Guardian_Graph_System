from core.deception_engine import user_count
from core.behavior_monitor import tagged_users

def test_user_count_returns_dict():
    # Simular usuarios etiquetados
    tagged_users["user1"] = ["scanner"]
    tagged_users["user2"] = ["editor_sensible"]
    tagged_users["user3"] = ["honeypot_access"]

    # Ejecutar evaluación de riesgo
    risk_map, _ = user_count()

    # Validaciones
    assert isinstance(risk_map, dict)
    assert len(risk_map) >= 3
    assert "user1" in risk_map
    assert "user2" in risk_map
    assert "user3" in risk_map
