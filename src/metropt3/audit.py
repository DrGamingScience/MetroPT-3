"""Audit raw observations and fit a sampling cadence using train timestamps only."""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from metropt3.config import ProjectConfig
from metropt3.ingest import (
    DIGITAL_COLUMNS, REFERENCE_CSV_SHA256, SENSOR_COLUMNS,
    _inspect_csv, _verify_locked,
)


TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
QUALITY_FLAGS = (
    "invalid_timestamp", "missing_cell", "invalid_numeric", "infinity", "invalid_digital",
)


class AuditError(ValueError):
    """The source cannot be verified or train cadence cannot be estimated."""


@dataclass
class AuditTables:
    cleaned: pd.DataFrame
    issues: pd.DataFrame
    conflicts: pd.DataFrame
    duplicate_rows: pd.DataFrame
    gaps: pd.DataFrame
    summary: dict


def _delta_summary(delta: pd.Series) -> dict:
    positive = delta[delta > 0]
    counts = positive.value_counts().sort_index()
    return {
        "count": len(positive),
        "min_seconds": float(positive.min()) if len(positive) else None,
        "max_seconds": float(positive.max()) if len(positive) else None,
        "median_seconds": float(positive.median()) if len(positive) else None,
        "quantiles_seconds": {
            str(q): float(positive.quantile(q)) if len(positive) else None
            for q in (0.01, 0.05, 0.25, 0.75, 0.95, 0.99)
        },
        "distribution_seconds": {str(float(k)): int(v) for k, v in counts.items()},
    }


