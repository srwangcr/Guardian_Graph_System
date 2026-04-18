from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from threading import Lock

try:
    from prometheus_client import Counter, Gauge, start_http_server
except ImportError:  # pragma: no cover - fallback for minimal environments
    Counter = Gauge = None

    def start_http_server(port):
        return None


@dataclass(frozen=True)
class TelemetrySnapshot:
    event_counts: dict[str, int]
    risk_counts: dict[str, int]
    demo_attack_counts: dict[str, int]


class _NoopMetric:
    def labels(self, *args, **kwargs):
        return self

    def inc(self, amount=1):
        return None

    def set(self, value):
        return None


_lock = Lock()
_metrics_server_started = False
_event_counts: dict[str, int] = defaultdict(int)
_risk_counts: dict[str, int] = defaultdict(int)
_demo_attack_counts: dict[str, int] = defaultdict(int)

if Counter is None:
    EVENT_COUNTER = _NoopMetric()
    RISK_COUNTER = _NoopMetric()
    DEMO_ATTACK_COUNTER = _NoopMetric()
    ACTIVE_THREATS = _NoopMetric()
else:
    EVENT_COUNTER = Counter(
        "ggs_events_total",
        "Total de eventos emitidos por Guardian Graph System",
        ["level", "event_type", "source"],
    )
    RISK_COUNTER = Counter(
        "ggs_risk_assessments_total",
        "Total de evaluaciones de riesgo",
        ["level", "source"],
    )
    DEMO_ATTACK_COUNTER = Counter(
        "ggs_demo_attacks_total",
        "Total de ataques simulados en modo demo",
        ["outcome"],
    )
    ACTIVE_THREATS = Gauge(
        "ggs_active_threats",
        "Cantidad actual de amenazas activas observadas por el demo",
    )


def ensure_metrics_server(port: int = 8000) -> None:
    global _metrics_server_started
    with _lock:
        if _metrics_server_started:
            return
        start_http_server(port)
        _metrics_server_started = True


def record_event(level: str, event_type: str, source: str = "guardian_graph") -> None:
    normalized_level = level.lower()
    normalized_event_type = event_type.lower()
    normalized_source = source.lower()
    _event_counts[f"{normalized_level}:{normalized_event_type}:{normalized_source}"] += 1
    EVENT_COUNTER.labels(normalized_level, normalized_event_type, normalized_source).inc()


def record_risk_assessment(level: str, source: str = "risk_engine") -> None:
    normalized_level = level.lower()
    normalized_source = source.lower()
    _risk_counts[f"{normalized_level}:{normalized_source}"] += 1
    RISK_COUNTER.labels(normalized_level, normalized_source).inc()


def record_demo_attack(outcome: str, active_threats: int | None = None) -> None:
    normalized_outcome = outcome.lower()
    _demo_attack_counts[normalized_outcome] += 1
    DEMO_ATTACK_COUNTER.labels(normalized_outcome).inc()
    if active_threats is not None:
        ACTIVE_THREATS.set(active_threats)


def snapshot() -> TelemetrySnapshot:
    return TelemetrySnapshot(
        event_counts=dict(_event_counts),
        risk_counts=dict(_risk_counts),
        demo_attack_counts=dict(_demo_attack_counts),
    )