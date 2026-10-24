"""PB02 acceptance checks use small synthetic packages, never the full dataset."""

import csv
import hashlib
import io
import json
import zipfile
from concurrent.futures import ThreadPoolExecutor
from http.client import IncompleteRead
from pathlib import Path

import pytest

import metropt3.ingest as module
from metropt3.cli import main
from metropt3.ingest import IngestError, SENSOR_COLUMNS, ingest_package


HEADER = ["", "timestamp", *SENSOR_COLUMNS]
PDF = b"%PDF-1.4\nsynthetic description fixture\n%%EOF\n"


def csv_bytes(header=None, rows=None):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(HEADER if header is None else header)
    writer.writerows(rows if rows is not None else [
        [99, "2020-02-01 00:00:00", *range(15)],
        [42, "2020-02-01 00:00:10", *range(15)],
    ])
    return stream.getvalue().encode()


@pytest.fixture
def package(tmp_path):
    def make(*, csv_data=None, pdf_data=PDF, name="source.zip", extra=None):
        path = tmp_path / name
        with zipfile.ZipFile(path, "w") as archive:
            if csv_data is not False:
                archive.writestr("nested/Metro.csv", csv_bytes() if csv_data is None else csv_data)
            if pdf_data is not False:
                archive.writestr("nested/Description.pdf", pdf_data)
            for member, contents in (extra or {}).items():
                archive.writestr(member, contents)
        return path
    return make


def read_manifest(result):
    return json.loads(result.manifest_path.read_text(encoding="utf-8"))


def test_preserves_bytes_header_and_records_measured_provenance(package, tmp_path):
    source = package()
    result = ingest_package(source, raw_dir=tmp_path / "raw", source_url="https://example.org/source.zip")
    manifest = read_manifest(result)
    assert manifest["status"] == "completed"
    assert manifest["schema_version"] == 1
    assert manifest["source"]["location"] == source.as_uri()
    assert manifest["source"]["url"] == "https://example.org/source.zip"
    assert manifest["downloaded_at"].endswith("+00:00")
    assert manifest["csv"]["columns"] == HEADER
    assert manifest["csv"]["feature_columns"] == list(SENSOR_COLUMNS)
    assert manifest["csv"]["row_count"] == 2
    assert manifest["csv"]["index_column"] == ""
    assert manifest["csv"]["raw_row_id"]["base"] == 0
    assert manifest["csv"]["raw_row_id"]["materialized_in_raw"] is False
    for role, original in (("csv", csv_bytes()), ("pdf", PDF)):
        info = manifest["files"][role]
        assert (result.manifest_path.parent / info["path"]).read_bytes() == original
        assert info["bytes"] == len(original)
        assert info["sha256"] == hashlib.sha256(original).hexdigest()
    assert result.audit_required is True
    assert manifest["audit"]["reason"] == "csv_checksum_differs_from_reference"


def test_idempotence_preserves_files_manifest_and_timestamp(package, tmp_path):
    raw = tmp_path / "raw"
    source = package()
    first = ingest_package(source, raw_dir=raw)
    snapshot = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in first.manifest_path.parent.iterdir()}
    # Different ZIP metadata and extra packaging files do not change CSV/PDF identity.
    repackaged = package(name="repacked.zip", extra={"README.txt": "different ZIP bytes"})
    second = ingest_package(repackaged, raw_dir=raw)
    assert first.reused is False and second.reused is True
    assert second.dataset_version == first.dataset_version
    assert list(raw.iterdir()) == [first.manifest_path.parent]
    assert snapshot == {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in first.manifest_path.parent.iterdir()}


def test_changed_csv_creates_auditable_version_without_touching_old(package, tmp_path):
    raw = tmp_path / "raw"
    first = ingest_package(package(), raw_dir=raw)
    before = first.manifest_path.read_bytes()
    second = ingest_package(package(csv_data=csv_bytes().replace(b"99,", b"98,")), raw_dir=raw)
    assert first.dataset_version != second.dataset_version
    assert second.audit_required
    assert first.manifest_path.read_bytes() == before
    assert len(list(raw.iterdir())) == 2


