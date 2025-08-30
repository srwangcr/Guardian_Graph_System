```markdown
# 🛡️ GGS: Guardian Graph System

**Defensa activa. Frustración táctica. Contención adaptativa.**  
GGS es una herramienta modular de ciberseguridad diseñada para detectar, engañar y contener actores maliciosos en sistemas Linux. Su enfoque no es simplemente reaccionar, sino **anticipar y desestabilizar** al atacante mediante señuelos, monitoreo inteligente y respuestas controladas.

---

## 🚀 Características principales

- **Decepción estratégica:** Generación de honeypots y archivos señuelo para atraer y marcar comportamientos sospechosos.
- **Evaluación de riesgo dinámica:** Asignación de niveles de riesgo por usuario según patrones de acceso, procesos activos y etiquetas de comportamiento.
- **Contención modular:** Detección de cifrado en honeypots y activación de medidas de aislamiento (Docker, monitoreo de red, etc.).
- **Logging persistente:** Registro estructurado de eventos con timestamps, niveles y contexto, configurable por entorno.
- **Arquitectura escalable:** Separación clara entre núcleo (`core/`), utilidades (`utils/`) y pruebas (`tests/`), con configuración externa (`config.yaml`).

---

## ⚙️ Instalación

```bash
git clone https://github.com/jurgen-dev/GGS.git
cd GGS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🧪 Pruebas

Para ejecutar la suite completa de pruebas:

```bash
python run_tests.py
```

Esto prepara el entorno, regenera honeypots, limpia logs y ejecuta todos los módulos en modo aislado.

---

## 📁 Estructura del proyecto

```
GGS/
├── core/
│   ├── deception_engine.py
│   ├── containment_system.py
│   └── honeypot_files.py
├── utils/
│   ├── config_manager.py
│   └── event_logger.py
├── tests/
│   ├── test_config.yaml
│   ├── test_event_logger.py
│   └── ...
├── run_tests.py
├── README.md
└── LICENSE
```

---

## 🧠 Filosofía del sistema

GGS no busca bloquear al atacante. Busca **confundirlo, ralentizarlo y exponerlo**.  
Cada interacción con un honeypot, cada proceso sospechoso, cada intento de cifrado es una oportunidad para marcar, registrar y responder.  
Este sistema está diseñado para ser **extendido, auditado y adaptado** por la comunidad. Su modularidad permite integrar nuevas técnicas de detección, visualización CLI, o incluso respuestas automatizadas.

---

## 📜 Licencia

Este proyecto está licenciado bajo la **GNU General Public License v3.0 (GPLv3)**.  
Esto significa que cualquier modificación o redistribución debe mantenerse libre y abierta.  
Para más información, consultá [https://www.gnu.org/licenses/gpl-3.0.html](https://www.gnu.org/licenses/gpl-3.0.html).

---

## 🤝 Contribuciones

Toda mejora es bienvenida. Si querés agregar módulos, refactorizar lógica, o proponer nuevas estrategias de defensa, abrí un issue o enviá un pull request.  
Este sistema es tan fuerte como la comunidad que lo respalda.

---

## ✨ Estado actual

✅ MVP funcional  
✅ Pruebas automatizadas  
✅ Arquitectura modular  
🔜 Integración continua  
🔜 Visualización CLI  
🔜 Simulador de ataque

---

**Construido por srwangcr** — estudiante de Ingeniería en Sistemas y desarrollador de herramientas abiertas para la defensa digital.  
GGS es más que un proyecto: es una declaración de estrategia.

```
---