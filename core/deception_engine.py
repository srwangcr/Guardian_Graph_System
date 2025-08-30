import psutil
from psutil import NoSuchProcess, AccessDenied, ZombieProcess
from utils.event_logger import log_event
from utils.config_manager import load_rules
from collections import defaultdict
from core.behavior_monitor import tagged_users

# Cargar configuración desde archivo de pruebas
config = load_rules("tests/test_config.yaml")
rules = config.get("rules", [])
risk_levels = config.get("risk_levels", {
    "suspicious": 2,
    "detected": 5,
    "full_monitoring": 8
})

def user_count():
    user_risk_actions = defaultdict(int)
    user_risk_level = {}

    # Evaluar procesos activos según reglas
    for proc in psutil.process_iter(['pid', 'name', 'username']):
        try:
            process_name = proc.info['name']
            user = proc.info['username']

            for rule in rules:
                if rule.get("process_name") == process_name and rule.get("tag") in rule.get("tag", ""):
                    user_risk_actions[user] += 1
        except (NoSuchProcess, AccessDenied, ZombieProcess):
            continue

    # Evaluar usuarios etiquetados manualmente (modo test)
    for user, tags in tagged_users.items():
        count = len(tags)
        if count == 0:
            level = "Detected"
        elif count <= 5:
            level = "Suspicious"
        else:
            level = "Full monitoring"
        user_risk_level[user] = level
        user_risk_actions[user] += count
        log_event(f"User {user} has been tagged as {level} due to {count} risky actions.")

    return user_risk_level, user_risk_actions
