# Changelog

All notable changes to this project will be documented in this file.

The format follows the spirit of [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Protected REST API mode with OAuth2 bearer flow in `utils/api_server.py` (`/token`, `/v1/health`, `/v1/risk`, `/v1/alerts`).
- New entrypoint flags in `main.py` for `--api`, `--api-host`, `--api-port`, and `--containment-agent`.
- Privilege-separated containment execution via queued actions and a dedicated `run_containment_agent()` in `core/containment_system.py`.
- Lightweight anomaly detection module `core/anomaly_detector.py` and integration into `core/deception_engine.py`.
- Optional SIEM forwarding support in `utils/event_logger.py` for Elasticsearch and Splunk HEC.
- Test coverage for API auth flow and anomaly detection behavior.

### Changed

- Rewrote the README in English.
- Aligned the documentation with current runtime modes, telemetry, API security flow, privilege separation model, anomaly detection, and SIEM integration.
- Added Mermaid diagrams for the architecture, demo flow, Cowrie bridge, and risk scoring path.
- Extended `config.yaml` and `tests/test_config.yaml` with `api`, `anomaly_detection`, `siem`, and enhanced `containment` settings.
- Updated dependencies in `requirements.txt` for API runtime and tests (`fastapi`, `uvicorn`, `python-multipart`, `httpx`).

### Notes

- Detection pipeline remains fail-safe: SIEM export failures do not block local logging or risk analysis.
