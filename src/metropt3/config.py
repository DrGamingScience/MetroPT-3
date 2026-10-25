"""Load and validate the versioned experiment configuration without data access."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Callable

import yaml


CONFIG_SCHEMA_VERSION = 1
MAX_RANDOM_SEED = 2**32 - 1
Validator = Callable[[Any], Any]


class ConfigError(ValueError):
    """An invalid configuration, including the offending field when available."""


class _UniqueKeySafeLoader(yaml.SafeLoader):
    """Reject duplicate keys and leave timestamps for field-aware validation."""


def _unique_mapping(loader: _UniqueKeySafeLoader, node: Any) -> dict[str, Any]:
    loader.flatten_mapping(node)
    result: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str):
            raise yaml.constructor.ConstructorError(
                None, None, "configuration keys must be strings", key_node.start_mark
            )
        if key in result:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate key: {key}", key_node.start_mark
            )
        result[key] = loader.construct_object(value_node)
    return result


_UniqueKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping
)
# PyYAML's timestamp constructor can raise ValueError before a field is known.
# Preserve its scalar text so _timestamp reports errors through _fields instead.
_UniqueKeySafeLoader.add_constructor(
    "tag:yaml.org,2002:timestamp", _UniqueKeySafeLoader.construct_scalar
)


def _integer(value: Any, *, minimum: int) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"expected an integer >= {minimum}, got {value!r}")
    return value


def _positive_int(value: Any) -> int:
    return _integer(value, minimum=1)


def _nonnegative_int(value: Any) -> int:
    return _integer(value, minimum=0)


def _seed(value: Any) -> int:
    """Use the integer range supported by scikit-learn's RandomState seeds."""
    value = _nonnegative_int(value)
    if value > MAX_RANDOM_SEED:
        raise ValueError(f"must be <= {MAX_RANDOM_SEED}")
    return value


def _number(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"expected a finite number, got {value!r}")
    try:
        normalized = float(value)
    except OverflowError as exc:
        raise ValueError("number is too large") from exc
    if not math.isfinite(normalized):
        raise ValueError(f"expected a finite number, got {value!r}")
    return normalized


def _positive_number(value: Any) -> float:
    value = _number(value)
    if value <= 0:
        raise ValueError("must be greater than 0")
    return value


def _nonnegative_number(value: Any) -> float:
    value = _number(value)
    if value < 0:
        raise ValueError("must be at least 0")
    return value


def _fraction(value: Any) -> float:
    value = _number(value)
    if not 0 < value <= 1:
        raise ValueError("must be in (0, 1]")
    return value


def _quantile(value: Any) -> float:
    value = _number(value)
    if not 0 < value < 1:
        raise ValueError("must be in (0, 1)")
    return value


