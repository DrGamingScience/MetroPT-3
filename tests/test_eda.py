"""PB06: held-out isolation, quality scope and deterministic daily sampling."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


spec = importlib.util.spec_from_file_location(
    "pb06_train_eda", Path(__file__).resolve().parents[1] / "scripts/pb06_train_eda.py")
eda = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eda)


@pytest.fixture
def observations():
    times = pd.to_datetime([
        "2020-02-01 00:00:00", "2020-02-01 00:00:10", "2020-02-01 00:00:20",
        "2020-02-02 00:00:00", "2020-02-02 00:00:10", "2020-02-29 23:59:59",
        "2020-03-01 00:00:00", "2020-05-01 00:00:00",
    ])
    frame = pd.DataFrame({"timestamp": times, "raw_row_id": range(8),
                          "split": ["train"] * 6 + ["validation", "test"],
                          "valid": [True] * 5 + [False, True, True],
                          "segment_id": [0, 0, 0, 1, 1, 2, 3, 4]})
    for column in eda.ANALOG_COLUMNS:
        frame[column] = [-.02, 0, 2, 4, 8, 1e10, 15, 20]
    for column in eda.DIGITAL_COLUMNS:
        frame[column] = [0., 1., 0., 1., 1., 0., 1., 0.]
    for column in eda.QUALITY_FLAGS:
        frame[column] = False
    frame.loc[5, "invalid_numeric"] = True
    return frame


def test_heldout_values_and_order_cannot_change_train_eda(observations, config_values):
    before = eda.analyze(observations, config_values, per_day=2)
    changed = observations.copy()
    heldout = changed.split.ne("train")
    changed.loc[heldout, list(eda.ANALOG_COLUMNS)] = np.inf
    changed.loc[heldout, list(eda.DIGITAL_COLUMNS)] = 999
    changed.loc[heldout, "valid"] = False
    changed = changed.sample(frac=1, random_state=7)
    after = eda.analyze(changed, config_values, per_day=2)
    for key, value in before.items():
        if isinstance(value, pd.DataFrame):
            pd.testing.assert_frame_equal(value, after[key])
        else:
            assert value == after[key]


def test_quality_daily_sample_and_undefined_constant_correlation(observations, config_values):
    observations["Oil_level"] = 1.
    result = eda.analyze(observations, config_values, per_day=2)
    assert result["train_rows_before_quality"] == 6
    assert result["quality_excluded"] == 1
    assert result["quality"]["invalid_numeric"] == 1
    assert result["stats"].loc["TP2", "min"] == -.02  # valid negatives survive
    assert result["stats"].loc["TP2", "max"] == 8  # invalid extreme excluded
    assert result["sampling"].sample_rows.tolist() == [2, 2]
    assert result["sample"].raw_row_id.is_unique
    assert result["daily"].loc["2020-02-29", "valid_rows"] == 0
    assert result["pearson"].Oil_level.isna().all()
    again = eda.analyze(observations, config_values, per_day=2)
    pd.testing.assert_frame_equal(result["sample"], again["sample"])


def test_stale_split_is_rejected(observations, config_values):
    observations.loc[6, "split"] = "train"  # exact boundary must be excluded
    with pytest.raises(ValueError, match="rerun audit"):
        eda.analyze(observations, config_values)
