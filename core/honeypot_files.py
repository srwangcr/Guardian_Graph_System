import os
import time
import psutil
import subprocess
import hashlib
import pyshark
from utils.event_logger import log_event
from utils.config_manager import load_rules

# Ruta y archivos señuelo
decoy_path = "/home/shared/decoys/"
decoy_files = ["decoy1.txt", "decoy2.docx", "decoy3.xlsx"]
decoy_hashes = {}
config = load_rules("tests/test_config.yaml")  # usar config de pruebas
decoy_path = config["honeypot_path"]
decoy_files = config["honeypots"]["files"]
decoy_hashes = {}

# Calcular hash SHA-256 de un archivo
def calculate_hash(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(4096):
            hasher.update(chunk)
    return hasher.hexdigest()

# Crear archivos señuelo y guardar su hash original
def create_decoy_files():
    for filename in decoy_files:
        full_path = os.path.join(decoy_path, filename)
        if not os.path.exists(full_path):
            with open(full_path, "w") as f:
                f.write("Archivo señuelo para análisis de ransomware.\n")
            log_event(f"Honeypot creado: {full_path}")
        decoy_hashes[filename] = calculate_hash(full_path)

# Verificar si algún archivo fue modificado (posible cifrado)
def detect_encryption():
    for filename in decoy_files:
        full_path = os.path.join(decoy_path, filename)
        if not os.path.exists(full_path):
            return True
        current_hash = calculate_hash(full_path)
        if current_hash != decoy_hashes.get(filename):
            log_event(f"Modificación detectada en: {filename}")
            return True
    return False

# Aislar el proceso sospechoso en Docker
def isolate_process_in_docker(pid):
    log_event(f"Aislando proceso {pid} en contenedor Docker")
    subprocess.run([
        "docker", "run", "--rm", "-d",
        "--name", f"ransomware_container_{pid}",
        "--pid=host", "--security-opt", "no-new-privileges",
        "--volume", f"/proc/{pid}:/proc/{pid}",
        "ubuntu", "sleep", "3600"
    ])

# Activar PyShark para capturar tráfico saliente
def capture_network_with_pyshark():
    log_event("Iniciando captura de red con PyShark")
    capture = pyshark.LiveCapture(interface='eth0', bpf_filter='tcp')
    capture.sniff(timeout=10)
    for packet in capture:
        if 'IP' in packet:
            ip = packet.ip.dst
            log_event(f"Posible destino de clave de cifrado: {ip}")

# Ciclo principal de contención
def containment_cycle(tagged_users):
    create_decoy_files()
    while True:
        if detect_encryption():
            for proc in psutil.process_iter(['pid', 'name', 'username']):
                try:
                    pid = proc.info['pid']
                    username = proc.info['username']
                    if username in tagged_users:
                        isolate_process_in_docker(pid)
                        capture_network_with_pyshark()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        time.sleep(5)



def create_decoy_files():
    os.makedirs(decoy_path, exist_ok=True)
    for filename in decoy_files:
        full_path = os.path.join(decoy_path, filename)
        if not os.path.exists(full_path):
            with open(full_path, "w") as f:
                f.write("Archivo señuelo para análisis de ransomware.\n")
            log_event(f"Honeypot creado: {full_path}")
        decoy_hashes[filename] = calculate_hash(full_path)