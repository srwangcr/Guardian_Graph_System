import os
import shutil
import subprocess
import sys

# Rutas de prueba
TEST_CONFIG_PATH = "tests/test_config.yaml"
TEST_LOG_PATH = "test_system_events.log"
TEST_DECOY_PATH = "./test_decoys/"
EXPECTED_HONEYPOTS = ["contraseña.txt", "pepe.txt"]

def prepare_environment():
    print("🔧 Preparando entorno de pruebas...")

    # Limpiar logs
    if os.path.exists(TEST_LOG_PATH):
        os.remove(TEST_LOG_PATH)
        print("🧹 Log de eventos limpiado.")

    # Limpiar honeypots
    if os.path.exists(TEST_DECOY_PATH):
        shutil.rmtree(TEST_DECOY_PATH)
        print("🧹 Carpeta de honeypots eliminada.")

    os.makedirs(TEST_DECOY_PATH, exist_ok=True)
    for fname in EXPECTED_HONEYPOTS:
        with open(os.path.join(TEST_DECOY_PATH, fname), "w") as f:
            f.write("Archivo señuelo para pruebas.\n")
    print("📁 Honeypots regenerados.")

def run_pytest():
    print("\n🚀 Ejecutando pruebas unitarias...\n")
    result = subprocess.run(["pytest", "tests/", "--tb=short"], capture_output=True, text=True)

    print(result.stdout)
    if result.returncode == 0:
        print("✅ Todas las pruebas pasaron correctamente.")
    else:
        print("❌ Se detectaron fallos en las pruebas.")
        print(result.stderr)

def main():
    os.environ["PYTHONPATH"] = "."
    prepare_environment()
    run_pytest()

if __name__ == "__main__":
    main()
