from core.anomaly_detector import UserProcessAnomalyDetector


def test_anomaly_detector_flags_spike_after_baseline():
    detector = UserProcessAnomalyDetector(history_size=5, z_threshold=2.0, max_boost=4)

    detector.evaluate({"alice": 2})
    detector.evaluate({"alice": 2})
    detector.evaluate({"alice": 3})

    assessment = detector.evaluate({"alice": 15})["alice"]

    assert assessment.is_anomalous is True
    assert assessment.score_boost >= 1
