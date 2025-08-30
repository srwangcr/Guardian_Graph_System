import os
from core.honeypot_files import create_decoy_files
from utils.config_manager import load_rules
from utils.event_logger import log_event
from core.containment_system import calculate_hash

# Variables globales necesarias
config = load_rules("tests/test_config.yaml")
decoy_path = config["honeypot_path"]
decoy_files = config["honeypots"]["files"]
decoy_hashes = {}

def create_decoy_files():
    global decoy_hashes
    os.makedirs(decoy_path, exist_ok=True)
    for filename in decoy_files:
        full_path = os.path.join(decoy_path, filename)
        if not os.path.exists(full_path):
            with open(full_path, "w") as f:
                f.write("Archivo señuelo para pruebas.\n")
            log_event(f"Honeypot creado: {full_path}", log_path=config["log_file"])
        # Siempre calcular y guardar el hash
        decoy_hashes[filename] = calculate_hash(full_path)

def test_honeypots_created():
    create_decoy_files()

    expected_files = ["contraseña.txt", "pepe.txt"]
    for fname in expected_files:
        assert os.path.exists(os.path.join(decoy_path, fname))
