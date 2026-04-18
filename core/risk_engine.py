from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


DEFAULT_RISK_LEVELS = {
    "suspicious": 2,
    "detected": 5,
    "full_monitoring": 8,
}


@dataclass(frozen=True)
class RiskEvidence:
    process_name: str
    command_line: str
    matched_rules: tuple[str, ...]
    score: int


def score_tags(tags: Iterable[str]) -> int:
    total = 0
    for tag in tags:
        total += 1
        if "honeypot" in tag.lower() or "scanner" in tag.lower():
            total += 1
    return total


def assess_process(process_name: str, cmdline: Iterable[str], rules: list[dict]) -> RiskEvidence | None:
    command_line = " ".join(cmdline or [])
    matched_rules: list[str] = []
    score = 0

    for rule in rules:
        expected_name = rule.get("process_name")
        required_tokens = rule.get("cmd_contains", []) or []
        if expected_name and expected_name != process_name:
            continue
        if required_tokens and not any(token in command_line for token in required_tokens):
            continue
        matched_rules.append(rule.get("name", process_name))
        score += max(1, len(required_tokens) or 1)

    if not matched_rules:
        return None

    return RiskEvidence(
        process_name=process_name,
        command_line=command_line,
        matched_rules=tuple(matched_rules),
        score=score,
    )


def classify_risk(score: int, thresholds: dict[str, int] | None = None) -> str:
    thresholds = thresholds or DEFAULT_RISK_LEVELS
    if score >= thresholds.get("full_monitoring", 8):
        return "full_monitoring"
    if score >= thresholds.get("detected", 5):
        return "detected"
    if score >= thresholds.get("suspicious", 2):
        return "suspicious"
    return "observed"


def humanize_risk_level(level: str) -> str:
    return level.replace("_", " ").title()