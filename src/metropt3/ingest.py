"""Verify MetroPT-3 packages and atomically publish immutable raw versions."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import stat
import tempfile
import zipfile
import zlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from http.client import HTTPException
from pathlib import Path, PurePosixPath
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen


OFFICIAL_PACKAGE_URL = (
    "https://archive.ics.uci.edu/static/public/791/metropt%2B3%2Bdataset.zip"
)
REFERENCE_CSV_SHA256 = "db30ccb4ea402e3c8bf2c99db06e288d4f2a772f6928f9dbe26a920d69793e24"
RAW_SCHEMA_VERSION = 1
ANALOG_COLUMNS = (
    "TP2", "TP3", "H1", "DV_pressure", "Reservoirs", "Oil_temperature", "Motor_current",
)
DIGITAL_COLUMNS = (
    "COMP", "DV_eletric", "Towers", "MPG", "LPS", "Pressure_switch", "Oil_level",
    "Caudal_impulses",
)
SENSOR_COLUMNS = ANALOG_COLUMNS + DIGITAL_COLUMNS
INDEX_HEADERS = ("", "index", "Unnamed: 0")
CHUNK_SIZE = 1024 * 1024


class IngestError(ValueError):
    """A package cannot be verified or a locked raw version has changed."""


@dataclass(frozen=True)
class IngestResult:
    manifest_path: Path
    dataset_version: str
    reused: bool
    audit_required: bool

    def as_dict(self) -> dict:
        return {
            "status": "completed",
            "manifest": str(self.manifest_path),
            "dataset_version": self.dataset_version,
            "reused": self.reused,
            "audit_required": self.audit_required,
            "audit_reason": "csv_checksum_differs_from_reference" if self.audit_required else None,
        }


def _file_info(path: Path) -> dict:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
            digest.update(chunk)
            size += len(chunk)
    return {"bytes": size, "sha256": digest.hexdigest()}


def _receive(source: str, destination: Path) -> dict:
    parsed = urlparse(source)
    if parsed.scheme in ("http", "https"):
        with urlopen(source, timeout=60) as response, destination.open("wb") as output:
            if response.status != 200:
                raise IngestError(f"download: expected HTTP 200, got {response.status}")
            expected = response.headers.get("Content-Length")
            shutil.copyfileobj(response, output, CHUNK_SIZE)
            resolved_url = response.geturl()
        if expected is not None and destination.stat().st_size != int(expected):
            raise IngestError("download: incomplete response (Content-Length mismatch)")
        return {"kind": "url", "location": source, "resolved_url": resolved_url}
    local = Path(source).expanduser().resolve()
    with local.open("rb") as incoming, destination.open("wb") as output:
        shutil.copyfileobj(incoming, output, CHUNK_SIZE)
    return {"kind": "local", "location": local.as_uri(), "resolved_url": None}


def _extract(package: Path, destination: Path) -> dict:
    with zipfile.ZipFile(package) as archive:
        members: dict[str, list[zipfile.ZipInfo]] = {"csv": [], "pdf": []}
        for member in archive.infolist():
            path = PurePosixPath(member.filename)
            if (
                path.is_absolute() or ".." in path.parts or "\\" in member.filename
                or ":" in member.filename
                or stat.S_ISLNK(member.external_attr >> 16)
            ):
                raise IngestError(f"ZIP: unsafe member {member.filename!r}")
            if not member.is_dir() and path.suffix.lower().lstrip(".") in members:
                members[path.suffix.lower().lstrip(".")].append(member)
        for role, found in members.items():
            if len(found) != 1:
                raise IngestError(f"ZIP: expected exactly one {role.upper()}, found {len(found)}")
        corrupt = archive.testzip()
        if corrupt is not None:
            raise IngestError(f"ZIP: CRC check failed for {corrupt!r}")
        files = {}
        for role, found in members.items():
            member = found[0]
            name = PurePosixPath(member.filename).name
            target = destination / name
            with archive.open(member) as incoming, target.open("xb") as output:
                shutil.copyfileobj(incoming, output, CHUNK_SIZE)
            files[role] = {
                "path": name, "archive_member": member.filename, **_file_info(target),
            }
        return files


def _inspect_csv(path: Path) -> dict:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        header = next(reader, None)
        if header is None:
            raise IngestError("CSV: missing header")
        required = {"timestamp", *SENSOR_COLUMNS}
        missing = sorted(required - set(header))
        extras = [name for name in header if name not in required]
        if missing or len(header) != 17 or len(set(header)) != len(header):
            raise IngestError(
                f"CSV header: missing={missing!r}, non-sensor columns={extras!r}; "
                "expected timestamp, 15 sensors and one original index column"
            )
        if len(extras) != 1 or extras[0] not in INDEX_HEADERS:
            raise IngestError(f"CSV header: unsupported original index column {extras!r}")
        count = 0
        for count, row in enumerate(reader, start=1):
            if len(row) != len(header):
                raise IngestError(f"CSV: data record {count} has {len(row)} fields, expected 17")
        if count == 0:
            raise IngestError("CSV: no data records")
    return {
        "columns": header,
        "index_column": extras[0],
        "time_column": "timestamp",
        "analog_columns": list(ANALOG_COLUMNS),
        "digital_columns": list(DIGITAL_COLUMNS),
        "feature_columns": list(SENSOR_COLUMNS),
        "row_count": count,
        "raw_row_id": {
            "base": 0,
            "rule": "zero-based CSV data-record position, excluding header; scoped by dataset_version",
            "materialized_in_raw": False,
        },
    }


def _inspect_pdf(path: Path) -> None:
    with path.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            raise IngestError("PDF: missing PDF signature")
        stream.seek(max(0, path.stat().st_size - 1024))
        if b"%%EOF" not in stream.read():
            raise IngestError("PDF: missing EOF marker (possibly truncated)")


def _manifest_fields(value: object, fields: set[str], prefix: str = "") -> None:
    if not isinstance(value, dict):
        raise IngestError(f"raw manifest: {prefix or 'root'} must be an object")
    for field in sorted(fields - value.keys()):
        raise IngestError(f"raw manifest: missing {prefix}{field}")
    for field in sorted(value.keys() - fields):
        raise IngestError(f"raw manifest: unknown field {prefix}{field}")


def _is_http_url(value: object) -> bool:
    if not isinstance(value, str) or any(char.isspace() for char in value):
        return False
    try:
        parsed = urlparse(value)
        return parsed.scheme in ("http", "https") and bool(parsed.hostname)
    except ValueError:
        return False


def _validate_provenance(manifest: dict) -> None:
    """Validate original receipt metadata without comparing it to a new receipt."""
    source = manifest["source"]
    _manifest_fields(source, {"kind", "location", "resolved_url", "url"}, "source.")
    if source["kind"] not in ("local", "url"):
        raise IngestError("raw manifest: source.kind must be local or url")
    if source["kind"] == "url":
        for field in ("location", "resolved_url", "url"):
            if not _is_http_url(source[field]):
                raise IngestError(f"raw manifest: source.{field} must be an absolute HTTP(S) URL")
    else:
        location = source["location"]
        if not isinstance(location, str):
            raise IngestError("raw manifest: source.location must be an absolute file URI")
        parsed = urlparse(location)
        if parsed.scheme != "file" or not parsed.path.startswith("/"):
            raise IngestError("raw manifest: source.location must be an absolute file URI")
        if source["resolved_url"] is not None:
            raise IngestError("raw manifest: source.resolved_url must be null for local input")
        if source["url"] is not None and not _is_http_url(source["url"]):
            raise IngestError("raw manifest: source.url must be null or an absolute HTTP(S) URL")
    downloaded_at = manifest["downloaded_at"]
    try:
        if not isinstance(downloaded_at, str):
            raise ValueError("expected a string")
        if datetime.fromisoformat(downloaded_at).utcoffset() != timedelta(0):
            raise ValueError("expected UTC offset")
    except ValueError as exc:
        raise IngestError("raw manifest: downloaded_at must be an ISO timestamp in UTC") from exc
    package = manifest["package"]
    _manifest_fields(package, {"bytes", "sha256"}, "package.")
    if type(package["bytes"]) is not int or package["bytes"] <= 0:
        raise IngestError("raw manifest: package.bytes must be a positive integer")
    digest = package["sha256"]
    if not isinstance(digest, str) or len(digest) != 64 or set(digest) - set("0123456789abcdef"):
        raise IngestError("raw manifest: package.sha256 must be a lowercase SHA-256 digest")


def _verify_locked(target: Path, expected: dict) -> None:
    manifest_path = target / "raw_manifest.json"
    if target.is_symlink() or manifest_path.is_symlink():
        raise IngestError(f"locked raw version contains a symlink: {target}")
    actual = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(actual, dict) or type(actual.get("schema_version")) is not int:
        raise IngestError("locked raw manifest: invalid schema; refusing overwrite")
    _manifest_fields(actual, set(expected))
    _validate_provenance(actual)
    for field in ("schema_version", "status", "dataset_version", "files", "csv", "audit"):
        # JSON comparison also rejects nested bool/int and int/float substitutions.
        if json.dumps(actual[field], sort_keys=True) != json.dumps(expected[field], sort_keys=True):
            raise IngestError(f"locked raw manifest mismatch: {field}; refusing overwrite")
    for info in expected["files"].values():
        path = target / info["path"]
        if path.is_symlink() or _file_info(path) != {k: info[k] for k in ("bytes", "sha256")}:
            raise IngestError(f"locked raw file changed: {path}; refusing overwrite")


def ingest_package(
    source: str | Path = OFFICIAL_PACKAGE_URL,
    *,
    raw_dir: str | Path,
    source_url: str | None = None,
) -> IngestResult:
    """Receive a ZIP, verify its bytes/schema, then publish one content version.

    Each version has its own raw_manifest.json. Reimporting identical CSV/PDF
    files verifies and returns the existing version without modifying it.
    A checksum mismatch is accepted as a new version requiring a PB03 audit.
    """
    raw = Path(raw_dir).expanduser().resolve()
    try:
        if source_url is not None and not _is_http_url(source_url):
            raise IngestError("source_url: expected an explicit HTTP(S) provenance URL")
        raw.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".ingest-", dir=raw) as work:
            staging = Path(work)
            candidate = staging / "version"
            candidate.mkdir()
            package = staging / "package.zip"
            provenance = _receive(str(source), package)
            provenance["url"] = source_url or (
                provenance["location"] if provenance["kind"] == "url" else None
            )
            files = _extract(package, candidate)
            csv_info = _inspect_csv(candidate / files["csv"]["path"])
            _inspect_pdf(candidate / files["pdf"]["path"])
            identity = json.dumps(
                {"schema_version": RAW_SCHEMA_VERSION, "files": files},
                sort_keys=True, separators=(",", ":"),
            ).encode("utf-8")
            version = "sha256-" + hashlib.sha256(identity).hexdigest()
            audit_required = files["csv"]["sha256"] != REFERENCE_CSV_SHA256
            manifest = {
                "schema_version": RAW_SCHEMA_VERSION,
                "status": "completed",
                "dataset_version": version,
                "source": provenance,
                "downloaded_at": datetime.now(timezone.utc).isoformat(),
                "package": _file_info(package),
                "files": files,
                "csv": csv_info,
                "audit": {
                    "required": audit_required,
                    "reason": "csv_checksum_differs_from_reference" if audit_required else None,
                    "reference_csv_sha256": REFERENCE_CSV_SHA256,
                },
            }
            _validate_provenance(manifest)
            target = raw / version
            reused = target.exists()
            if reused:
                _verify_locked(target, manifest)
            else:
                (candidate / "raw_manifest.json").write_text(
                    json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
                )
                try:
                    candidate.rename(target)
                except OSError:
                    if not target.exists():
                        raise
                    _verify_locked(target, manifest)
                    reused = True
            return IngestResult(target / "raw_manifest.json", version, reused, audit_required)
    except IngestError:
        raise
    except (
        OSError, URLError, HTTPException, zipfile.BadZipFile, zipfile.LargeZipFile,
        UnicodeError, csv.Error, ValueError, EOFError, RuntimeError, zlib.error,
    ) as exc:
        raise IngestError(f"ingest failed: {exc}") from exc
