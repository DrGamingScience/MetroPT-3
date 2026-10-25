"""PB03 acceptance: quality lineage, strict gaps and train-only cadence."""

import csv
import io
import json
import zipfile

import numpy as np
import pandas as pd
import pytest

from metropt3.audit import AuditError, audit_dataset, audit_rows
from metropt3.cli import main
from metropt3.config import load_config
from metropt3.ingest import SENSOR_COLUMNS, ingest_package


HEADER = ["", "timestamp", *SENSOR_COLUMNS]


def row(timestamp, *, index="original-index", **changes):
    return [index, timestamp, *[str(changes.get(name, 1)) for name in SENSOR_COLUMNS]]


def frame(rows):
    return pd.DataFrame(rows, columns=HEADER, dtype=pd.StringDtype(storage="pyarrow"))


@pytest.fixture
def config(config_values, write_config):
    return load_config(write_config(config_values))


def base_rows():
    return [row(f"2020-02-01 00:00:{second:02d}") for second in (0, 10, 20)]


def test_quality_flags_duplicates_conflicts_and_raw_lineage(config):
    rows = base_rows() + [
        row("broken timestamp"),                                      # 3
        row("2020-02-01 00:00:30", TP2="broken"),                     # 4
        row("2020-02-01 00:00:10", index="another index"),            # 5 exact copy of 1
        row("2020-02-01 00:00:40", TP2=5),                            # 6 conflict
        row("2020-02-01 00:00:40", TP2=6),                            # 7 conflict
        row("2020-02-01 00:00:40", TP2=5, index="third index"),       # 8 exact copy in conflict
        row("2020-02-01 00:00:50", TP3="  ", H1="inf", COMP=2),     # 9 sensor issues
        row("2020-02-01 00:01:00", TP2="NaN", TP3="null", H1="NA"), # 10 nonblank invalids
    ]
    tables = audit_rows(frame(rows), config)
    c = tables.cleaned.set_index("raw_row_id")
    assert list(c.index) == [0, 1, 2, 4, 9, 10]
    assert c.loc[1, "duplicate_count"] == 2
    assert c.loc[4, "invalid_numeric"] and not c.loc[4, "valid"]
    assert np.isnan(c.loc[4, "TP2"])
    assert c.loc[9, "missing_cell"] and c.loc[9, "infinity"] and c.loc[9, "invalid_digital"]
    assert np.isinf(c.loc[9, "H1"])
    assert set(tables.issues.raw_row_id) == {3, 4, 9, 10}
    assert tables.issues.set_index("raw_row_id").loc[3, "timestamp"] == "broken timestamp"
    assert tables.issues.set_index("raw_row_id").loc[4, "TP2"] == "broken"
    assert set(tables.conflicts.raw_row_id) == {6, 7, 8}
    mapping = tables.duplicate_rows.set_index("raw_row_id")
    assert mapping.loc[5, "representative_raw_row_id"] == 1
    assert mapping.loc[8, "representative_raw_row_id"] == 6
    assert tables.summary["exact_duplicate_extra_rows"] == 2
    assert tables.summary["timestamp_conflict_groups"] == 1
    assert tables.summary["raw_rows"] - sum(tables.summary["removed_rows"].values()) == len(c)
    stats = tables.summary["columns"]
    assert stats["TP3"]["missing_cells"] == 1
    assert stats["TP2"]["invalid_numeric_cells"] == 2
    assert stats["H1"]["infinity_cells"] == 1
    assert stats["COMP"]["invalid_digital_cells"] == 1
    assert c["timestamp"].dt.tz is None


def test_strict_gap_boundary_and_stable_timestamp_order(config):
    rows = base_rows() + [row("2020-02-01 00:00:50"), row("2020-02-01 00:01:21")]
    tables = audit_rows(frame(rows[::-1]), config)
    assert tables.summary["cadence"]["delta0_seconds"] == 10
    assert tables.summary["cadence"]["gap_break_seconds"] == 30
    assert tables.cleaned.raw_row_id.tolist() == [4, 3, 2, 1, 0]
    assert tables.cleaned.segment_id.tolist() == [0, 0, 0, 0, 1]
    assert tables.gaps.delta_seconds.tolist() == [31]
    assert tables.gaps.previous_raw_row_id.tolist() == [1]
    assert tables.gaps.raw_row_id.tolist() == [0]
    assert tables.summary["cadence"]["train_deltas"]["median_seconds"] == 20


def test_test_timestamp_and_sensor_distribution_cannot_change_train_fit(config):
    first = audit_rows(frame(base_rows() + [row(f"2020-05-01 00:00:{s:02d}", TP2=1e12) for s in (0, 1, 2, 3, 4, 5)]), config)
    second = audit_rows(frame(base_rows() + [row("2020-09-01 00:00:00", TP2=-1e12)]), config)
    assert first.summary["cadence"] == second.summary["cadence"]
    assert first.summary["columns"]["TP2"]["train_finite"] == second.summary["columns"]["TP2"]["train_finite"]
    assert first.summary["cadence"]["delta0_seconds"] == 10


