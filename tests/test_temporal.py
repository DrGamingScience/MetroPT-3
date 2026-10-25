"""PB05 acceptance: boundaries, common warm-up, full lineage and coverage."""

import json

import numpy as np
import pandas as pd
import pytest

from metropt3.config import load_config
from metropt3.events import reported_events
from metropt3.temporal import (
    TemporalError, apply_window_masks, build_time_grid, split_timestamps, summarize_time_grid,
)


@pytest.fixture
def config(config_values, write_config):
    return load_config(write_config(config_values))


def observations(config, *ranges):
    times = pd.DatetimeIndex(sorted(set(t for start, end in ranges
                                       for t in pd.date_range(start, end, freq="10s"))))
    rows = pd.DataFrame({"timestamp": times, "raw_row_id": np.arange(len(times))})
    rows["segment_id"] = (rows.timestamp.diff().dt.total_seconds() > 30).cumsum()
    rows["split"] = split_timestamps(rows.timestamp, config)
    return rows


@pytest.fixture
def rows(config):
    return observations(config, ("2020-02-01 00:00:00", "2020-02-01 00:40:00"))


def grid_for(rows, config):
    return build_time_grid(rows, config, gap_break_seconds=30)


def links(rows, end, *times):
    ids = rows.set_index("timestamp").raw_row_id
    return pd.DataFrame({"window_end": [pd.Timestamp(end)] * len(times),
                         "raw_row_id": pd.Series([ids.loc[pd.Timestamp(t)] for t in times], dtype="int64")})


def masks(grid, rows, config, sources, *, events=None, fills=None, quality=None, quality_reason=None):
    return apply_window_masks(
        grid, rows, reported_events() if events is None else events, config,
        sources=sources, fill_origins=fills,
        quality_valid=pd.Series(True, index=grid.index) if quality is None else quality,
        quality_reason=quality_reason,
    )


def at(grid, time):
    return grid.set_index("window_end").loc[pd.Timestamp(time)]


def test_exact_split_boundaries_are_exclusive(config):
    assert split_timestamps([
        "2020-02-29 23:59:59", "2020-03-01 00:00:00",
        "2020-04-30 23:59:59", "2020-05-01 00:00:00",
    ], config).tolist() == ["train", "validation", "validation", "test"]


@pytest.mark.parametrize("boundary", ["2020-03-01", "2020-05-01"])
def test_split_resets_warmup_even_without_segment_break(config, boundary):
    boundary = pd.Timestamp(boundary)
    rows = observations(config, (boundary - pd.Timedelta(minutes=20), boundary + pd.Timedelta(minutes=20)))
    grid = grid_for(rows, config)
    assert rows.segment_id.nunique() == 1
    assert at(grid, boundary - pd.Timedelta(minutes=1)).temporal_valid
    assert at(grid, boundary).warmup
    assert at(grid, boundary + pd.Timedelta(minutes=15)).temporal_reason == "warmup"
    assert at(grid, boundary + pd.Timedelta(minutes=16)).temporal_valid
    assert at(grid, boundary).block_start == boundary


def test_warmup_930_seconds_rounds_up_to_minute_and_restarts_after_gap(config):
    rows = observations(config, ("2020-02-01 00:00:00", "2020-02-01 00:20:00"),
                        ("2020-02-01 01:00:10", "2020-02-01 01:20:10"))
    grid = grid_for(rows, config)
    assert len(grid) == 81  # every minute, including the entire gap
    assert at(grid, "2020-02-01 00:15:00").warmup
    assert at(grid, "2020-02-01 00:16:00").temporal_valid
    assert at(grid, "2020-02-01 00:21:00").temporal_reason == "gap"
    assert pd.isna(at(grid, "2020-02-01 00:21:00").segment_id)
    assert at(grid, "2020-02-01 01:00:00").temporal_reason == "gap"  # cannot read 01:00:10
    assert at(grid, "2020-02-01 01:15:00").warmup
    assert at(grid, "2020-02-01 01:16:00").temporal_valid


