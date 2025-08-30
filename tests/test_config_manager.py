from utils.config_manager import load_rules

def test_load_rules_valid():
    config = load_rules("tests/test_config.yaml")
    assert "rules" in config
    assert isinstance(config["rules"], list)
    assert config["honeypot_path"] == "./test_decoys/"