def audit_rows(raw: pd.DataFrame, config: ProjectConfig) -> AuditTables:
    """Materialize CSV record IDs; keep sensor defects flagged for downstream masks.

    Input values are original strings, including blanks. The original index is
    provenance, not a sensor: exact duplicates compare timestamp + sensor tokens.
    Conflicting timestamps and unparseable timestamps never enter cleaned rows.
    """
    values = config.as_dict()
    if values["quality"]["gap_multiplier"] != 3:
        raise AuditError("quality.gap_multiplier: PB03 requires 3")
    raw = raw.copy()
    raw["raw_row_id"] = np.arange(len(raw), dtype=np.int64)
    timestamps = raw["timestamp"]
    # Check clock ranges before parsing: pandas may normalize seconds 60/61.
    # Calendar validity is checked by to_datetime; never infer day/month or offsets.
    format_ok = timestamps.str.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2} (?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    ).fillna(False)
    parsed = pd.to_datetime(timestamps.where(format_ok), format=TIMESTAMP_FORMAT, errors="coerce")
    flags = pd.DataFrame(False, index=raw.index, columns=QUALITY_FLAGS)
    flags["invalid_timestamp"] = parsed.isna()
    train_mask = parsed < pd.Timestamp(values["split"]["train_end_exclusive"])
    numeric = pd.DataFrame(index=raw.index)
    column_stats = {}
    for name in SENSOR_COLUMNS:
        text = raw[name].str.strip()
        missing = text.eq("") | text.isna()
        number = pd.to_numeric(text, errors="coerce").astype("float64")
        invalid = number.isna() & ~missing
        infinity = np.isinf(number)
        domain = (
            number.notna() & ~number.isin([0, 1])
            if name in DIGITAL_COLUMNS else pd.Series(False, index=raw.index)
        )
        flags["missing_cell"] |= missing
        flags["invalid_numeric"] |= invalid
        flags["infinity"] |= infinity
        flags["invalid_digital"] |= domain
        finite_train = number[train_mask & np.isfinite(number) & ~domain]
        column_stats[name] = {
            "raw_type": str(raw[name].dtype), "cleaned_type": "float64",
            "missing_cells": int(missing.sum()), "invalid_numeric_cells": int(invalid.sum()),
            "infinity_cells": int(infinity.sum()), "invalid_digital_cells": int(domain.sum()),
            "unique_numeric_values": int(number.nunique()),
            "train_finite": {
                "count": len(finite_train),
                "min": float(finite_train.min()) if len(finite_train) else None,
                "median": float(finite_train.median()) if len(finite_train) else None,
                "max": float(finite_train.max()) if len(finite_train) else None,
            },
        }
        numeric[name] = number

    # Only inspect repeated timestamps, avoiding a full 15-sensor groupby on real raw.
    repeated = parsed.notna() & parsed.duplicated(keep=False)
    duplicate_candidates = raw.loc[repeated].copy()
    duplicate_candidates["parsed_timestamp"] = parsed[repeated]
    keys = ["parsed_timestamp", *SENSOR_COLUMNS]
    duplicates = pd.DataFrame(columns=["raw_row_id", "representative_raw_row_id", "duplicate_count"])
    representative = pd.Series(True, index=raw.index)
    duplicate_count = pd.Series(1, index=raw.index, dtype="int64")
    conflict_mask = pd.Series(False, index=raw.index)
    if len(duplicate_candidates):
        grouped = duplicate_candidates.groupby(keys, sort=False, dropna=False)["raw_row_id"]
        ids = grouped.transform("min")
        counts = grouped.transform("size")
        representative.loc[repeated] = duplicate_candidates["raw_row_id"].eq(ids)
        duplicate_count.loc[repeated] = counts
        multiple = counts > 1
        duplicates = pd.DataFrame({
            "raw_row_id": duplicate_candidates.loc[multiple, "raw_row_id"],
            "representative_raw_row_id": ids[multiple], "duplicate_count": counts[multiple],
        }).reset_index(drop=True)
        distinct = duplicate_candidates.loc[representative[repeated]]
        conflict_times = distinct.loc[
            distinct["parsed_timestamp"].duplicated(keep=False), "parsed_timestamp"
        ]
        conflict_mask = parsed.isin(conflict_times)

    annotated = raw.loc[flags.any(axis=1) | conflict_mask].copy()
    annotated["parsed_timestamp"] = parsed.loc[annotated.index]
    for name in QUALITY_FLAGS:
        annotated[name] = flags.loc[annotated.index, name]
    annotated["timestamp_conflict"] = conflict_mask.loc[annotated.index]
    issues = annotated.loc[flags.any(axis=1)].reset_index(drop=True)
    conflicts = annotated.loc[conflict_mask].reset_index(drop=True)
    keep = parsed.notna() & representative & ~conflict_mask
    cleaned = raw.loc[keep, [c for c in raw.columns if c not in SENSOR_COLUMNS]].copy()
    cleaned["timestamp"] = parsed[keep]
    for name in SENSOR_COLUMNS:
        cleaned[name] = numeric.loc[keep, name]
    for name in QUALITY_FLAGS:
        cleaned[name] = flags.loc[keep, name]
    cleaned["valid"] = ~flags.loc[keep].any(axis=1)
    cleaned["duplicate_count"] = duplicate_count[keep]
    cleaned = cleaned.sort_values(["timestamp", "raw_row_id"], kind="stable").reset_index(drop=True)
    train_end = pd.Timestamp(values["split"]["train_end_exclusive"])
    validation_end = pd.Timestamp(values["split"]["validation_end_exclusive"])
    train_times = cleaned.loc[cleaned["timestamp"] < train_end, "timestamp"]
    train_delta = train_times.diff().dt.total_seconds()
    positive = train_delta[train_delta > 0]
    if positive.empty:
        raise AuditError(
            "train cadence: need at least two distinct non-conflicting train timestamps; "
            "no validation/test fallback"
        )
    frequency = positive.value_counts()
    modes = sorted(float(x) for x in frequency[frequency == frequency.max()].index)
    delta0 = modes[0]
    gap_break = 3 * delta0
    delta = cleaned["timestamp"].diff().dt.total_seconds()
    breaks = delta > gap_break
    cleaned["segment_id"] = breaks.cumsum().astype("int64")
    cleaned["split"] = np.where(
        cleaned["timestamp"] < train_end, "train",
        np.where(cleaned["timestamp"] < validation_end, "validation", "test"),
    )
    gaps = cleaned.loc[breaks, ["raw_row_id", "timestamp", "segment_id"]].copy()
    gaps.insert(0, "previous_raw_row_id", cleaned["raw_row_id"].shift()[breaks].astype("int64"))
    gaps.insert(1, "previous_timestamp", cleaned["timestamp"].shift()[breaks])
    gaps["delta_seconds"] = delta[breaks]
    # An estimate relative to cadence, not an invented/resampled timestamp grid.
    absent = np.maximum(np.ceil(delta.fillna(0) / delta0).astype("int64") - 1, 0)
    gaps["estimated_missing_ticks"] = absent[breaks]
    summary = {
        "timestamp_format": TIMESTAMP_FORMAT, "timezone": None,
        "config_hash": config.config_hash, "config": values,
        "raw_rows": len(raw), "cleaned_rows": len(cleaned),
        "valid_rows": int(cleaned["valid"].sum()),
        "flagged_cleaned_rows": int((~cleaned["valid"]).sum()),
        "quality_rows_raw": {name: int(flags[name].sum()) for name in QUALITY_FLAGS},
        "exact_duplicate_extra_rows": int((~representative).sum()),
        "timestamp_conflict_rows": int(conflict_mask.sum()),
        "timestamp_conflict_groups": int(parsed[conflict_mask].nunique()),
        "removed_rows": {
            "invalid_timestamp": int(parsed.isna().sum()),
            "timestamp_conflict": int(conflict_mask.sum()),
            "exact_duplicate_nonconflict": int((~representative & ~conflict_mask).sum()),
        },
        "time_start": str(cleaned["timestamp"].min()), "time_end": str(cleaned["timestamp"].max()),
        "cadence": {
            "fit_scope": "sorted unique non-conflicting timestamps strictly before train_end_exclusive; sensor defects do not remove timestamps",
            "train_end_exclusive": str(train_end), "delta0_seconds": delta0,
            "gap_break_seconds": gap_break, "gap_operator": ">",
            "mode_candidates_seconds": modes, "mode_tie_rule": "smallest positive mode",
            "minimum_positive_deltas": 1, "train_deltas": _delta_summary(train_delta),
        },
        "all_deltas_quality_only": _delta_summary(delta),
        "gap_count": int(breaks.sum()), "segment_count": int(cleaned["segment_id"].nunique()),
        "gap_seconds": {
            "total": float(delta[breaks].sum()),
            "max": float(delta[breaks].max()) if breaks.any() else None,
        },
        "estimated_missing_ticks": int(absent.sum()),
        "september_1_rows_retained": int(cleaned["timestamp"].dt.normalize().eq(pd.Timestamp("2020-09-01")).sum()),
        "columns": column_stats,
        "schema": {name: str(dtype) for name, dtype in cleaned.dtypes.items()},
        "splits": {
            name: {"rows": len(part), "valid_rows": int(part["valid"].sum()),
                   "start": str(part["timestamp"].min()) if len(part) else None,
                   "end": str(part["timestamp"].max()) if len(part) else None}
            for name in ("train", "validation", "test")
            for part in [cleaned.loc[cleaned["split"] == name]]
        },
    }
    return AuditTables(cleaned, issues, conflicts, duplicates, gaps.reset_index(drop=True), summary)


