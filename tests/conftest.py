"""Fixtures use the real config contract without requiring the dataset."""

import json
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


@pytest.fixture
def write_timestamp_config(config_values, write_config):
    """Control YAML quoting instead of letting safe_dump choose it for us."""
    def write(field, value, *, quoted):
        path = write_config(config_values)
        lines = path.read_text(encoding="utf-8").splitlines()
        prefix = f"  {field}:"
        rendered = json.dumps(value) if quoted else value
        for index, line in enumerate(lines):
            if line.startswith(prefix):
                lines[index] = f"{prefix} {rendered}"
                break
        else:
            raise AssertionError(f"Timestamp field not found: {field}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    return write
