import psutil
import time
from utils.event_logger import log_event
from utils.config_manager import load_rules

# Cargar reglas desde el archivo de configuración
rules = load_rules("config.yaml")

# Diccionario para almacenar usuarios etiquetados y sus tags
tagged_users = {}  # Ejemplo: {'usuario1': ['tag1', 'tag2']}

# Función principal de monitoreo
def monitor_user_behavior():
    while True:
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cmdline']):
            try:
                process_name = proc.info['name']
                cmdline = proc.info.get('cmdline', [])
                username = proc.info['username']

                evaluate_rules(username, process_name, cmdline)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        time.sleep(5)  # Monitorear cada 5 segundos

# Función para evaluar reglas de comportamiento
def evaluate_rules(username, process_name, cmdline):
    for rule in rules.get('user_behavior_rules', []):
        # Validar que el usuario coincida con la regla
        if rule['username'] == username:
            # Validar que cmdline exista y no contenga el tag esperado
            if cmdline and rule['tag'] not in ' '.join(cmdline):
                tag_user(username, rule['tag'])
                log_event(f"Usuario '{username}' etiquetado con '{rule['tag']}' por ejecutar '{process_name}'")

# Función para etiquetar usuarios
def tag_user(username, tag):
    if username not in tagged_users:
        tagged_users[username] = [tag]
    elif tag not in tagged_users[username]:
        tagged_users[username].append(tag)
