import os
import hashlib
from utils.event_logger import log_event
from utils.config_manager import load_rules

# Cargar configuración desde archivo de pruebas
config = load_rules("tests/test_config.yaml")
decoy_path = config["honeypot_path"]
decoy_files = config["honeypots"]["files"]
log_path = config["log_file"]
decoy_hashes = {}

def calculate_hash(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(4096):
            hasher.update(chunk)
    return hasher.hexdigest()

def create_decoy_files():
    os.makedirs(decoy_path, exist_ok=True)
    for filename in decoy_files:
        full_path = os.path.join(decoy_path, filename)
        with open(full_path, "w") as f:
            f.write("Archivo señuelo para pruebas.\n")
        decoy_hashes[filename] = calculate_hash(full_path)
        log_event(f"Honeypot creado: {full_path}", log_path=log_path)

def detect_encryption():
    for filename in decoy_files:
        full_path = os.path.join(decoy_path, filename)
        if not os.path.exists(full_path):
            return True
        current_hash = calculate_hash(full_path)
        if current_hash != decoy_hashes.get(filename):
            log_event(f"Modificación detectada en: {filename}", log_path=log_path)
            return True
    return False
