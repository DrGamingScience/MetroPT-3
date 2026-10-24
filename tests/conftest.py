"""Fixtures use the real config contract without requiring the dataset."""

from pathlib import Path

import pytest
import yaml


BASE_CONFIG = Path(__file__).resolve().parents[1] / "configs" / "base.yaml"


@pytest.fixture
def config_values():
    return yaml.safe_load(BASE_CONFIG.read_text(encoding="utf-8"))


@pytest.fixture
def write_config(tmp_path):
    def write(values, name="base.yaml"):
        path = tmp_path / "configs" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(values, sort_keys=False), encoding="utf-8")
        return path

    return write
