from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

try:
    import pyshark
except ImportError:  # pragma: no cover - optional runtime dependency
    pyshark = None

from utils.config_manager import load_rules
from utils.event_logger import log_event


config = load_rules(os.getenv("GGS_CONFIG_PATH", "tests/test_config.yaml"))
level_malicious_process = load_rules("configs/config_levels.yaml")

decoy_path = config["honeypot_path"]
decoy_files = config["honeypots"]["files"]
log_path = config["log_file"]
decoy_hashes: dict[str, str] = {}


def _containment_queue_path() -> Path:
    queue_path = config.get("containment", {}).get("queue_file", "containment_actions.queue")
    return Path(queue_path)


@dataclass(frozen=True)
class ContainmentAction:
    action: str
    pid: int | None = None
    docker_image: str | None = None
    interface: str | None = None
    detection_type: str | None = None
    metadata: dict[str, Any] | None = None


def enqueue_containment_action(action: ContainmentAction) -> None:
    queue_path = _containment_queue_path()
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(action), ensure_ascii=False) + "\n")
    log_event(
        f"Accion de contencion encolada: {action.action}",
        log_path=log_path,
        event_type="containment_queued",
        action=action.action,
        pid=action.pid,
    )


def _execute_action(action: ContainmentAction) -> None:
    if action.action == "isolate_in_docker" and action.pid:
        isolate_process_in_docker(action.pid, action.docker_image or "ubuntu:latest")
    elif action.action == "network_capture":
        capture_network_with_pyshark(action.interface or "eth0")
    elif action.action == "kill_process" and action.pid:
        os.kill(action.pid, signal.SIGKILL)
        log_event(f"Proceso {action.pid} terminado", log_path=log_path, event_type="containment_kill")


def run_containment_agent(poll_interval: float = 1.0) -> None:
    """
    Agent process intended to run with elevated privileges.

    The analysis engine only enqueues actions using least privilege.
    """
    queue_path = _containment_queue_path()
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.touch(exist_ok=True)

    cursor = 0
    log_event("Containment agent iniciado", log_path=log_path, event_type="containment_agent_start")
    while True:
        with queue_path.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        while cursor < len(lines):
            raw = lines[cursor].strip()
            cursor += 1
            if not raw:
                continue
            try:
                payload = json.loads(raw)
                action = ContainmentAction(**payload)
                _execute_action(action)
            except Exception as exc:
                log_event(
                    f"Error ejecutando accion de contencion: {exc}",
                    level="error",
                    log_path=log_path,
                    event_type="containment_agent_error",
                )

        time.sleep(poll_interval)


def assignment_alert_malicius_process(process_info, detection_type="encryption"):
    """
    Asigna nivel de severidad y encola acciones según config_levels.yaml.
    """
    level = determine_severity_level(detection_type)
    level_config = level_malicious_process["malicious_levels"].get(f"level_{level}")

    if not level_config:
        log_event(f"Nivel desconocido: {level}", log_path=log_path)
        return

    log_event(
        f"Proceso {process_info['pid']} asignado a {level_config['name']} (severity={level})",
        log_path=log_path,
        event_type="containment_assignment",
        pid=process_info.get("pid"),
        detection_type=detection_type,
    )

    direct_execute = bool(config.get("containment", {}).get("direct_execute", False))
    for action_name in level_config["actions"]:
        action = ContainmentAction(
            action=action_name,
            pid=process_info.get("pid"),
            docker_image=level_config.get("docker_image"),
            interface=level_config.get("capture_interface"),
            detection_type=detection_type,
            metadata={"level": level, "name": level_config.get("name")},
        )
        if direct_execute:
            _execute_action(action)
        else:
            enqueue_containment_action(action)


def determine_severity_level(detection_type):
    level_map = {
        "suspicious": 1,
        "network_anomaly": 2,
        "encryption": 3,
    }
    return level_map.get(detection_type, 1)


def calculate_hash(filepath):
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(4096):
            hasher.update(chunk)
    return hasher.hexdigest()


def create_decoy_files():
    os.makedirs(decoy_path, exist_ok=True)
    for filename in decoy_files:
        full_path = os.path.join(decoy_path, filename)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write("Archivo señuelo para pruebas.\n")
        decoy_hashes[filename] = calculate_hash(full_path)
        log_event(f"Honeypot creado: {full_path}", log_path=log_path, event_type="honeypot_create")


def detect_encryption():
    for filename in decoy_files:
        full_path = os.path.join(decoy_path, filename)
        if not os.path.exists(full_path):
            return True
        current_hash = calculate_hash(full_path)
        if current_hash != decoy_hashes.get(filename):
            log_event(f"Modificacion detectada en: {filename}", log_path=log_path, event_type="honeypot_modify")
            return True
    return False


def isolate_process_in_docker(pid, docker_image="ubuntu:latest"):
    log_event(f"Aislando proceso {pid} en contenedor Docker", log_path=log_path, event_type="containment_isolate")
    try:
        subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-d",
                "--name",
                f"ransomware_container_{pid}",
                "--pid=host",
                "--security-opt",
                "no-new-privileges",
                "--volume",
                f"/proc/{pid}:/proc/{pid}",
                docker_image,
                "sleep",
                "3600",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        log_event(f"Error al aislar proceso {pid}: {e}", level="error", log_path=log_path, event_type="containment_error")


def capture_network_with_pyshark(interface="eth0"):
    if pyshark is None:
        log_event("PyShark no esta disponible en este entorno.", log_path=log_path)
        return
    log_event(f"Iniciando captura de red en {interface}", log_path=log_path, event_type="network_capture")
    try:
        capture = pyshark.LiveCapture(interface=interface, bpf_filter="tcp")
        capture.sniff(timeout=10)
        for packet in capture:
            if "IP" in packet:
                ip = packet.ip.dst
                log_event(f"Destino de red capturado: {ip}", log_path=log_path, event_type="network_capture_destination")
    except Exception as e:
        log_event(f"Error en captura de red: {e}", level="error", log_path=log_path, event_type="network_capture_error")
