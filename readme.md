# GGS: Guardian Graph System

GGS is a modular active-defense prototype for Linux. The repository combines structured logging, Prometheus telemetry, rule-based risk scoring, honeypots and decoys, privilege-aware containment orchestration, anomaly-assisted scoring, and a Cowrie event bridge.

## What is implemented today

- `main.py` starts the CLI dashboard by default and can switch to demo mode (`--demo`), API mode (`--api`), or privileged containment-agent mode (`--containment-agent`).
- `utils/api_server.py` exposes a protected REST API with OAuth2 bearer token flow.
- `utils/event_logger.py` writes structured JSON events to disk, updates telemetry counters, and can forward to SIEM backends.
- `utils/telemetry.py` exposes Prometheus counters and gauges.
- `core/risk_engine.py` classifies risk from scores and threshold rules.
- `core/anomaly_detector.py` provides lightweight anomaly detection (rolling z-score) to complement static rules.
- `core/behavior_monitor.py` tags users according to behavior rules when such rules are present in the loaded config.
- `core/deception_engine.py` combines active processes, rules, tags, and anomaly boosts into a per-user risk summary.
- `core/honeypot_files.py` creates, monitors, and recreates decoy files and a honeypot process.
- `core/containment_system.py` now supports queued containment actions and a separate privileged agent.
- `core/cowrie_bridge.py` parses Cowrie JSON events and emits them as GGS events.
- `utils/cli_dashboard.py` renders tagged users, risk levels, and an events panel with Rich.
- `web/dashboard_streamlit.py` provides a lightweight web dashboard with live polling for alerts and risk endpoints.
- `run_tests.py` prepares the test environment, regenerates decoys, and runs `pytest`.

## Configuration overview

The default configuration is defined in [config.yaml](config.yaml) and the containment severity map lives in [configs/config_levels.yaml](configs/config_levels.yaml).

### [config.yaml](config.yaml)

This file currently defines:

- `scan_interval`: default process scan interval in seconds.
- `honeypot_path`: location for decoy files.
- `log_file`: structured event log destination.
- `rules`: process-matching rules with `process_name`, `cmd_contains`, and `tag`.
- `risk_levels`: thresholds for `suspicious`, `detected`, and `full_monitoring`.
- `actions`: declarative response flags per risk level.
- `honeypots`: enabled decoys and their filenames.
- `containment`: Docker image and network/encryption monitoring flags plus `queue_file` and `direct_execute` for privilege separation.
- `notifications`: webhook settings for external alerts.
- `api`: static tokens and service accounts for OAuth2 bearer access.
- `anomaly_detection`: z-score detector controls (`enabled`, `history_size`, `z_threshold`, `max_boost`).
- `siem`: optional remote audit forwarding (`elasticsearch` or `splunk`).

### [configs/config_levels.yaml](configs/config_levels.yaml)

This file maps severity levels to response profiles:

- `level_1` is low-risk, logging and process monitoring only.
- `level_2` adds increased monitoring and optional network capture.
- `level_3` enables Docker isolation, network capture, and process termination.

The file also includes detection patterns and escalation thresholds for file modifications and process attempts.

## Architecture

```mermaid
flowchart TD
    A[main.py] --> B{Execution mode}
    B -->|default| C[utils/cli_dashboard.py]
    B -->|--demo| D[core/demo_runner.py]
    B -->|--api| M[utils/api_server.py]
    B -->|--containment-agent| N[core/containment_system.py]

    E[core/behavior_monitor.py] --> F[core/deception_engine.py]
    O[core/anomaly_detector.py] --> F
    F --> G[core/risk_engine.py]
    G --> H[utils/event_logger.py]
    H --> I[utils/telemetry.py]
    H --> P[SIEM: Elastic/Splunk]

    J[core/honeypot_files.py] --> H
    K[core/containment_system.py] --> Q[Containment queue]
    N --> Q
    N --> H
    L[core/cowrie_bridge.py] --> H
```

## Demo flow

```mermaid
sequenceDiagram
    participant U as User
    participant M as main.py
    participant D as core/demo_runner.py
    participant R as risk_engine
    participant T as telemetry
    participant L as event_logger

    U->>M: python main.py --demo --iterations 8 --metrics-port 8000
    M->>D: run_demo()
    loop each scenario
        D->>R: classify_risk(score)
        D->>T: record_demo_attack() / record_risk_assessment()
        D->>L: log_event()
    end
    D-->>U: simulated attack summary and detection counts
```

## Cowrie integration