def test_changed_description_versions_the_source_package(package, tmp_path):
    raw = tmp_path / "raw"
    first = ingest_package(package(), raw_dir=raw)
    second = ingest_package(package(pdf_data=PDF.replace(b"synthetic", b"updated")), raw_dir=raw)
    assert first.dataset_version != second.dataset_version
    assert read_manifest(first)["files"]["csv"] == read_manifest(second)["files"]["csv"]


def test_row_id_uses_csv_records_in_original_order(package, tmp_path):
    rows = [[9, "value\nwith newline", *range(15)], [2, "unparsed timestamp", *range(15)]]
    original = csv_bytes(rows=rows)
    result = ingest_package(package(csv_data=original), raw_dir=tmp_path / "raw")
    assert read_manifest(result)["csv"]["row_count"] == 2
    assert (result.manifest_path.parent / "Metro.csv").read_bytes() == original


@pytest.mark.parametrize("kwargs,reason", [
    ({"csv_data": False}, "exactly one CSV"),
    ({"pdf_data": False}, "exactly one PDF"),
    ({"pdf_data": b"not a PDF"}, "PDF signature"),
    ({"pdf_data": b"%PDF-1.4\ntruncated"}, "EOF marker"),
    ({"extra": {"other.csv": b"extra"}}, "exactly one CSV"),
    ({"extra": {"../escape.txt": b"escape"}}, "unsafe member"),
    ({"extra": {"C:/escape.txt": b"escape"}}, "unsafe member"),
])
def test_invalid_package_never_publishes_manifest(package, tmp_path, kwargs, reason):
    raw = tmp_path / "raw"
    with pytest.raises(IngestError, match=reason):
        ingest_package(package(**kwargs), raw_dir=raw)
    assert not list(raw.iterdir())


@pytest.mark.parametrize("mutation", ["truncated", "crc", "not_zip"])
def test_corrupt_zip_fails_without_ready_state(package, tmp_path, mutation):
    source = package()
    contents = source.read_bytes()
    if mutation == "truncated":
        contents = contents[:-30]
    elif mutation == "crc":
        contents = contents.replace(b"%PDF-1.4", b"%PDF-1.5")
    else:
        contents = b"not ZIP"
    source.write_bytes(contents)
    raw = tmp_path / "raw"
    with pytest.raises(IngestError):
        ingest_package(source, raw_dir=raw)
    assert not list(raw.iterdir())


@pytest.mark.parametrize("header,reason", [
    ([h.replace("DV_eletric", "DV_electric") for h in HEADER], "DV_eletric"),
    ([h.replace("Towers", "TOWERS") for h in HEADER], "Towers"),
    ([h for h in HEADER if h != "TP2"], "TP2"),
    (HEADER[1:], "original index"),
    (["unexpected_index", *HEADER[1:]], "unsupported original index"),
    ([*HEADER[:-1], "TP2"], "Caudal_impulses"),
])
def test_invalid_header_reports_original_names(package, tmp_path, header, reason):
    raw = tmp_path / "raw"
    with pytest.raises(IngestError, match=reason):
        ingest_package(package(csv_data=csv_bytes(header=header)), raw_dir=raw)
    assert not list(raw.iterdir())


@pytest.mark.parametrize("data,reason", [
    (b"", "missing header"),
    (csv_bytes(rows=[]), "no data records"),
    (csv_bytes(rows=[[1, "timestamp"]]), "data record 1"),
    (csv_bytes() + b'"unclosed', "unexpected end"),
])
def test_incomplete_csv_fails(package, tmp_path, data, reason):
    with pytest.raises(IngestError, match=reason):
        ingest_package(package(csv_data=data), raw_dir=tmp_path / "raw")
    assert not list((tmp_path / "raw").iterdir())


@pytest.mark.parametrize("index", ["index", "Unnamed: 0"])
def test_explicit_index_headers_are_preserved(package, tmp_path, index):
    result = ingest_package(package(csv_data=csv_bytes(header=[index, *HEADER[1:]])), raw_dir=tmp_path / "raw")
    manifest = read_manifest(result)
    assert manifest["csv"]["index_column"] == index
    assert index not in manifest["csv"]["feature_columns"]
    assert "timestamp" not in manifest["csv"]["feature_columns"]


