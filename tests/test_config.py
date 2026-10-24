import json

import pytest
import yaml

from metropt3.config import ConfigError, load_config, validate_config


def test_base_config_matches_benchmark_defaults(config_values, write_config):
    config = load_config(write_config(config_values))
    values = config.as_dict()
    assert values["features"]["window_minutes"] == 5
    assert values["features"]["score_stride_seconds"] == 60
    assert values["quality"]["common_warmup_seconds"] == 930
    assert values["dataset"]["timezone"] is None
    assert values["reproducibility"]["seed"] == 42
    assert values["alerts"]["merge_gap_seconds"] == 300
    assert json.loads(config.canonical_json) == values


@pytest.mark.parametrize(
    ("section", "name", "value"),
    [
        ("features", "window_minutes", 0),
        ("features", "window_minutes", True),
        ("features", "score_stride_seconds", -1),
        ("features", "candidate_windows", []),
        ("features", "candidate_windows", [1, 5, 5]),
        ("features", "candidate_windows", [1, "5", 15]),
        ("features", "closed", "left"),
        ("features", "std_ddof", False),
        ("quality", "min_observed_fraction", 0),
        ("quality", "min_observed_fraction", 1.1),
        ("quality", "gap_multiplier", float("nan")),
        ("quality", "gap_multiplier", float("inf")),
        ("quality", "max_ffill_age_seconds", -1),
        ("quality", "common_warmup_seconds", 929),
        ("ecod", "batch_size", 0),
        ("ecod", "batch_size", 1.5),
        ("selection", "quantiles", [0]),
        ("selection", "quantiles", [1]),
        ("selection", "quantiles", [float("nan")]),
        ("selection", "quantiles", [0.99, 0.99]),
        ("selection", "alarm_operator", "greater_or_equal"),
        ("selection", "outside_episode_budget_per_day", -1),
        ("alerts", "break_on_invalid", "true"),
        ("reproducibility", "seed", -1),
        ("reproducibility", "n_jobs_benchmark", True),
        ("paths", "raw", ""),
        ("dataset", "timezone", "Asia/Saigon"),
        ("split", "train_end_exclusive", "not-a-date"),
        ("split", "train_end_exclusive", "2020-03-01T00:00:00+00:00"),
    ],
)
def test_invalid_field_reports_its_name(config_values, write_config, section, name, value):
    config_values[section][name] = value
    with pytest.raises(ConfigError, match=rf"{section}\.{name}"):
        load_config(write_config(config_values))


@pytest.mark.parametrize("end", ["2020-03-01 00:00:00", "2020-02-01 00:00:00"])
def test_validation_must_follow_train(config_values, write_config, end):
    config_values["split"]["validation_end_exclusive"] = end
    with pytest.raises(ConfigError, match="split.validation_end_exclusive"):
        load_config(write_config(config_values))


def test_warmup_covers_largest_candidate_and_fill(config_values, write_config):
    config_values["features"]["candidate_windows"].append(30)
    with pytest.raises(ConfigError, match="quality.common_warmup_seconds: must be >= 1830"):
        load_config(write_config(config_values))


def test_selected_window_must_be_registered(config_values, write_config):
    config_values["features"]["window_minutes"] = 2
    with pytest.raises(ConfigError, match="features.window_minutes"):
        load_config(write_config(config_values))


def test_missing_field_and_typo_are_not_silently_defaulted(config_values, write_config):
    del config_values["ecod"]["batch_size"]
    with pytest.raises(ConfigError, match="ecod.batch_size: required"):
        load_config(write_config(config_values))
    config_values["ecod"]["batchsize"] = 4096
    with pytest.raises(ConfigError, match="ecod.batchsize: unknown"):
        load_config(write_config(config_values))


@pytest.mark.parametrize("values", [None, [], {}, {"schema_version": 2}])
def test_malformed_or_unsupported_document(values):
    with pytest.raises(ConfigError):
        validate_config(values)


def test_section_must_be_a_mapping(config_values, write_config):
    config_values["features"] = []
    with pytest.raises(ConfigError, match="features.*expected a mapping"):
        load_config(write_config(config_values))


def test_hash_ignores_mapping_order_and_yaml_formatting(config_values, write_config):
    first = load_config(write_config(config_values, "first.yaml"))
    reordered = {
        key: dict(reversed(list(value.items()))) if isinstance(value, dict) else value
        for key, value in reversed(list(config_values.items()))
    }
    second_path = write_config(reordered, "second.yaml")
    with second_path.open("a", encoding="utf-8") as stream:
        stream.write("\n# Formatting is not an experiment setting.\n")
    second = load_config(second_path)
    assert first.config_hash == second.config_hash
    assert first.canonical_json == second.canonical_json


def test_equivalent_numeric_and_timestamp_values_have_same_hash(config_values, write_config):
    first = load_config(write_config(config_values, "first.yaml"))
    config_values["quality"]["gap_multiplier"] = 3.0
    config_values["split"]["train_end_exclusive"] = "2020-03-01T00:00:00"
    second = load_config(write_config(config_values, "second.yaml"))
    assert first.config_hash == second.config_hash


def test_semantic_change_changes_hash(config_values, write_config):
    first = load_config(write_config(config_values, "first.yaml"))
    config_values["reproducibility"]["seed"] = 7
    second = load_config(write_config(config_values, "second.yaml"))
    assert first.config_hash != second.config_hash


def test_exposed_values_cannot_mutate_config(config_values, write_config):
    config = load_config(write_config(config_values))
    before = config.config_hash
    exposed = config.as_dict()
    exposed["reproducibility"]["seed"] = 7
    exposed["features"]["candidate_windows"].append(30)
    assert config.as_dict()["reproducibility"]["seed"] == 42
    assert config.config_hash == before


def test_paths_resolve_from_config_location_not_cwd(config_values, write_config, tmp_path, monkeypatch):
    source = write_config(config_values)
    other_cwd = tmp_path / "unrelated"
    other_cwd.mkdir()
    monkeypatch.chdir(other_cwd)
    config = load_config(source)
    assert config.project_root == tmp_path
    assert config.resolve_path("raw") == tmp_path / "data" / "raw"
    assert config.resolve_path("artifacts") == tmp_path / "artifacts"
    assert not (tmp_path / "data").exists()
    assert not (tmp_path / "artifacts").exists()


def test_relocating_project_does_not_change_hash(config_values, write_config, tmp_path):
    first = load_config(write_config(config_values))
    other_source = tmp_path / "relocated" / "configs" / "base.yaml"
    other_source.parent.mkdir(parents=True)
    other_source.write_text(yaml.safe_dump(config_values), encoding="utf-8")
    second = load_config(other_source)
    assert first.project_root != second.project_root
    assert first.config_hash == second.config_hash


@pytest.mark.parametrize(
    "contents",
    [
        "schema_version: 1\nschema_version: 2\n",
        "features:\n  window_minutes: 1\n  window_minutes: 5\n",
        "features: [broken\n",
        "!!python/object/apply:builtins.str [not-allowed]\n",
    ],
)
def test_yaml_errors_are_config_errors(tmp_path, contents):
    path = tmp_path / "invalid.yaml"
    path.write_text(contents, encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(path)


def test_missing_file_has_readable_error(tmp_path):
    with pytest.raises(ConfigError, match="missing.yaml"):
        load_config(tmp_path / "missing.yaml")
