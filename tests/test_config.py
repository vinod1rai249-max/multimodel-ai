import pytest
import os
from core.config_loader import load_config, Config

def test_load_config():
    # Test loading the actual config.yaml
    config = load_config("config.yaml")
    assert isinstance(config, Config)
    assert len(config.routing.text_generation) > 0
    assert config.app_settings.theme == "dark"

def test_config_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("non_existent.yaml")