def _text(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("expected a non-empty string")
    return value


def _fixed(expected: Any) -> Validator:
    def parse(value: Any) -> Any:
        if type(value) is not type(expected) or value != expected:
            raise ValueError(f"must be {expected!r} in schema v{CONFIG_SCHEMA_VERSION}")
        return value

    return parse


def _choice(*choices: str) -> Validator:
    def parse(value: Any) -> str:
        value = _text(value)
        if value not in choices:
            raise ValueError(f"must be one of {choices!r}")
        return value

    return parse


def _list_of(parse_item: Validator) -> Validator:
    def parse(value: Any) -> list[Any]:
        if not isinstance(value, list) or not value:
            raise ValueError("expected a non-empty list")
        parsed = []
        for index, item in enumerate(value):
            try:
                parsed.append(parse_item(item))
            except ValueError as exc:
                raise ValueError(f"item {index}: {exc}") from exc
        if len(set(parsed)) != len(parsed):
            raise ValueError("list items must be unique")
        return parsed

    return parse


def _timestamp(value: Any) -> str:
    try:
        if isinstance(value, datetime):
            parsed = value
        elif isinstance(value, date):
            parsed = datetime.combine(value, time())
        elif isinstance(value, str):
            parsed = datetime.fromisoformat(value)
        else:
            raise ValueError("expected an ISO timestamp")
    except ValueError as exc:
        raise ValueError(f"invalid ISO timestamp {value!r}: {exc}") from exc
    if parsed.tzinfo is not None:
        raise ValueError("must use the dataset clock without a timezone offset")
    return parsed.isoformat(sep=" ")


_SECTIONS: dict[str, dict[str, Validator]] = {
    "paths": {
        "project_root": _text,
        "raw": _text,
        "interim": _text,
        "processed": _text,
        "artifacts": _text,
        "reports": _text,
    },
    "dataset": {
        "uci_id": _fixed(791),
        "time_column": _fixed("timestamp"),
        "timezone": _fixed(None),
    },
    "split": {
        "train_end_exclusive": _timestamp,
        "validation_end_exclusive": _timestamp,
    },
    "features": {
        "set": _choice("F35", "F51", "F55", "F7"),
        "window_minutes": _positive_int,
        "candidate_windows": _list_of(_positive_int),
        "score_stride_seconds": _positive_int,
        "closed": _fixed("right"),
        "std_ddof": _fixed(0),
    },
    "quality": {
        "min_observed_fraction": _fraction,
        "gap_multiplier": _positive_number,
        "max_ffill_age_seconds": _nonnegative_int,
        "edge_tolerance_multiplier": _positive_number,
        "common_warmup_seconds": _nonnegative_int,
    },
    "ecod": {
        "implementation": _fixed("paper_frozen_v1"),
        "aggregation": _fixed("max_of_three_sums"),
        "tie_skewness": _fixed("right"),
        "probability_floor": _fixed("one_over_n_plus_one"),
        "batch_size": _positive_int,
    },
    "selection": {
        "primary_metric": _fixed("average_precision"),
        "quantiles": _list_of(_quantile),
        "quantile_method": _fixed("higher"),
        "alarm_operator": _fixed("greater_than"),
        "outside_episode_budget_per_day": _nonnegative_number,
    },
    "alerts": {
        "merge_gap_seconds": _positive_int,
        "break_on_invalid": _fixed(True),
    },
    "reproducibility": {
        "seed": _seed,
        "stability_seeds": _list_of(_seed),
        "n_jobs_benchmark": _fixed(1),
    },
}


def _fields(data: Any, schema: dict[str, Validator], prefix: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ConfigError(f"{prefix or 'config'}: expected a mapping")
    for name in data:
        if name not in schema:
            raise ConfigError(f"{prefix}{name}: unknown field")
    result = {}
    for name, parse in schema.items():
        key = f"{prefix}{name}"
        if name not in data:
            raise ConfigError(f"{key}: required field is missing")
        try:
            result[name] = parse(data[name])
        except ConfigError:
            raise
        except ValueError as exc:
            raise ConfigError(f"{key}: {exc}") from exc
    return result


def validate_config(data: Any) -> dict[str, Any]:
    """Validate and normalize all fields, without reading raw data or making dirs."""
    schema = {"schema_version": _fixed(CONFIG_SCHEMA_VERSION)}
    for name, fields in _SECTIONS.items():
        schema[name] = lambda value, fields=fields, name=name: _fields(
            value, fields, f"{name}."
        )
    result = _fields(data, schema, "")
    split = result["split"]
    if datetime.fromisoformat(split["train_end_exclusive"]) >= datetime.fromisoformat(
        split["validation_end_exclusive"]
    ):
        raise ConfigError("split.validation_end_exclusive: must be after train_end_exclusive")

    features, quality = result["features"], result["quality"]
    if features["score_stride_seconds"] != 60:
        raise ConfigError(
            "features.score_stride_seconds: PB05 requires exactly 60 seconds"
        )
    if features["window_minutes"] not in features["candidate_windows"]:
        raise ConfigError("features.window_minutes: must appear in candidate_windows")
    minimum_warmup = max(features["candidate_windows"]) * 60 + quality["max_ffill_age_seconds"]
    if quality["common_warmup_seconds"] < minimum_warmup:
        raise ConfigError(
            f"quality.common_warmup_seconds: must be >= {minimum_warmup} "
            "(largest candidate window plus maximum forward-fill age)"
        )
    return result


@dataclass(frozen=True)
class ProjectConfig:
    """A validated immutable snapshot; callers receive copies of its values."""

    source: Path
    project_root: Path
    canonical_json: str = field(repr=False)

    @property
    def config_hash(self) -> str:
        return hashlib.sha256(self.canonical_json.encode("utf-8")).hexdigest()

    def as_dict(self) -> dict[str, Any]:
        return json.loads(self.canonical_json)

    def resolve_path(self, name: str) -> Path:
        paths = self.as_dict()["paths"]
        if name == "project_root":
            return self.project_root
        path = Path(paths[name]).expanduser()
        return (self.project_root / path).resolve()


def load_config(path: str | Path) -> ProjectConfig:
    """Read safe YAML, normalize its values, and resolve paths from its location."""
    source = Path(path).expanduser().resolve()
    try:
        with source.open(encoding="utf-8-sig") as stream:
            data = yaml.load(stream, Loader=_UniqueKeySafeLoader)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ConfigError(f"{source}: {exc}") from exc
    normalized = validate_config(data)
    canonical_json = json.dumps(
        normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    root = Path(normalized["paths"]["project_root"]).expanduser()
    return ProjectConfig(source, (source.parent / root).resolve(), canonical_json)
