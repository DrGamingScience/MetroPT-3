"""PB04 acceptance: reported intervals, point labels and actual source overlap."""

from pathlib import Path

import pandas as pd
import pytest

from metropt3.events import (
    EVENT_COLUMNS, EVENT_SOURCE, EventError, event_coverage, label_timestamps,
    read_events, reference_status, reported_events, validate_events,
)
from metropt3.ingest import SENSOR_COLUMNS


@pytest.fixture
def events():
    return reported_events()


def test_reported_intervals_and_provenance(events):
    assert list(events.columns) == list(EVENT_COLUMNS)
    assert events.event_id.tolist() == ["E1", "E2", "E3", "E4"]
    assert events.start.dt.strftime("%Y-%m-%d %H:%M:%S").tolist() == [
        "2020-04-18 00:00:00", "2020-05-29 23:30:00",
        "2020-06-05 10:00:00", "2020-07-15 14:30:00",
    ]
    assert events.end.dt.strftime("%Y-%m-%d %H:%M:%S").tolist() == [
        "2020-04-18 23:59:00", "2020-05-30 06:00:00",
        "2020-06-07 14:30:00", "2020-07-15 19:00:00",
    ]
    assert events.source.eq(EVENT_SOURCE).all()
    assert events.failure_type.eq("Air leak").all()
    assert events.start.dt.tz is None and events.end.dt.tz is None
    assert "Maintenance on 30Apr at 12:00" in events.loc[1, "source_note"]
    assert "no date correction" in events.loc[1, "confidence_note"]


@pytest.mark.parametrize("event_index", range(4))
def test_closed_boundaries_at_nanosecond_precision(events, event_index):
    event = events.iloc[event_index]
    times = [event.start - pd.Timedelta(1, "ns"), event.start,
             event.end, event.end + pd.Timedelta(1, "ns")]
    labels = label_timestamps(times, events)
    assert labels.label.tolist() == [0, 1, 1, 0]
    assert labels.event_ids.tolist() == [[], [event.event_id], [event.event_id], []]


def test_e1_end_is_not_extended_to_end_of_minute(events):
    labels = label_timestamps(["2020-04-18 23:59:00", "2020-04-18 23:59:59"], events)
    assert labels.label.tolist() == [1, 0]


def test_zero_point_label_does_not_make_post_event_window_a_reference(events):
    # Nominal window (23:55, 00:00] still consumes observations from E1.
    times = pd.to_datetime(["2020-04-18 23:58:00", "2020-04-19 00:00:00"])
    label = label_timestamps(times[-1:], events)
    status = reference_status(times, events)
    assert label.label.tolist() == [0]
    assert status == {
        "source_event_ids": ["E1"], "source_overlaps_event": True, "is_reference": False,
    }


def test_fill_origin_outside_nominal_window_still_excludes_reference(events):
    # A fill at 23:59:20 originated at 23:59:00, outside (23:59:10, 00:00:10].
    actual = pd.to_datetime(["2020-04-18 23:59:20", "2020-04-19 00:00:10"])
    assert reference_status(actual, events)["is_reference"]
    status = reference_status(
        actual, events, fill_origin_timestamps=["2020-04-18 23:59:00"],
    )
    assert status["source_event_ids"] == ["E1"] and not status["is_reference"]
    assert label_timestamps(actual[-1:], events).label.tolist() == [0]


def test_source_check_uses_actual_timestamps_not_min_max_interval(events):
    sources = ["2020-04-17 23:59:59", "2020-04-19 00:00:00"]
    assert reference_status(sources, events)["source_event_ids"] == []
    # Split/segment/gap validity is supplied separately by PB05/PB07.
    assert not reference_status(sources, events, valid=False)["is_reference"]


def test_overlapping_events_return_all_ids_once_in_source_order(events):
    overlap = events.iloc[[0]].copy()
    overlap["event_id"] = "E1-overlap"
    combined = pd.concat([overlap, events], ignore_index=True)
    times = ["2020-04-18 12:00:00"] * 2
    labels = label_timestamps(times, combined)
    assert labels.event_ids.tolist() == [["E1-overlap", "E1"]] * 2
    assert reference_status(times, combined)["source_event_ids"] == ["E1-overlap", "E1"]
    labels.event_ids.iloc[0].append("local edit")
    assert labels.event_ids.iloc[1] == ["E1-overlap", "E1"]