def test_all_window_lengths_have_identical_temporal_mask(config_values, write_config):
    grids = []
    for window in [1, 5, 15]:
        config_values["features"]["window_minutes"] = window
        config = load_config(write_config(config_values))
        rows = observations(config, ("2020-02-01 00:00:09", "2020-02-01 00:25:09"))
        grids.append(grid_for(rows, config))
    for grid in grids[1:]:
        pd.testing.assert_series_equal(grid.temporal_valid, grids[0].temporal_valid)
    assert grids[0].window_end.iloc[0] == pd.Timestamp("2020-02-01 00:01:00")
    assert grids[0].window_end.iloc[-1] == pd.Timestamp("2020-02-01 00:25:00")


def test_future_observations_do_not_change_past_calendar(config):
    first = observations(config, ("2020-02-01 00:00:00", "2020-02-01 00:25:00"))
    second = observations(config, ("2020-02-01 00:00:00", "2020-02-01 00:20:00"),
                          ("2020-02-01 00:24:00", "2020-02-01 00:40:00"))
    a, b = grid_for(first, config), grid_for(second, config)
    pd.testing.assert_frame_equal(a[a.window_end <= "2020-02-01 00:20:00"],
                                  b[b.window_end <= "2020-02-01 00:20:00"])


def test_lineage_rejects_cross_split_raw_and_fill_and_keeps_train_sources_disjoint(config):
    rows = observations(config, ("2020-02-29 23:30:00", "2020-03-01 00:30:00"))
    grid = grid_for(rows, config)
    train_end, val_end = "2020-02-29 23:59:00", "2020-03-01 00:20:00"
    good = pd.concat([links(rows, train_end, train_end), links(rows, val_end, val_end)], ignore_index=True)
    result = masks(grid, rows, config, good)
    assert at(result, train_end).is_reference and at(result, val_end).is_reference
    assert good.groupby("window_end").raw_row_id.apply(set).iloc[0].isdisjoint(
        good.groupby("window_end").raw_row_id.apply(set).iloc[1])
    raw = links(rows, val_end, "2020-02-29 23:59:50")
    assert at(masks(grid, rows, config, raw), val_end).reason == "source_split"
    fills = raw.assign(target_timestamp=pd.Timestamp("2020-03-01 00:19:50"))
    result = masks(grid, rows, config, good, fills=fills)
    assert at(result, val_end).reason == "source_split" and not at(result, val_end).is_reference
    assert at(result, train_end).valid  # reject the offending window, not the whole table


def test_fill_origin_must_share_segment(config):
    rows = observations(config, ("2020-02-01 00:00:00", "2020-02-01 00:20:00"),
                        ("2020-02-01 01:00:00", "2020-02-01 01:30:00"))
    grid = grid_for(rows, config)
    end = "2020-02-01 01:20:00"
    source = links(rows, end, end)
    fills = links(rows, end, "2020-02-01 00:20:00").assign(target_timestamp=pd.Timestamp(end))
    result = masks(grid, rows, config, source, fills=fills)
    assert at(result, end).reason == "source_segment"


@pytest.mark.parametrize("age,expected", [(30, True), (31, False)])
def test_fill_age_exact_boundary(config, rows, age, expected):
    grid = grid_for(rows, config)
    end = "2020-02-01 00:25:00"
    source = links(rows, end, end)
    origin = "2020-02-01 00:24:20"
    fills = links(rows, end, origin).assign(target_timestamp=pd.Timestamp(origin) + pd.Timedelta(seconds=age))
    result = at(masks(grid, rows, config, source, fills=fills), end)
    assert result.valid == expected
    if not expected:
        assert result.reason == "stale_fill"


def test_reference_excludes_actual_fill_event_outside_nominal_window(config_values, write_config):
    config_values["features"]["window_minutes"] = 1
    config = load_config(write_config(config_values))
    rows = observations(config, ("2020-04-18 23:30:00", "2020-04-19 00:10:00"))
    grid = grid_for(rows, config)
    end = "2020-04-19 00:00:00"
    source = links(rows, end, end)
    fills = links(rows, end, "2020-04-18 23:58:50").assign(target_timestamp=pd.Timestamp("2020-04-18 23:59:20"))
    result = at(masks(grid, rows, config, source, fills=fills), end)
    assert result.valid and result.is_evaluation and result.label == 0
    assert result.source_event_ids == ["E1"] and not result.is_reference
    assert result.source_min_time == pd.Timestamp("2020-04-18 23:58:50")
    assert result.source_min_time < result.window_start