def test_extremes_negative_pressure_and_september_1_survive(config):
    tables = audit_rows(frame(base_rows() + [row("2020-09-01 12:00:00", TP2=-9999, DV_pressure=-0.25, Motor_current=1e100)]), config)
    last = tables.cleaned.iloc[-1]
    assert last["valid"]
    assert last.TP2 == -9999 and last.DV_pressure == -0.25 and last.Motor_current == 1e100
    assert tables.summary["september_1_rows_retained"] == 1


def test_mode_tie_has_documented_deterministic_rule(config):
    tables = audit_rows(frame([row("2020-02-01 00:00:00"), row("2020-02-01 00:00:20"), row("2020-02-01 00:00:30")]), config)
    assert tables.summary["cadence"]["mode_candidates_seconds"] == [10, 20]
    assert tables.summary["cadence"]["delta0_seconds"] == 10
    assert tables.summary["cadence"]["mode_tie_rule"] == "smallest positive mode"


@pytest.mark.parametrize("rows", [
    [row("2020-03-01 00:00:00"), row("2020-03-01 00:00:10")],
    [row("2020-02-01 00:00:00"), row("2020-05-01 00:00:10"), row("2020-05-01 00:00:20")],
    [row("2020-02-01 00:00:00"), row("2020-02-01 00:00:00")],
])
def test_insufficient_train_deltas_stop_without_fallback(config, rows):
    with pytest.raises(AuditError, match="train cadence.*no validation/test fallback"):
        audit_rows(frame(rows), config)


def test_exclusive_split_boundaries_and_cross_boundary_delta_not_fit(config):
    tables = audit_rows(frame([
        row("2020-02-29 23:59:40"), row("2020-02-29 23:59:50"),
        row("2020-03-01 00:00:00"), row("2020-05-01 00:00:00"),
    ]), config)
    assert tables.cleaned.split.tolist() == ["train", "train", "validation", "test"]
    assert tables.summary["cadence"]["train_deltas"]["count"] == 1


def test_invalid_sensor_tokens_do_not_hide_conflicting_observations(config):
    tables = audit_rows(frame(base_rows() + [row("2020-02-01 00:00:30", TP2="bad-a"), row("2020-02-01 00:00:30", TP2="bad-b")]), config)
    assert len(tables.conflicts) == 2
    assert set(tables.conflicts.TP2) == {"bad-a", "bad-b"}
    assert tables.summary["exact_duplicate_extra_rows"] == 0


def test_timestamp_format_is_explicit_and_never_infers_timezone_or_dayfirst(config):
    tables = audit_rows(frame(base_rows() + [row(s) for s in (
        "01/09/2020 00:00:00", "2020-09-01T00:00:00Z", "2020-2-1 00:00:30", "2020-02-30 00:00:00", "",
    )]), config)
    assert tables.summary["quality_rows_raw"]["invalid_timestamp"] == 5
    assert len(tables.issues) == 5


@pytest.mark.parametrize("invalid,valid", [
    ("2020-02-01 00:00:60", "2020-02-01 00:01:00"),
    ("2020-02-01 00:00:61", "2020-02-01 00:01:01"),
    ("2020-02-01 00:60:00", "2020-02-01 01:00:00"),
    ("2020-02-01 24:00:00", "2020-02-02 00:00:00"),
])
def test_out_of_range_clock_cannot_normalize_into_valid_row_conflict(config, invalid, valid):
    tables = audit_rows(frame(base_rows() + [
        row(invalid, TP2=2),
        row(valid, TP2=3),
    ]), config)
    assert tables.cleaned.raw_row_id.tolist() == [0, 1, 2, 4]
    kept = tables.cleaned.set_index("raw_row_id").loc[4]
    assert kept.timestamp == pd.Timestamp(valid) and kept.TP2 == 3 and kept.valid
    assert tables.issues.raw_row_id.tolist() == [3]
    rejected = tables.issues.iloc[0]
    assert rejected.timestamp == invalid and rejected.invalid_timestamp
    assert pd.isna(rejected.parsed_timestamp) and not rejected.timestamp_conflict
    assert tables.conflicts.empty and tables.duplicate_rows.empty
    assert tables.summary["quality_rows_raw"]["invalid_timestamp"] == 1
    assert tables.summary["removed_rows"]["invalid_timestamp"] == 1
    assert tables.summary["timestamp_conflict_rows"] == 0


@pytest.fixture
def locked_raw(tmp_path):
    def make(rows):
        stream = io.StringIO(newline="")
        writer = csv.writer(stream)
        writer.writerow(HEADER)
        writer.writerows(rows)
        package = tmp_path / "source.zip"
        with zipfile.ZipFile(package, "w") as archive:
            archive.writestr("Metro.csv", stream.getvalue())
            archive.writestr("description.pdf", b"%PDF-1.4\nfixture\n%%EOF\n")
        return ingest_package(package, raw_dir=tmp_path / "raw").manifest_path
    return make


