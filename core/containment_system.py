import os
import hashlib
import subprocess
import pyshark
from utils.event_logger import log_event
from utils.config_manager import load_rules

# Cargar configuración desde archivo de pruebas
config = load_rules("tests/test_config.yaml")
decoy_path = config["honeypot_path"]
decoy_files = config["honeypots"]["files"]
log_path = config["log_file"]
log_proccess = config.get("log_process", False)
level_malicious_process = load_rules("configs/config_levels.yaml")
decoy_hashes = {}

def assignment_alert_malicius_process(process_info, detection_type="encryption"):
    """
    Asigna nivel de severidad y ejecuta acciones según config_levels.yaml
    
    Args:
        process_info: dict con pid, name, username
        detection_type: "encryption", "suspicious", "network_anomaly"
    """
    # Determinar nivel inicial (1-3)
    level = determine_severity_level(detection_type)
    level_config = level_malicious_process["malicious_levels"].get(f"level_{level}")
    
    if not level_config:
        log_event(f"Nivel desconocido: {level}", log_path=log_path)
        return
    
    log_event(
        f"Proceso {process_info['pid']} asignado a {level_config['name']} "
        f"(severity={level})",
        log_path=log_path
    )
    
    # Ejecutar acciones según nivel
    for action in level_config["actions"]:
        if action == "log_event":
            log_event(f"ALERTA [{level_config['name']}]: {process_info}", log_path=log_path)
        elif action == "isolate_in_docker" and level_config["isolation"]:
            isolate_process_in_docker(process_info['pid'], level_config.get("docker_image"))
        elif action == "network_capture" and level_config["network_capture"]:
            capture_network_with_pyshark(level_config.get("capture_interface"))
        elif action == "kill_process":
            os.kill(process_info['pid'], 9)
            log_event(f"Proceso {process_info['pid']} terminado", log_path=log_path)

def determine_severity_level(detection_type):
    """Retorna nivel (1-3) según tipo de detección"""
    level_map = {
        "suspicious": 1,
        "network_anomaly": 2,
        "encryption": 3
    }
    return level_map.get(detection_type, 1)

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

def isolate_process_in_docker(pid, docker_image="ubuntu:latest"):
    """Aisla un proceso en un contenedor Docker"""
    log_event(f"Aislando proceso {pid} en contenedor Docker", log_path=log_path)
    try:
        subprocess.run([
            "docker", "run", "--rm", "-d",
            "--name", f"ransomware_container_{pid}",
            "--pid=host", "--security-opt", "no-new-privileges",
            "--volume", f"/proc/{pid}:/proc/{pid}",
            docker_image, "sleep", "3600"
        ], check=True)
    except subprocess.CalledProcessError as e:
        log_event(f"Error al aislar proceso {pid}: {e}", log_path=log_path)

def capture_network_with_pyshark(interface="eth0"):
    """Captura tráfico de red con PyShark"""
    log_event(f"Iniciando captura de red en {interface}", log_path=log_path)
    try:
        capture = pyshark.LiveCapture(interface=interface, bpf_filter='tcp')
        capture.sniff(timeout=10)
        for packet in capture:
            if 'IP' in packet:
                ip = packet.ip.dst
                log_event(f"Destino de red capturado: {ip}", log_path=log_path)
    except Exception as e:
        log_event(f"Error en captura de red: {e}", log_path=log_path)
