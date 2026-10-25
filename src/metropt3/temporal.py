"""Minute calendar and source-aware split/purge policy, shared with PB07.

The calendar reports temporal eligibility only. Final window validity requires
PB07's sensor-quality decision and the complete raw/fill lineage.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from metropt3.config import ProjectConfig
from metropt3.events import _clock, event_coverage, label_timestamps, validate_events


SPLITS = ("train", "validation", "test")


class TemporalError(ValueError):
    """Calendar or window lineage violates the temporal contract."""


def split_timestamps(timestamps, config: ProjectConfig) -> pd.Series:
    """Assign each original-clock timestamp to exactly one half-open split."""
    times = _clock(timestamps, "timestamp")
    if times.isna().any():
        raise TemporalError("timestamp: missing values cannot be assigned to a split")
    boundaries = config.as_dict()["split"]
    return pd.Series(np.where(
        times < pd.Timestamp(boundaries["train_end_exclusive"]), "train",
        np.where(times < pd.Timestamp(boundaries["validation_end_exclusive"]),
                 "validation", "test"),
    ), index=times.index, name="split")


def _cleaned_rows(cleaned: pd.DataFrame, config: ProjectConfig) -> pd.DataFrame:
    columns = ["timestamp", "raw_row_id", "segment_id", "split"]
    if not cleaned.columns.is_unique or not set(columns).issubset(cleaned.columns):
        raise TemporalError(f"cleaned: requires unique columns including {columns}")
    rows = cleaned[columns].copy().reset_index(drop=True)
    if rows.empty:
        raise TemporalError("cleaned: at least one observation is required")
    rows["timestamp"] = _clock(rows.timestamp, "cleaned.timestamp")
    if (rows.timestamp.isna().any() or rows.timestamp.duplicated().any()
            or not rows.timestamp.is_monotonic_increasing):
        raise TemporalError("cleaned.timestamp: expected sorted unique non-missing timestamps")
    for name in ("raw_row_id", "segment_id"):
        if (not pd.api.types.is_integer_dtype(rows[name])
                or pd.api.types.is_bool_dtype(rows[name])
                or rows[name].isna().any() or (rows[name] < 0).any()):
            raise TemporalError(f"cleaned.{name}: expected nonnegative integer IDs")
    if rows.raw_row_id.duplicated().any():
        raise TemporalError("cleaned.raw_row_id: IDs must be unique within a dataset version")
    if not rows.split.equals(split_timestamps(rows.timestamp, config)):
        raise TemporalError("cleaned.split: differs from the configured calendar boundaries")
    return rows


def build_time_grid(
    cleaned: pd.DataFrame, config: ProjectConfig, *, gap_break_seconds: float,
) -> pd.DataFrame:
    """Keep all minute ticks from ceil(first observation) through floor(last).

    A block is a (split, segment_id) pair. Its first actual observation starts
    warm-up. Only observations at or before t determine eligibility at t; a
    trailing age > gap_break is a gap. PB07 must still check window edge ages,
    per-sensor coverage and internal gaps. No resampling/filling is performed.
    """
    if (isinstance(gap_break_seconds, (bool, np.bool_))
            or not np.isfinite(gap_break_seconds) or gap_break_seconds <= 0):
        raise TemporalError("gap_break_seconds: expected a positive finite train-fitted value")
    rows = _cleaned_rows(cleaned, config)
    audit = cleaned.attrs.get("audit", {})
    fitted_gap = audit.get("cadence", {}).get("gap_break_seconds")
    if fitted_gap is not None and fitted_gap != gap_break_seconds:
        raise TemporalError("gap_break_seconds: differs from the cleaned dataset's train-fitted cadence")
    expected_segments = (rows.timestamp.diff().dt.total_seconds() > gap_break_seconds).cumsum()
    if not np.array_equal(rows.segment_id.to_numpy(), expected_segments.to_numpy()):
        raise TemporalError("cleaned.segment_id: inconsistent with the supplied train-fitted gap_break")
    values = config.as_dict()
    warmup = values["quality"]["common_warmup_seconds"]
    rows["block_start"] = rows.groupby(["split", "segment_id"], sort=False).timestamp.transform("first")
    ticks = pd.DataFrame({"window_end": pd.date_range(
        rows.timestamp.iloc[0].ceil("min"), rows.timestamp.iloc[-1].floor("min"), freq="60s",
    )})
    ticks["split"] = split_timestamps(ticks.window_end, config)
    latest = pd.merge_asof(
        ticks[["window_end"]], rows.rename(columns={"split": "source_split"}),
        left_on="window_end", right_on="timestamp", direction="backward",
    )
    same_split = ticks.split.eq(latest.source_split)
    gap = ~same_split | ((ticks.window_end - latest.timestamp).dt.total_seconds() > gap_break_seconds)
    ticks["segment_id"] = latest.segment_id.astype("Int64").where(~gap)
    ticks["block_start"] = latest.block_start.where(~gap)
    ticks["warmup_until"] = ticks.block_start + pd.to_timedelta(warmup, unit="s")
    ticks["warmup"] = ~gap & (ticks.window_end < ticks.warmup_until)
    ticks["temporal_valid"] = ~gap & ~ticks.warmup
    ticks["temporal_reason"] = pd.Series(np.select(
        [gap, ticks.warmup], ["gap", "warmup"], default="",
    ), dtype="string").replace("", pd.NA)
    ticks["window_start"] = ticks.window_end - pd.to_timedelta(values["features"]["window_minutes"], unit="min")
    ticks.attrs["temporal"] = {
        "scope": "temporal eligibility only; PB07 quality and actual-source checks still required",
        "split": values["split"], "config_hash": config.config_hash,
        "config_snapshot": values,
        "stride_seconds": 60, "window_closed": "right",
        "window_minutes": values["features"]["window_minutes"],
        "common_warmup_seconds": warmup, "gap_break_seconds": float(gap_break_seconds),
        "reason_priority": ["gap", "warmup", "source_split", "source_segment",
                            "future_source", "outside_window", "stale_fill", "missing_source", "quality"],
        "duration_policy": "tick counts times 60 seconds; represented grid duration, not sensor uptime",
    }
    ticks.attrs["temporal"].update({
        key: audit[key] for key in ("raw_manifest", "dataset_version", "csv_sha256") if key in audit
    })
    return ticks


def _quality_mask(values: pd.Series, grid: pd.DataFrame) -> pd.Series:
    if (not isinstance(values, pd.Series) or not values.index.equals(grid.index)
            or not pd.api.types.is_bool_dtype(values.dtype) or values.isna().any()):
        raise TemporalError("quality_valid: expected non-missing boolean Series aligned to the grid")
    return values.astype(bool)


def apply_window_masks(
    grid: pd.DataFrame, cleaned: pd.DataFrame, events: pd.DataFrame,
    config: ProjectConfig, *, sources: pd.DataFrame, quality_valid: pd.Series,
    fill_origins: pd.DataFrame | None = None, quality_reason: pd.Series | None = None,
) -> pd.DataFrame:
    """Finalize PB07 windows using complete actual lineage, never nominal bounds.

    sources: one (window_end, raw_row_id) per raw observation actually used.
    fill_origins: (window_end, raw_row_id, target_timestamp) for EVERY filled value;
    the ID identifies its original observation, not the intervening filled row.
    Repeated IDs (multiple sensors) are allowed. The caller supplies the complete
    source set and quality check for its feature set. Unknown IDs/ticks fail fast.
    Empty lineage invalidates a window rather than silently creating reference.
    """
    rows = _cleaned_rows(cleaned, config)
    meta = grid.attrs.get("temporal", {})
    if meta.get("config_hash") != config.config_hash:
        raise TemporalError("grid: config differs; rebuild the calendar for this configuration")
    for key in ("dataset_version", "csv_sha256"):
        if key in meta and meta[key] != cleaned.attrs.get("audit", {}).get(key):
            raise TemporalError(f"grid: {key} differs from the supplied cleaned dataset")
    expected = build_time_grid(cleaned, config, gap_break_seconds=meta["gap_break_seconds"])
    if not grid[expected.columns].equals(expected):
        raise TemporalError("grid: calendar changed or belongs to a different cleaned dataset")
    events = validate_events(events)
    quality = _quality_mask(quality_valid, grid)
    if quality_reason is not None:
        if not isinstance(quality_reason, pd.Series) or not quality_reason.index.equals(grid.index):
            raise TemporalError("quality_reason: expected a Series aligned to the grid")
        if not quality_reason.dropna().map(lambda x: isinstance(x, str) and bool(x.strip())).all():
            raise TemporalError("quality_reason: use nonempty strings or null")
    result = grid.copy()
    result.attrs["temporal"] = dict(meta)
    reason = result.temporal_reason.copy()
    bad = {name: pd.Series(False, index=result.index) for name in (
        "source_split", "source_segment", "future_source", "outside_window", "stale_fill",
    )}
    counts = pd.Series(0, index=result.index, dtype="int64")
    event_ids = [[] for _ in range(len(result))]
    source_min = pd.Series(pd.NaT, index=result.index, dtype="datetime64[ns]")
    source_max = source_min.copy()
    targets = result[["window_end", "window_start", "split", "segment_id"]].copy()
    targets["position"] = np.arange(len(result))
    for lineage, is_fill in ((sources, False), (fill_origins, True)):
        if lineage is None:
            continue
        required = {"window_end", "raw_row_id"} | ({"target_timestamp"} if is_fill else set())
        if not lineage.columns.is_unique or set(lineage.columns) != required:
            raise TemporalError(f"lineage: expected exactly {sorted(required)}")
        links = lineage.copy()
        links["window_end"] = _clock(links.window_end, "lineage.window_end")
        if not links.empty and (not pd.api.types.is_integer_dtype(links.raw_row_id)
                                or pd.api.types.is_bool_dtype(links.raw_row_id)):
            raise TemporalError("lineage.raw_row_id: expected integer IDs")
        if links.raw_row_id.isna().any() or links.window_end.isna().any():
            raise TemporalError("lineage: missing IDs/timestamps")
        if not links.window_end.isin(result.window_end).all():
            raise TemporalError("lineage: unknown window_end")
        if not links.raw_row_id.isin(rows.raw_row_id).all():
            raise TemporalError("lineage: unknown raw_row_id in this dataset version")
        if links.empty:
            continue
        if is_fill:
            links["target_timestamp"] = _clock(links.target_timestamp, "fill.target_timestamp")
            if links.target_timestamp.isna().any():
                raise TemporalError("fill.target_timestamp: missing timestamp")
        links = links.merge(rows.rename(columns={"split": "source_split", "segment_id": "source_segment"}),
                            on="raw_row_id", validate="many_to_one")
        links = links.merge(targets, on="window_end", validate="many_to_one")
        used_time = links.target_timestamp if is_fill else links.timestamp
        flags = {
            "source_split": links.source_split.ne(links.split),
            "source_segment": links.source_segment.ne(links.segment_id).fillna(True),
            "future_source": links.timestamp.gt(used_time) | used_time.gt(links.window_end),
            "outside_window": used_time.le(links.window_start) | used_time.gt(links.window_end),
            "stale_fill": ((used_time - links.timestamp).dt.total_seconds()
                           > config.as_dict()["quality"]["max_ffill_age_seconds"]) if is_fill
                          else pd.Series(False, index=links.index),
        }
        # With a same-segment origin <= target <= t, the intervening target is
        # also in that segment. Check its split explicitly as well as causality.
        if is_fill:
            flags["source_split"] |= split_timestamps(used_time, config).ne(links.split)
        for name, mask in flags.items():
            positions = links.loc[mask, "position"].unique()
            bad[name].iloc[positions] = True
        grouped = links.groupby("position").timestamp
        n = grouped.size()
        counts.iloc[n.index] += n.to_numpy()
        for series, new, op in ((source_min, grouped.min(), "min"), (source_max, grouped.max(), "max")):
            combined = pd.concat([series.iloc[new.index].reset_index(drop=True), new.reset_index(drop=True)], axis=1)
            series.iloc[new.index] = getattr(combined, op)(axis=1).to_numpy()
        for event in events.itertuples(index=False):
            hits = links.loc[links.timestamp.between(event.start, event.end, inclusive="both"), "position"].unique()
            for position in hits:
                if event.event_id not in event_ids[position]:
                    event_ids[position].append(event.event_id)
    for name, mask in bad.items():
        reason = reason.mask(reason.isna() & mask, name)
    reason = reason.mask(reason.isna() & counts.eq(0), "missing_source")
    reason = reason.mask(reason.isna() & ~quality, "quality")
    if quality_reason is not None:
        reason = reason.mask(reason.eq("quality").fillna(False), quality_reason.fillna("quality"))
    result["valid"] = reason.isna()
    result["reason"] = reason
    result["is_evaluation"] = result.valid
    # Preserve source-table event ordering, including overlaps found only in fill.
    order = {event_id: i for i, event_id in enumerate(events.event_id)}
    result["source_event_ids"] = [sorted(ids, key=order.__getitem__) for ids in event_ids]
    result["source_overlaps_event"] = [bool(ids) for ids in event_ids]
    result["source_min_time"], result["source_max_time"] = source_min, source_max
    result["is_reference"] = result.valid & result.split.isin(["train", "validation"]) & ~result.source_overlaps_event
    labels = label_timestamps(result.window_end, events, valid=result.valid)
    result["label"], result["event_ids"] = labels.label, labels.event_ids
    result.attrs["temporal"]["scope"] = "final masks for the caller-supplied complete lineage and PB07 quality decision"
    result.attrs["temporal"]["summary"] = summarize_time_grid(result, events)
    return result


def summarize_time_grid(grid: pd.DataFrame, events: pd.DataFrame) -> dict:
    """Count every expected tick and retain even events with no eligible point."""
    events = validate_events(events)
    final = "valid" in grid
    mask = grid.valid if final else grid.temporal_valid
    reasons = grid.reason if final else grid.temporal_reason
    labels = label_timestamps(grid.window_end, events, valid=mask)
    coverage = event_coverage(grid.window_end, events, valid=mask)
    coverage["first_valid_time"] = coverage.first_valid_time.map(lambda t: str(t) if pd.notna(t) else None)
    boundaries = grid.attrs["temporal"]["split"]
    train_end, val_end = (pd.Timestamp(boundaries[key]) for key in (
        "train_end_exclusive", "validation_end_exclusive",
    ))
    parts = {}
    for name in SPLITS:
        selected = grid.split.eq(name)
        overlaps = ((events.start < train_end) if name == "train" else
                    ((events.end >= train_end) & (events.start < val_end)) if name == "validation" else
                    (events.end >= val_end))
        event_part = event_coverage(grid.loc[selected, "window_end"], events.loc[overlaps], valid=mask[selected])
        parts[name] = {
            "expected_ticks": int(selected.sum()), "valid_ticks": int((selected & mask).sum()),
            "excluded_by_reason": {str(k): int(v) for k, v in reasons[selected].value_counts().items()},
            "expected_grid_seconds": int(selected.sum()) * 60,
            "valid_grid_seconds": int((selected & mask).sum()) * 60,
            "positive_ticks": int(labels.loc[selected, "label"].eq(1).sum()),
            "reference_ticks": int(grid.loc[selected, "is_reference"].sum()) if final else None,
            "source_event_ids": events.loc[overlaps, "event_id"].tolist(),
            "source_events": int(overlaps.sum()), "evaluable_events": int(event_part.evaluable.sum()),
        }
    return {
        "scope": "final caller-supplied window masks" if final else "temporal eligibility only; not final scoring-window coverage",
        "mask_column": "valid" if final else "temporal_valid", "splits": parts,
        "event_coverage": coverage.to_dict(orient="records"),
    }
