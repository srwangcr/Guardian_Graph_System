import logging
from datetime import datetime
import os


def log_event(message, level="info", log_path="system_events.log"):
    logger = logging.getLogger("event_logger")
    logger.setLevel(logging.INFO)

    # Verificar si ya existe un handler para este archivo
    log_path_abs = os.path.abspath(log_path)
    if not any(
        isinstance(h, logging.FileHandler) and os.path.abspath(h.baseFilename) == log_path_abs
        for h in logger.handlers
    ):
        file_handler = logging.FileHandler(log_path)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {message}"

    # Registrar el evento
    if level == "info":
        logger.info(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "error":
        logger.error(message)
    else:
        logger.debug(message)

    # Forzar escritura inmediata en el archivo
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.flush()

    print(formatted)
