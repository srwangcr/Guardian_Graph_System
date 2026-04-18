from __future__ import annotations

from dataclasses import dataclass

from core.risk_engine import classify_risk, humanize_risk_level
from utils.event_logger import log_event
from utils.telemetry import ensure_metrics_server, record_demo_attack, record_risk_assessment, snapshot


@dataclass(frozen=True)
class DemoResult:
    simulated_attacks: int
    detected_attacks: int
    risk_summary: dict[str, int]


SCENARIOS = (
    {"name": "nmap_scan", "score": 2, "detected": True},
    {"name": "ssh_bruteforce", "score": 3, "detected": True},
    {"name": "file_encryption", "score": 5, "detected": True},
    {"name": "benign_login", "score": 0, "detected": False},
)


def run_demo(iterations: int = 8, metrics_port: int = 8000) -> DemoResult:
    ensure_metrics_server(metrics_port)
    detected_attacks = 0

    for index in range(iterations):
        scenario = SCENARIOS[index % len(SCENARIOS)]
        risk_level = classify_risk(scenario["score"])
        pretty_level = humanize_risk_level(risk_level)
        if scenario["detected"]:
            detected_attacks += 1
            record_demo_attack("detected", active_threats=detected_attacks)
        else:
            record_demo_attack("benign", active_threats=detected_attacks)

        record_risk_assessment(risk_level, source="demo")
        log_event(
            f"Demo scenario {scenario['name']} classified as {pretty_level}",
            event_type="demo_attack",
            scenario=scenario["name"],
            score=scenario["score"],
            detected=scenario["detected"],
        )

    telemetry = snapshot()
    summary = DemoResult(
        simulated_attacks=iterations,
        detected_attacks=detected_attacks,
        risk_summary={key: value for key, value in telemetry.risk_counts.items()},
    )
    print(
        "Demo terminado: "
        f"{summary.detected_attacks}/{summary.simulated_attacks} ataques detectados."
    )
    return summary