def test_invalid_points_remain_nullable_and_do_not_count_for_coverage(events):
    times = pd.Series(pd.to_datetime([
        "2020-04-18 12:00:00", "2020-04-18 13:00:00", None, "2020-05-30 00:00:00",
    ]), index=[10, 30, 50, 70])
    valid = pd.Series([False, True, False, False], index=times.index)
    labels = label_timestamps(times, events, valid=valid)
    assert str(labels.label.dtype) == "Int8"
    assert labels.label.isna().tolist() == [True, False, True, True]
    assert labels.loc[30, "label"] == 1
    assert labels.event_ids.tolist() == [[], ["E1"], [], []]
    coverage = event_coverage(times, events, valid=valid)
    assert coverage.event_id.tolist() == ["E1", "E2", "E3", "E4"]
    assert coverage.n_valid_timestamps.tolist() == [1, 0, 0, 0]
    assert coverage.evaluable.tolist() == [True, False, False, False]
    assert coverage.first_valid_time.iloc[0] == times.loc[30]
    assert coverage.first_valid_time.iloc[1:].isna().all()


def test_labels_are_separate_and_never_mutate_sensor_features(events):
    features = pd.DataFrame({
        "window_end": pd.to_datetime(["2020-04-18 12:00:00", "2020-04-19 00:00:00"]),
        "TP2__mean__5min": [8.0, 7.0],
    }, index=[100, 200])
    before = features.copy(deep=True)
    original_events = events.copy(deep=True)
    labels = label_timestamps(features.window_end, events)
    pd.testing.assert_frame_equal(features, before)
    pd.testing.assert_frame_equal(events, original_events)
    assert labels.index.equals(features.index)
    assert set(labels.columns).isdisjoint(SENSOR_COLUMNS)
    assert "label" not in features and "event_ids" not in features
    assert features.join(labels[["label", "event_ids"]]).label.tolist() == [1, 0]


@pytest.mark.parametrize("column,value,message", [
    ("event_id", "E2", "duplicate IDs"),
    ("start", "2020-04-19 00:00:00", "start must be <= end"),
    ("end", pd.NaT, "missing event boundary"),
    ("start", "2020-04-18 00:00:60", "expected an ISO timestamp"),
    ("end", "2020-02-30 00:00:00", "invalid timestamp"),
    ("source", " ", "empty values"),
])
def test_invalid_event_table_is_rejected(events, column, value, message):
    modified = events.astype({column: object})
    modified.loc[0, column] = value
    with pytest.raises(EventError, match=message):
        validate_events(modified)


@pytest.mark.parametrize("times", [
    ["2020-04-18 00:00:00+07:00"],
    pd.date_range("2020-04-18", periods=1, tz="UTC"),
    [pd.Timestamp("2020-04-18", tz="Asia/Ho_Chi_Minh")],
    ["18/04/2020 00:00:00"], [123],
])
def test_no_implicit_timezone_or_timestamp_inference(events, times):
    with pytest.raises(EventError):
        label_timestamps(times, events)
    with pytest.raises(EventError):
        reference_status(times, events)


def test_masks_must_be_boolean_complete_and_aligned(events):
    times = pd.Series(pd.to_datetime(["2020-04-18 12:00:00"]), index=[10])
    for bad in ([1], [None], [], pd.Series([True], index=[20])):
        with pytest.raises(EventError, match="valid"):
            label_timestamps(times, events, valid=bad)
    with pytest.raises(EventError, match="cannot be missing"):
        label_timestamps([pd.NaT], events)
    with pytest.raises(EventError, match="actual source timestamps"):
        reference_status([], events)
    with pytest.raises(EventError, match="cannot be missing"):
        reference_status([pd.NaT], events)
    with pytest.raises(EventError, match="cannot be missing"):
        reference_status(times, events, fill_origin_timestamps=[pd.NaT])
    assert not reference_status([], events, valid=False)["is_reference"]


def test_empty_evaluation_retains_every_event_as_not_evaluable(events):
    assert label_timestamps([], events, valid=[]).empty
    coverage = event_coverage([], events, valid=[])
    assert len(coverage) == 4
    assert not coverage.evaluable.any()
    assert coverage.n_valid_timestamps.eq(0).all()
    assert coverage.first_valid_time.isna().all()


def test_events_csv_roundtrip_and_review_copy_match(events, tmp_path):
    path = tmp_path / "events.csv"
    events.to_csv(path, index=False, date_format="%Y-%m-%d %H:%M:%S")
    pd.testing.assert_frame_equal(read_events(path), events)
    review_copy = Path(__file__).resolve().parents[1] / "docs/examples/pb04/events.csv"
    pd.testing.assert_frame_equal(read_events(review_copy), events)
    # This blank is intentional source information, not NaN.
    events.loc[0, "source_note"] = ""
    events.to_csv(path, index=False)
    assert read_events(path).loc[0, "source_note"] == ""


def test_missing_schema_and_missing_file_report_event_errors(events, tmp_path):
    with pytest.raises(EventError, match="expected exactly"):
        validate_events(events.drop(columns=["source"]))
    with pytest.raises(EventError, match="cannot read events"):
        read_events(tmp_path / "missing.csv")
