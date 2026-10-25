import json
import subprocess
import sys

import pytest


def run_cli(*args, cwd):
    return subprocess.run(
        [sys.executable, "-m", "metropt3.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def test_help_works_without_config_or_data(tmp_path):
    result = run_cli("--help", cwd=tmp_path)
    assert result.returncode == 0
    assert "check-config" in result.stdout
    assert not list(tmp_path.iterdir())


def test_check_config_reports_hash_and_paths(config_values, write_config, tmp_path):
    source = write_config(config_values)
    result = run_cli("check-config", "--config", str(source), cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["valid"] is True
    assert len(output["config_hash"]) == 64
    assert output["paths"]["raw"] == str(tmp_path / "data" / "raw")
    assert not (tmp_path / "artifacts").exists()


def test_invalid_config_exits_before_success(config_values, write_config, tmp_path):
    config_values["features"]["window_minutes"] = 0
    result = run_cli("check-config", "--config", str(write_config(config_values)), cwd=tmp_path)
    assert result.returncode == 2
    assert "features.window_minutes" in result.stderr
    assert not result.stdout
    assert not (tmp_path / "artifacts").exists()


@pytest.mark.parametrize("field", ["train_end_exclusive", "validation_end_exclusive"])
@pytest.mark.parametrize("value", ["2020-02-30 00:00:00", "2020-03-01 25:00:00"])
@pytest.mark.parametrize("quoted", [False, True], ids=["unquoted", "quoted"])
def test_invalid_yaml_timestamp_reports_field(
    write_timestamp_config, tmp_path, field, value, quoted
):
    source = write_timestamp_config(field, value, quoted=quoted)
    result = run_cli("check-config", "--config", str(source), cwd=tmp_path)
    assert result.returncode == 2
    assert f"split.{field}" in result.stderr
    assert "Traceback" not in result.stderr
    assert not result.stdout
    assert not (tmp_path / "artifacts").exists()


@pytest.mark.parametrize("field", ["seed", "stability_seeds"])
@pytest.mark.parametrize("seed", [-1, 4294967296])
def test_invalid_seed_reports_field(config_values, write_config, tmp_path, field, seed):
    config_values["reproducibility"][field] = seed if field == "seed" else [42, seed]
    result = run_cli("check-config", "--config", str(write_config(config_values)), cwd=tmp_path)
    assert result.returncode == 2
    assert f"reproducibility.{field}" in result.stderr
    if field == "stability_seeds":
        assert "item 1" in result.stderr
    assert "Traceback" not in result.stderr
    assert not result.stdout
    assert not (tmp_path / "artifacts").exists()


@pytest.mark.parametrize("command", ["features", "train", "validate", "freeze", "test", "report"])
def test_unimplemented_stages_fail_instead_of_claiming_success(command, tmp_path):
    result = run_cli(command, cwd=tmp_path)
    assert result.returncode == 2
    assert "invalid choice" in result.stderr
    assert not result.stdout


def test_package_entry_point_and_version(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "metropt3", "--version"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.startswith("metropt3 ")