def test_reference_uses_actual_sources_instead_of_min_max_span(config, rows):
    grid = grid_for(rows, config)
    events = reported_events().iloc[:1].copy()
    events["start"] = pd.Timestamp("2020-02-01 00:22:00")
    events["end"] = pd.Timestamp("2020-02-01 00:22:30")
    end = "2020-02-01 00:25:00"
    sources = links(rows, end, "2020-02-01 00:20:10", end)
    result = at(masks(grid, rows, config, sources, events=events), end)
    assert result.is_reference and not result.source_overlaps_event


def test_test_windows_never_become_fit_reference(config):
    rows = observations(config, ("2020-05-01 00:00:00", "2020-05-01 00:30:00"))
    grid = grid_for(rows, config)
    end = "2020-05-01 00:20:00"
    result = at(masks(grid, rows, config, links(rows, end, end)), end)
    assert result.valid and result.is_evaluation and not result.is_reference


@pytest.mark.parametrize("source,expected", [
    ("2020-02-01 00:25:10", "future_source"),
    ("2020-02-01 00:20:00", "outside_window"),  # (t-W,t] is open on the left
])
def test_future_or_outside_window_sources_are_invalid(config, rows, source, expected):
    grid = grid_for(rows, config)
    end = "2020-02-01 00:25:00"
    result = at(masks(grid, rows, config, links(rows, end, source)), end)
    assert not result.valid and result.reason == expected and pd.isna(result.label)


def test_sensor_quality_is_required_and_reason_priority_is_stable(config, rows):
    grid = grid_for(rows, config)
    end = "2020-02-01 00:25:00"
    quality = pd.Series(False, index=grid.index)
    reasons = pd.Series("insufficient_coverage", index=grid.index)
    result = masks(grid, rows, config, links(rows, end, end), quality=quality, quality_reason=reasons)
    assert at(result, end).reason == "insufficient_coverage"
    assert at(result, "2020-02-01 00:15:00").reason == "warmup"
    assert at(result, "2020-02-01 00:26:00").reason == "missing_source"
    assert not result.is_reference.any() and not result.is_evaluation.any()
    # Custom reasons must not replace successful windows with a missing mask.
    result = masks(grid, rows, config, links(rows, end, end), quality_reason=reasons)
    assert at(result, end).valid


def test_all_events_remain_in_summary_even_without_valid_point(config, rows):
    grid = grid_for(rows, config)
    summary = summarize_time_grid(grid, reported_events())
    assert len(summary["event_coverage"]) == 4
    assert all(not e["evaluable"] and e["n_valid_timestamps"] == 0
               and e["first_valid_time"] is None for e in summary["event_coverage"])
    assert summary["splits"]["validation"]["source_event_ids"] == ["E1"]
    assert summary["splits"]["test"]["source_event_ids"] == ["E2", "E3", "E4"]
    assert summary["splits"]["test"]["evaluable_events"] == 0
    for part in summary["splits"].values():
        assert part["expected_ticks"] == part["valid_ticks"] + sum(part["excluded_by_reason"].values())
    json.dumps(summary, allow_nan=False)


def test_final_coverage_counts_positive_points_and_retains_zero_coverage_events(config):
    rows = observations(config, ("2020-04-18 00:00:00", "2020-04-18 00:30:00"))
    grid = grid_for(rows, config)
    end = "2020-04-18 00:20:00"
    final = masks(grid, rows, config, links(rows, end, end))
    assert at(final, end).label == 1 and not at(final, end).is_reference
    summary = summarize_time_grid(final, reported_events())
    assert summary["splits"]["validation"]["positive_ticks"] == 1
    assert summary["event_coverage"][0]["n_valid_timestamps"] == 1
    assert len(summary["event_coverage"]) == 4
    assert summary["mask_column"] == "valid"