def _verified_manifest(path: Path) -> dict:
    """Reuse PB02 verification, reconstructing content-derived fields from raw."""
    manifest = json.loads(path.read_text(encoding="utf-8"))
    expected = copy.deepcopy(manifest)
    expected["schema_version"] = 1
    expected["status"] = "completed"
    for info in manifest["files"].values():
        file_path = (path.parent / info["path"]).resolve()
        if file_path.parent != path.parent or Path(info["path"]).name != info["path"]:
            raise AuditError("raw manifest: file paths must stay inside the raw version")
    expected["csv"] = _inspect_csv(path.parent / manifest["files"]["csv"]["path"])
    identity = json.dumps(
        {"schema_version": 1, "files": manifest["files"]},
        sort_keys=True, separators=(",", ":"),
    ).encode()
    expected["dataset_version"] = "sha256-" + hashlib.sha256(identity).hexdigest()
    differs = manifest["files"]["csv"]["sha256"] != REFERENCE_CSV_SHA256
    expected["audit"] = {
        "required": differs,
        "reason": "csv_checksum_differs_from_reference" if differs else None,
        "reference_csv_sha256": REFERENCE_CSV_SHA256,
    }
    _verify_locked(path.parent, expected)
    return manifest


def data_card(summary: dict) -> str:
    """Human-readable quality report; machine-readable metadata lives in Parquet."""
    s = summary
    def compact_deltas(stats: dict) -> str:
        frequent = sorted(
            stats["distribution_seconds"].items(), key=lambda item: (-item[1], float(item[0]))
        )[:5]
        top = ", ".join(f"{seconds}s: {count}" for seconds, count in frequent)
        return (
            f"{stats['count']} deltas; min/median/max: "
            f"{stats['min_seconds']} / {stats['median_seconds']} / {stats['max_seconds']} s; "
            f"quantiles: {json.dumps(stats['quantiles_seconds'])}; "
            f"five most frequent (seconds: count): {top}. "
            "Full distribution is in Parquet metadata."
        )

    lines = [
        "# MetroPT-3 data card — PB03", "",
        f"Raw manifest: `{s['raw_manifest']}`",
        f"Dataset version: `{s['dataset_version']}`",
        f"CSV SHA-256: `{s['csv_sha256']}`",
        f"Config hash: `{s['config_hash']}`", "",
        "## Cleaning and provenance", "",
        f"Raw rows: **{s['raw_rows']}**; cleaned: **{s['cleaned_rows']}**; valid: **{s['valid_rows']}**; retained with sensor flags: **{s['flagged_cleaned_rows']}**.",
        f"Time: {s['time_start']} → {s['time_end']} (original clock, no timezone).",
        f"Timestamp format: `{s['timestamp_format']}`. raw_row_id = zero-based CSV record position, scoped by dataset version; original index retained.",
        "Exact duplicates compare parsed timestamp + all original sensor tokens, excluding the provenance index. Keep smallest raw_row_id; duplicate_count includes the representative. duplicate_rows.parquet maps every involved raw_row_id, including conflict groups.",
        f"Exact duplicate extra rows (including conflicts): {s['exact_duplicate_extra_rows']}; conflicting timestamps: {s['timestamp_conflict_groups']} groups / {s['timestamp_conflict_rows']} raw rows.",
        f"Disjoint removal reasons: `{json.dumps(s['removed_rows'], sort_keys=True)}`.",
        f"Raw row flags (may overlap): `{json.dumps(s['quality_rows_raw'], sort_keys=True)}`.",
        "Unparseable timestamps are excluded from cleaned and retained verbatim in issues.parquet. Every conflicting raw row is retained in conflicts.parquet. Sensor defects remain in cleaned with valid=false; no fill, resampling or silent row removal.",
        "Missing cells mean blank/whitespace sensor tokens. Nonempty unparseable tokens (including NA/NaN/null) are invalid_numeric. Infinity is separate. Digital domain is {0, 1}; finite analog extremes and negative pressures are preserved.",
        f"2020-09-01 retained rows: **{s['september_1_rows_retained']}**. No z-score/IQR filtering.", "",
        "## Cadence and absent timestamps", "",
        f"delta0 = **{s['cadence']['delta0_seconds']} s**; gap_break = **{s['cadence']['gap_break_seconds']} s**; a gap requires delta **>** gap_break. Segment IDs start at 0.",
        f"Fit scope: {s['cadence']['fit_scope']}. Boundary: {s['cadence']['train_end_exclusive']}.",
        f"Minimum: one positive train delta; tied modes choose the smallest positive mode. Candidates: {s['cadence']['mode_candidates_seconds']}.",
        "Train deltas: " + compact_deltas(s['cadence']['train_deltas']),
        "All-file deltas (quality audit only): " + compact_deltas(s['all_deltas_quality_only']),
        f"Gaps: **{s['gap_count']}**; segments: **{s['segment_count']}**; estimated absent cadence ticks: **{s['estimated_missing_ticks']}**.",
        f"Total gap duration: {s['gap_seconds']['total']} s; longest gap: {s['gap_seconds']['max']} s.",
        "Absent ticks are sum(max(ceil(delta/delta0)-1, 0)), an estimate on the cleaned timeline, distinct from missing cells. No regular timestamp grid is asserted. gaps.parquet records only segment breaks, when present. Splits do not reset segment_id; downstream windows must enforce both split and segment boundaries.", "",
        "## Calendar split summary (before PB05 window masks/purge)", "",
        "| Split | Rows | Valid rows | First | Last |", "| --- | ---: | ---: | --- | --- |",
    ]
    for name, part in s["splits"].items():
        lines.append(f"| {name} | {part['rows']} | {part['valid_rows']} | {part['start']} | {part['end']} |")
    lines += [
        "", "## Sensor quality", "",
        "All-file columns below are quality diagnostics only. Min/median/max describe finite raw train cells (before deduplication/conflict removal), not fitted preprocessing. Model/feature decisions must use train only.",
        "", "| Sensor | Missing | Invalid numeric | Infinity | Outside digital domain | Unique numeric | Train finite min / median / max |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for name, col in s["columns"].items():
        t = col["train_finite"]
        lines.append(f"| {name} | {col['missing_cells']} | {col['invalid_numeric_cells']} | {col['infinity_cells']} | {col['invalid_digital_cells']} | {col['unique_numeric_values']} | {t['min']} / {t['median']} / {t['max']} |")
    lines += ["", "## Cleaned schema", "", "```json", json.dumps(s["schema"], indent=2), "```", "", "Config snapshot, raw provenance and these statistics are stored in cleaned.parquet attrs['audit']. Optional detail tables are written only when nonempty.", ""]
    return "\n".join(lines)


def audit_dataset(manifest_path: str | Path, *, config: ProjectConfig, output_dir: str | Path) -> dict:
    """Verify an explicit raw version and write one reviewable audit directory."""
    manifest_path = Path(manifest_path).expanduser().resolve()
    output = Path(output_dir).expanduser().resolve()
    try:
        if output.exists():
            raise AuditError(f"output already exists: {output}; choose a new audit directory")
        manifest = _verified_manifest(manifest_path)
        header = manifest["csv"]["columns"]
        raw = pd.read_csv(
            manifest_path.parent / manifest["files"]["csv"]["path"],
            names=header, header=0, dtype=pd.StringDtype(storage="pyarrow"),
            keep_default_na=False, na_filter=False, skip_blank_lines=False, encoding="utf-8-sig",
        )
        tables = audit_rows(raw, config)
        tables.summary.update({
            "raw_manifest": str(manifest_path),
            "dataset_version": manifest["dataset_version"],
            "csv_sha256": manifest["files"]["csv"]["sha256"],
        })
        # Fail before publishing if metadata is not standard JSON.
        json.dumps(tables.summary, allow_nan=False)
        tables.cleaned.attrs["audit"] = tables.summary
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".audit-", dir=output.parent) as work:
            staging = Path(work) / "result"
            staging.mkdir()
            tables.cleaned.to_parquet(staging / "cleaned.parquet", index=False)
            for name in ("issues", "conflicts", "duplicate_rows", "gaps"):
                frame = getattr(tables, name)
                if len(frame):
                    frame.to_parquet(staging / f"{name}.parquet", index=False)
            (staging / "data_card.md").write_text(data_card(tables.summary), encoding="utf-8")
            staging.rename(output)
        return {
            "status": "completed", "output": str(output),
            "data_card": str(output / "data_card.md"), "cleaned": str(output / "cleaned.parquet"),
            "raw_rows": tables.summary["raw_rows"], "cleaned_rows": tables.summary["cleaned_rows"],
            "delta0_seconds": tables.summary["cadence"]["delta0_seconds"],
            "gap_break_seconds": tables.summary["cadence"]["gap_break_seconds"],
        }
    except AuditError:
        raise
    except (OSError, ValueError, TypeError, KeyError, AttributeError, csv.Error) as exc:
        raise AuditError(f"audit failed: {exc}") from exc