```mermaid
flowchart LR
    A[Cowrie JSON log] --> B[core/cowrie_bridge.py]
    B --> C[parse_cowrie_event()]
    C --> D[emit_cowrie_event()]
    D --> E[utils/event_logger.py]
    E --> F[JSONL log + telemetry]
```

The bridge extracts fields such as `event_id`, `src_ip`, `username`, `password`, and `command`, then records them as structured GGS events. If a webhook URL is provided, the event can also be forwarded externally.

## Risk scoring

Risk classification is currently based on three inputs:

- Matching active processes against process rules loaded from `config.yaml`.
- User tags accumulated by `core/behavior_monitor.py`.
- Optional anomaly score boost from `core/anomaly_detector.py`.

`core/risk_engine.py` reduces the resulting score to four levels:

- `observed`
- `suspicious`
- `detected`
- `full_monitoring`

```mermaid
flowchart TD
    A[Active processes] --> B[Rule matches]
    C[User tags] --> D[Tag score]
    K[Process count baseline] --> L[Anomaly boost]
    B --> E[Total score]
    D --> E
    L --> E
    E --> F{Threshold}
    F -->|>= full_monitoring| G[full_monitoring]
    F -->|>= detected| H[detected]
    F -->|>= suspicious| I[suspicious]
    F -->|< suspicious| J[observed]
```

## Installation

### Local

```bash
git clone https://github.com/jurgen-dev/GGS.git
cd GGS
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

On Linux or macOS, activate the environment with `source venv/bin/activate`.

### Docker

```bash
docker compose up --build
```

This starts the demo, Cowrie, the Cowrie bridge, and Prometheus according to [docker-compose.yml](docker-compose.yml).

## Usage

### CLI dashboard

```bash
python main.py
```

### Protected API (OAuth2 bearer)

```bash
python main.py --api --api-host 0.0.0.0 --api-port 8080
```

Then request a token:

```bash
curl -X POST http://localhost:8080/token -H "Content-Type: application/x-www-form-urlencoded" -d "username=guardian_api&password=change_me"
```

Use the bearer token against `/v1/health`, `/v1/risk`, and `/v1/alerts`.

### Web dashboard (Streamlit)

```bash
streamlit run web/dashboard_streamlit.py
```

The dashboard authenticates against `/token` and then auto-refreshes data from `/v1/alerts` and `/v1/risk`.
Use the sidebar to configure API base URL, refresh interval, and alert limit.

### Privileged containment agent

```bash
python main.py --containment-agent
```

Recommended deployment model:

- Run dashboard/API and analysis components with restricted permissions.
- Run only the containment agent with elevated privileges.
- Keep `containment.direct_execute: false` in production.

### Demo with metrics

```bash
python main.py --demo --iterations 8 --metrics-port 8000
```

### Tests

```bash
python run_tests.py
```

The test runner clears `test_system_events.log`, regenerates `test_decoys/`, and runs `pytest tests/`.

## Validation

The current test suite verifies that:

- `run_demo(iterations=4)` reports 3 detections out of 4 simulated scenarios.
- `log_event()` writes structured JSON entries.
- API authentication and protected endpoint access flow.
- Anomaly detector baseline and spike detection behavior.
- `parse_cowrie_event()` and `emit_cowrie_event()` handle Cowrie payloads correctly.
- `load_rules()` reads configuration from YAML.

That gives the demo a reproducible detection rate of 75% in the covered test scenario.

## Project structure

```text
GGS/
├── core/
│   ├── behavior_monitor.py
│   ├── containment_system.py
│   ├── cowrie_bridge.py
│   ├── deception_engine.py
│   ├── demo_runner.py
│   ├── honeypot_files.py
│   └── risk_engine.py
├── utils/
│   ├── cli_dashboard.py
│   ├── config_manager.py
│   ├── event_logger.py
│   └── telemetry.py
├── configs/
│   └── config_levels.yaml
├── tests/
│   ├── test_config.yaml
│   └── ...
├── web/
│   └── dashboard_streamlit.py
├── config.yaml
├── docker-compose.yml
├── main.py
├── prometheus.yml
├── readme.md
└── run_tests.py
```

## Notes

- The project is Linux-first: several modules depend on `/proc`, `psutil`, Docker, and optional network capture.
- `pyshark` is optional at runtime, but network capture usually also requires `tshark` on the host.
- `prometheus_client` is used for the local demo and dashboard metrics.
- SIEM forwarding is non-blocking by design, so a remote outage does not stop local detection.

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3).