@pytest.mark.parametrize("tamper", ["csv", "manifest", "missing_pdf", "invalid_json", "json_list", "boolean_schema"])
def test_locked_version_tampering_is_not_overwritten(package, tmp_path, tamper):
    source = package()
    raw = tmp_path / "raw"
    first = ingest_package(source, raw_dir=raw)
    if tamper == "csv":
        path = first.manifest_path.parent / "Metro.csv"
        path.write_bytes(b"changed")
    elif tamper == "manifest":
        first.manifest_path.write_text('{"schema_version": 999}', encoding="utf-8")
    elif tamper == "invalid_json":
        first.manifest_path.write_text('{"truncated":', encoding="utf-8")
    elif tamper == "json_list":
        first.manifest_path.write_text('[]', encoding="utf-8")
    elif tamper == "boolean_schema":
        values = read_manifest(first)
        values["schema_version"] = True
        first.manifest_path.write_text(json.dumps(values), encoding="utf-8")
    else:
        (first.manifest_path.parent / "Description.pdf").unlink()
    with pytest.raises(IngestError):
        ingest_package(source, raw_dir=raw)
    assert len(list(raw.iterdir())) == 1
    if tamper == "csv":
        assert path.read_bytes() == b"changed"


def test_matching_reference_does_not_request_checksum_audit(package, tmp_path, monkeypatch):
    monkeypatch.setattr(module, "REFERENCE_CSV_SHA256", hashlib.sha256(csv_bytes()).hexdigest())
    result = ingest_package(package(), raw_dir=tmp_path / "raw")
    assert result.audit_required is False
    assert read_manifest(result)["audit"]["reason"] is None


@pytest.mark.parametrize("fault", [None, "length", "interrupted", "partial_status"])
def test_url_download_verifies_transport_and_preserves_url(package, tmp_path, monkeypatch, fault):
    contents = package().read_bytes()

    class Response(io.BytesIO):
        status = 206 if fault == "partial_status" else 200
        headers = {"Content-Length": str(len(contents) + (1 if fault == "length" else 0))}

        def geturl(self):
            return "https://example.org/redirected.zip"

        def read(self, size=-1):
            if fault == "interrupted":
                raise IncompleteRead(b"partial", len(contents))
            return super().read(size)

    monkeypatch.setattr(module, "urlopen", lambda *args, **kwargs: Response(contents))
    raw = tmp_path / "raw"
    if fault:
        with pytest.raises(IngestError):
            ingest_package("https://example.org/source.zip", raw_dir=raw)
        assert not list(raw.iterdir())
    else:
        result = ingest_package("https://example.org/source.zip", raw_dir=raw)
        assert read_manifest(result)["source"]["url"] == "https://example.org/source.zip"
        assert read_manifest(result)["source"]["resolved_url"].endswith("redirected.zip")


def test_publish_failure_removes_staging_and_leaves_previous_version(package, tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    previous = ingest_package(package(), raw_dir=raw)
    original = previous.manifest_path.read_bytes()

    def fail(*args):
        raise OSError("simulated publish failure")

    monkeypatch.setattr(Path, "rename", fail)
    with pytest.raises(IngestError, match="publish failure"):
        ingest_package(package(csv_data=csv_bytes().replace(b"99,", b"98,")), raw_dir=raw)
    assert list(raw.iterdir()) == [previous.manifest_path.parent]
    assert previous.manifest_path.read_bytes() == original


def test_concurrent_same_package_publishes_one_version(package, tmp_path):
    source = package()
    raw = tmp_path / "raw"
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: ingest_package(source, raw_dir=raw), range(2)))
    assert results[0].dataset_version == results[1].dataset_version
    assert sorted(r.reused for r in results) == [False, True]
    assert len(list(raw.iterdir())) == 1


def test_cli_ingest_local_and_failure(package, config_values, write_config, tmp_path, capsys):
    config = write_config(config_values)
    source = package()
    arguments = ["ingest", "--config", str(config), "--source", str(source)]
    assert main(arguments) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["audit_required"] is True
    assert Path(first["manifest"]).is_file()
    assert main(arguments) == 0
    assert json.loads(capsys.readouterr().out)["reused"] is True
    source.write_bytes(b"truncated")
    with pytest.raises(SystemExit) as error:
        main(arguments)
    assert error.value.code == 2
    captured = capsys.readouterr()
    assert not captured.out
    assert "metropt3:" in captured.err and "Traceback" not in captured.err
