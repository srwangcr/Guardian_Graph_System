from core.demo_runner import run_demo


def test_run_demo_returns_deterministic_summary():
    result = run_demo(iterations=4, metrics_port=0)

    assert result.simulated_attacks == 4
    assert result.detected_attacks == 3
    assert any(key.endswith(":demo") for key in result.risk_summary)