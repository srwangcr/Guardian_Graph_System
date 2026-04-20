from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from statistics import mean, pstdev


@dataclass(frozen=True)
class AnomalyAssessment:
    user: str
    process_count: int
    baseline_mean: float
    baseline_std: float
    z_score: float
    score_boost: int
    is_anomalous: bool


class UserProcessAnomalyDetector:
    """
    Lightweight anomaly detector based on rolling process-count z-score.

    It complements rule-based detections without adding heavy ML dependencies.
    """

    def __init__(self, history_size: int = 20, z_threshold: float = 2.5, max_boost: int = 4) -> None:
        self.history_size = max(5, history_size)
        self.z_threshold = z_threshold
        self.max_boost = max(1, max_boost)
        self._history: dict[str, list[int]] = defaultdict(list)

    def evaluate(self, counts_by_user: dict[str, int]) -> dict[str, AnomalyAssessment]:
        assessments: dict[str, AnomalyAssessment] = {}

        for user, process_count in counts_by_user.items():
            history = self._history[user]
            baseline_mean = mean(history) if history else float(process_count)
            baseline_std = pstdev(history) if len(history) > 1 else 0.0

            if baseline_std <= 0.0:
                z_score = 0.0
            else:
                z_score = (process_count - baseline_mean) / baseline_std

            is_anomalous = z_score >= self.z_threshold and process_count > baseline_mean
            score_boost = 0
            if is_anomalous:
                normalized = min(self.max_boost, max(1, int(round(z_score))))
                score_boost = normalized

            assessments[user] = AnomalyAssessment(
                user=user,
                process_count=process_count,
                baseline_mean=baseline_mean,
                baseline_std=baseline_std,
                z_score=z_score,
                score_boost=score_boost,
                is_anomalous=is_anomalous,
            )

            history.append(process_count)
            if len(history) > self.history_size:
                del history[: len(history) - self.history_size]

        return assessments