def test_short_timeline_with_no_minute_ticks_has_typed_empty_grid(config):
    rows = observations(config, ("2020-02-01 00:00:10", "2020-02-01 00:00:20"))
    grid = grid_for(rows, config)
    assert grid.empty
    assert summarize_time_grid(grid, reported_events())["splits"]["train"]["expected_ticks"] == 0
    final = masks(grid, rows, config, links(rows, "2020-02-01 00:00:00"))
    assert final.empty


def test_invalid_contracts_fail_instead_of_silently_accepting_lineage(config, rows):
    grid = grid_for(rows, config)
    end = "2020-02-01 00:25:00"
    sources = links(rows, end, end)
    with pytest.raises(TemporalError, match="unknown raw_row_id"):
        masks(grid, rows, config, sources.assign(raw_row_id=-1))
    with pytest.raises(TemporalError, match="unknown window_end"):
        masks(grid, rows, config, sources.assign(window_end=pd.Timestamp("2020-02-02")))
    with pytest.raises(TemporalError, match="quality_valid"):
        masks(grid, rows, config, sources, quality=pd.Series(True, index=grid.index + 1))
    with pytest.raises(TemporalError, match="calendar changed"):
        masks(grid.assign(temporal_valid=True), rows, config, sources)
    with pytest.raises(TemporalError, match="cleaned.segment_id"):
        grid_for(rows.assign(segment_id=1), config)
    with pytest.raises(TemporalError, match="cleaned.split"):
        grid_for(rows.assign(split="test"), config)
    with pytest.raises(ValueError, match="timezone"):
        split_timestamps(pd.Series(pd.date_range("2020-02-01", periods=2, tz="UTC")), config)


def test_warmup_includes_exact_930_seconds(config):
    rows = observations(config, ("2020-02-01 00:00:30", "2020-02-01 00:20:30"))
    grid = grid_for(rows, config)
    assert at(grid, "2020-02-01 00:16:00").temporal_valid
    assert at(grid, "2020-02-01 00:15:00").warmup


@pytest.mark.parametrize("start,last,eligible", [
    ("00:00:00", "00:15:30", True),
    ("00:00:09", "00:15:29", False),
])
def test_trailing_gap_is_strictly_greater_than_30_seconds(config, start, last, eligible):
    rows = observations(config, (f"2020-02-01 {start}", f"2020-02-01 {last}"),
                        ("2020-02-01 00:20:00", "2020-02-01 00:40:00"))
    point = at(grid_for(rows, config), "2020-02-01 00:16:00")
    assert point.temporal_valid == eligible
    if not eligible:
        assert point.temporal_reason == "gap"


def test_grid_and_summary_survive_parquet_roundtrip_without_final_validity(config, rows, tmp_path):
    grid = grid_for(rows, config)
    path = tmp_path / "grid.parquet"
    grid.attrs["temporal"]["summary"] = summarize_time_grid(grid, reported_events())
    grid.to_parquet(path, index=False)
    restored = pd.read_parquet(path)
    pd.testing.assert_frame_equal(grid, restored)
    assert restored.attrs == grid.attrs
    assert "valid" not in restored and "is_reference" not in restored
    end = "2020-02-01 00:25:00"
    final = masks(restored, rows, config, links(rows, end, end))
    assert final.attrs["temporal"]["summary"]["mask_column"] == "valid"
    assert restored.attrs["temporal"]["summary"]["mask_column"] == "temporal_valid"


def test_dataset_version_and_train_fitted_gap_are_preserved_and_checked(config, rows):
    rows.attrs["audit"] = {"dataset_version": "fixture-v1", "csv_sha256": "a" * 64,
                           "cadence": {"gap_break_seconds": 30}}
    grid = grid_for(rows, config)
    assert grid.attrs["temporal"]["dataset_version"] == "fixture-v1"
    end = "2020-02-01 00:25:00"
    other = rows.copy()
    other.attrs["audit"]["dataset_version"] = "fixture-v2"
    with pytest.raises(TemporalError, match="dataset_version"):
        masks(grid, other, config, links(rows, end, end))
    with pytest.raises(TemporalError, match="train-fitted cadence"):
        build_time_grid(rows, config, gap_break_seconds=31)
