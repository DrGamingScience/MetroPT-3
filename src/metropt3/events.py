"""Reported failures, point labels and source-aware reference checks.

Labels are evaluation sidecars, never detector features. A zero means outside
the reported intervals, not a guarantee of healthy operation. All timestamps
use the original, timezone-naive sensor clock; intervals include both ends.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


EVENT_SOURCE = "https://archive.ics.uci.edu/dataset/791/metropt3%2Bdataset"
EVENT_COLUMNS = (
    "event_id", "start", "end", "failure_type", "source", "source_note", "confidence_note",
)
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
_CLOCK_PATTERN = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}[ T](?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    r"(?:\.[0-9]{1,9})?"
)


class EventError(ValueError):
    """Event definitions or timestamp/mask inputs violate the clock contract."""


def _clock(values, name: str) -> pd.Series:
    times = values.copy() if isinstance(values, pd.Series) else pd.Series(values)
    if isinstance(times.dtype, pd.DatetimeTZDtype):
        raise EventError(f"{name}: use the original clock without timezone conversion")
    if pd.api.types.is_datetime64_dtype(times.dtype):
        return times
    parsed = []
    for value in times:
        if value is None or value is pd.NA or value is pd.NaT:
            parsed.append(pd.NaT)
            continue
        if isinstance(value, str):
            if not _CLOCK_PATTERN.fullmatch(value):
                raise EventError(f"{name}: expected an ISO timestamp without timezone: {value!r}")
        elif not isinstance(value, (datetime, np.datetime64)):
            raise EventError(f"{name}: expected datetime values, not {type(value).__name__}")
        try:
            timestamp = pd.Timestamp(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise EventError(f"{name}: invalid timestamp {value!r}") from exc
        if timestamp.tzinfo is not None:
            raise EventError(f"{name}: use the original clock without timezone conversion")
        parsed.append(timestamp)
    return pd.Series(pd.to_datetime(parsed), index=times.index, name=times.name)


def validate_events(events: pd.DataFrame) -> pd.DataFrame:
    """Return a validated copy; permit overlapping events and preserve row order."""
    if not events.columns.is_unique or set(events.columns) != set(EVENT_COLUMNS):
        raise EventError(f"events: expected exactly these columns: {', '.join(EVENT_COLUMNS)}")
    result = events.loc[:, list(EVENT_COLUMNS)].copy().reset_index(drop=True)
    for name in ("event_id", "failure_type", "source", "source_note", "confidence_note"):
        if not result[name].map(lambda x: isinstance(x, str)).all():
            raise EventError(f"events.{name}: expected strings (empty notes are allowed)")
        if name in ("event_id", "failure_type", "source") and result[name].str.strip().eq("").any():
            raise EventError(f"events.{name}: empty values are not allowed")
    if result.event_id.duplicated().any():
        raise EventError("events.event_id: duplicate IDs")
    for name in ("start", "end"):
        result[name] = _clock(result[name], f"events.{name}")
        if result[name].isna().any():
            raise EventError(f"events.{name}: missing event boundary")
    if (result.start > result.end).any():
        raise EventError("events: start must be <= end")
    return result


def reported_events() -> pd.DataFrame:
    """Transcribe UCI's four company reports; E1-E4 are local unique IDs.

    The source repeats Nr. #1 for its second row. Its April maintenance note
    conflicts with the May interval; both are retained without correcting dates.
    Minute-precision boundaries are represented with seconds exactly 00.
    """
    intervals = (
        ("E1", "2020-04-18 00:00:00", "2020-04-18 23:59:00", "Nr. #1; severity: High stress; report: blank."),
        ("E2", "2020-05-29 23:30:00", "2020-05-30 06:00:00", "Nr. #1; severity: High stress; Maintenance on 30Apr at 12:00"),
        ("E3", "2020-06-05 10:00:00", "2020-06-07 14:30:00", "Nr. #3; severity: High stress; Maintenance on 8Jun at 16:00"),
        ("E4", "2020-07-15 14:30:00", "2020-07-15 19:00:00", "Nr. #4; severity: High stress; Maintenance on 16Jul at 00:00"),
    )
    records = []
    for event_id, start, end, note in intervals:
        confidence = (
            "Company-reported interval, not independently verified; minute precision; "
            "timezone unspecified. Local event IDs follow source row order."
        )
        if event_id == "E2":
            confidence += (
                " Source repeats Nr. #1 and says 30Apr despite a May interval; "
                "original note and interval retained, no date correction."
            )
        records.append((event_id, start, end, "Air leak", EVENT_SOURCE, note, confidence))
    return validate_events(pd.DataFrame(records, columns=EVENT_COLUMNS))


def read_events(path: str | Path) -> pd.DataFrame:
    """Read an events.csv without treating empty source notes as missing values."""
    try:
        return validate_events(pd.read_csv(path, dtype=str, keep_default_na=False))
    except (OSError, ValueError) as exc:
        raise EventError(f"cannot read events: {exc}") from exc


def _evaluation_inputs(window_end, valid) -> tuple[pd.Series, pd.Series]:
    times = _clock(window_end, "window_end")
    if valid is None:
        mask = pd.Series(True, index=times.index)
    elif isinstance(valid, pd.Series):
        if not valid.index.equals(times.index):
            raise EventError("valid: index must match window_end; align explicitly")
        mask = valid.copy()
    else:
        if len(valid) != len(times):
            raise EventError("valid: length must match window_end")
        mask = pd.Series(valid, index=times.index, dtype=bool if len(valid) == 0 else None)
    if not pd.api.types.is_bool_dtype(mask.dtype) or mask.isna().any():
        raise EventError("valid: expected non-missing booleans")
    if (mask & times.isna()).any():
        raise EventError("window_end: valid evaluation timestamps cannot be missing")
    return times, mask.astype(bool)


def label_timestamps(window_end, events: pd.DataFrame, *, valid=None) -> pd.DataFrame:
    """Build a separate label table on the caller's index.

    Invalid rows have a nullable label, never zero. event_ids lists every match
    in event-table order. This table must not be passed to a detector as features.
    """
    events = validate_events(events)
    times, mask = _evaluation_inputs(window_end, valid)
    labels = pd.Series(pd.NA, index=times.index, dtype="Int8")
    labels.loc[mask] = 0
    ids = [[] for _ in range(len(times))]
    for event in events.itertuples(index=False):
        hit = mask & times.between(event.start, event.end, inclusive="both")
        labels.loc[hit] = 1
        for position in np.flatnonzero(hit.to_numpy()):
            ids[position].append(event.event_id)
    return pd.DataFrame({
        "window_end": times, "valid": mask, "label": labels, "event_ids": ids,
    }, index=times.index)


def reference_status(
    source_timestamps, events: pd.DataFrame, *, fill_origin_timestamps=(), valid: bool = True,
) -> dict:
    """Check every source actually used, including original timestamps of fills.

    Call during feature construction with the complete source set, not nominal
    window bounds or source min/max. Origins outside the nominal window still
    count. This checks event exclusion only; PB05/PB07 must also enforce quality,
    split and segment rules before passing valid=True.
    """
    if not isinstance(valid, (bool, np.bool_)):
        raise EventError("valid: expected a boolean")
    events = validate_events(events)
    sources = _clock(source_timestamps, "source_timestamps")
    origins = _clock(fill_origin_timestamps, "fill_origin_timestamps")
    if sources.isna().any() or origins.isna().any():
        raise EventError("source timestamps and fill origins cannot be missing")
    if valid and sources.empty:
        raise EventError("valid reference window requires actual source timestamps")
    ids = []
    for event in events.itertuples(index=False):
        if (sources.between(event.start, event.end, inclusive="both").any()
                or origins.between(event.start, event.end, inclusive="both").any()):
            ids.append(event.event_id)
    return {
        "source_event_ids": ids, "source_overlaps_event": bool(ids),
        "is_reference": bool(valid and not ids),
    }


def event_coverage(window_end, events: pd.DataFrame, *, valid=None) -> pd.DataFrame:
    """Keep all reported events, including those with no valid evaluation point.

    PB11 must call with valid *score* timestamps/common mask. Passing cleaned row
    timestamps instead gives row availability only, not final model evaluability.
    """
    events = validate_events(events)
    times, mask = _evaluation_inputs(window_end, valid)
    records = []
    for event in events.itertuples(index=False):
        selected = times[mask & times.between(event.start, event.end, inclusive="both")]
        records.append((
            event.event_id, len(selected), bool(len(selected)),
            selected.min() if len(selected) else pd.NaT,
        ))
    return pd.DataFrame(records, columns=(
        "event_id", "n_valid_timestamps", "evaluable", "first_valid_time",
    ))
