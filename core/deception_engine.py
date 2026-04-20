from __future__ import annotations

import os
from collections import defaultdict

import psutil
from psutil import NoSuchProcess, AccessDenied, ZombieProcess

from core.anomaly_detector import UserProcessAnomalyDetector
from core.behavior_monitor import tagged_users
from core.risk_engine import assess_process, classify_risk, humanize_risk_level, score_tags
from utils.config_manager import load_rules
from utils.event_logger import log_event
from utils.telemetry import record_risk_assessment


config = load_rules(os.getenv("GGS_CONFIG_PATH", "tests/test_config.yaml"))
rules = config.get("rules", [])
risk_levels = config.get("risk_levels", {
    "suspicious": 2,
    "detected": 5,
    "full_monitoring": 8,
})

anomaly_config = config.get("anomaly_detection", {})
anomaly_detector = UserProcessAnomalyDetector(
    history_size=int(anomaly_config.get("history_size", 20)),
    z_threshold=float(anomaly_config.get("z_threshold", 2.5)),
    max_boost=int(anomaly_config.get("max_boost", 4)),
)

def user_count():
    user_risk_actions = defaultdict(int)
    user_risk_level = {}
    processes_by_user = defaultdict(int)

    for proc in psutil.process_iter(['pid', 'name', 'username']):
        try:
            process_name = proc.info['name']
            user = proc.info['username']
            cmdline = proc.cmdline() if hasattr(proc, "cmdline") else []

            if user:
                processes_by_user[user] += 1

            evidence = assess_process(process_name, cmdline, rules)
            if evidence is not None and user:
                user_risk_actions[user] += evidence.score
                log_event(
                    f"Proceso {process_name} coincide con {', '.join(evidence.matched_rules)}",
                    event_type="process_match",
                    process_name=process_name,
                    username=user,
                    score=evidence.score,
                )
        except (NoSuchProcess, AccessDenied, ZombieProcess):
            continue

    if anomaly_config.get("enabled", False):
        anomalies = anomaly_detector.evaluate(dict(processes_by_user))
        for user, assessment in anomalies.items():
            if not assessment.is_anomalous:
                continue
            user_risk_actions[user] += assessment.score_boost
            log_event(
                f"Anomalia detectada para {user}: z={assessment.z_score:.2f}, boost={assessment.score_boost}",
                event_type="anomaly_detection",
                username=user,
                z_score=round(assessment.z_score, 3),
                baseline_mean=round(assessment.baseline_mean, 3),
                baseline_std=round(assessment.baseline_std, 3),
                process_count=assessment.process_count,
                score_boost=assessment.score_boost,
            )

    for user, tags in tagged_users.items():
        count = score_tags(tags)
        total_score = user_risk_actions[user] + count
        risk_level = classify_risk(total_score, risk_levels)
        user_risk_level[user] = humanize_risk_level(risk_level)
        user_risk_actions[user] += count
        record_risk_assessment(risk_level, source="deception_engine")
        log_event(
            f"User {user} assigned to {user_risk_level[user]} with score {total_score}.",
            event_type="risk_assessment",
            username=user,
            score=total_score,
            tags=list(tags),
        )

    return user_risk_level, user_risk_actions