def test_cli_real_io_parquet_metadata_and_immutable_raw(config, locked_raw, tmp_path, capsys):
    manifest = locked_raw(base_rows() + [row("invalid\nCSV record"), row("2020-02-01 00:00:10"), row("2020-02-01 00:01:00", TP2="bad")])
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in manifest.parent.iterdir()}
    output = tmp_path / "audit"
    assert main(["audit", "--config", str(config.source), "--manifest", str(manifest), "--output", str(output)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "completed"
    cleaned = pd.read_parquet(result["cleaned"])
    assert cleaned.attrs["audit"]["dataset_version"] == json.loads(manifest.read_text())["dataset_version"]
    assert cleaned.attrs["audit"]["config_hash"] == config.config_hash
    assert cleaned.attrs["audit"]["cadence"]["delta0_seconds"] == 10
    assert cleaned.raw_row_id.tolist() == [0, 1, 2, 5]
    assert cleaned[""].tolist() == ["original-index"] * 4
    assert pd.read_parquet(output / "issues.parquet").raw_row_id.tolist() == [3, 5]
    assert pd.read_parquet(output / "issues.parquet").iloc[0].timestamp == "invalid\nCSV record"
    assert "smallest positive mode" in (output / "data_card.md").read_text(encoding="utf-8")
    assert (output / "duplicate_rows.parquet").exists() and (output / "gaps.parquet").exists()
    assert not (output / "conflicts.parquet").exists()
    assert before == {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in manifest.parent.iterdir()}
    with pytest.raises(SystemExit) as exc:
        main(["audit", "--config", str(config.source), "--manifest", str(manifest), "--output", str(output)])
    assert exc.value.code == 2
    assert "already exists" in capsys.readouterr().err


def test_default_output_resolves_from_config(config, locked_raw, capsys):
    manifest = locked_raw(base_rows())
    assert main(["audit", "--config", str(config.source), "--manifest", str(manifest)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["output"] == str(config.resolve_path("interim") / "pb03-audit")


@pytest.mark.parametrize("defect", ["checksum", "row_count", "version", "status", "missing_source", "path_escape", "bad_json"])
def test_audit_rejects_invalid_raw_without_output(config, locked_raw, tmp_path, capsys, defect):
    manifest = locked_raw(base_rows())
    receipt = json.loads(manifest.read_text())
    if defect == "checksum":
        with (manifest.parent / receipt["files"]["csv"]["path"]).open("a") as stream:
            stream.write("\n")
    elif defect == "row_count":
        receipt["csv"]["row_count"] += 1
    elif defect == "version":
        receipt["dataset_version"] = "wrong"
    elif defect == "status":
        receipt["status"] = "incomplete"
    elif defect == "missing_source":
        del receipt["source"]
    elif defect == "path_escape":
        receipt["files"]["csv"]["path"] = "../outside.csv"
    if defect != "checksum":
        manifest.write_text("{" if defect == "bad_json" else json.dumps(receipt), encoding="utf-8")
    output = tmp_path / "audit"
    with pytest.raises(SystemExit) as exc:
        main(["audit", "--config", str(config.source), "--manifest", str(manifest), "--output", str(output)])
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert not captured.out and "Traceback" not in captured.err
    assert not output.exists()


def test_fit_failure_never_publishes_output(config, locked_raw, tmp_path):
    manifest = locked_raw([row("2020-05-01 00:00:00"), row("2020-05-01 00:00:10")])
    with pytest.raises(AuditError, match="train cadence"):
        audit_dataset(manifest, config=config, output_dir=tmp_path / "audit")
    assert not (tmp_path / "audit").exists()


def test_conflicting_raw_rows_survive_parquet_roundtrip(config, locked_raw, tmp_path):
    manifest = locked_raw(base_rows() + [
        row("2020-02-01 00:00:30", TP2="bad-a"),
        row("2020-02-01 00:00:30", TP2="bad-b"),
        row("2020-02-01 00:00:30", TP2="bad-a", index="copy"),
    ])
    output = tmp_path / "audit"
    audit_dataset(manifest, config=config, output_dir=output)
    conflicts = pd.read_parquet(output / "conflicts.parquet")
    assert conflicts.raw_row_id.tolist() == [3, 4, 5]
    assert conflicts.timestamp_conflict.all() and conflicts.invalid_numeric.all()
    assert conflicts.TP2.tolist() == ["bad-a", "bad-b", "bad-a"]
    assert pd.read_parquet(output / "cleaned.parquet").raw_row_id.tolist() == [0, 1, 2]


def test_write_failure_does_not_publish_partial_audit(config, locked_raw, tmp_path, monkeypatch):
    manifest = locked_raw(base_rows())
    def fail(*args, **kwargs):
        raise OSError("disk full")
    monkeypatch.setattr(pd.DataFrame, "to_parquet", fail)
    with pytest.raises(AuditError, match="disk full"):
        audit_dataset(manifest, config=config, output_dir=tmp_path / "audit")
    assert not (tmp_path / "audit").exists()
    assert not list(tmp_path.glob(".audit-*"))


def test_nonstandard_gap_multiplier_is_not_silently_ignored(config_values, write_config):
    config_values["quality"]["gap_multiplier"] = 2
    config = load_config(write_config(config_values))
    with pytest.raises(AuditError, match="gap_multiplier.*requires 3"):
        audit_rows(frame(base_rows()), config)
