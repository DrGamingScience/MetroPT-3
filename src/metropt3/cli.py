"""CLI entry point. Only commands with implemented behavior are registered."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from metropt3 import __version__
from metropt3.config import ConfigError, load_config
from metropt3.ingest import IngestError, OFFICIAL_PACKAGE_URL, ingest_package


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="metropt3", description="MetroPT-3 reproducible anomaly detection pipeline."
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser(
        "check-config", help="Validate a config and print its hash and resolved paths."
    )
    check.add_argument("--config", type=Path, default=Path("configs/base.yaml"))
    ingest = commands.add_parser("ingest", help="Verify and lock a MetroPT-3 ZIP package.")
    ingest.add_argument("--config", type=Path, default=Path("configs/base.yaml"))
    ingest.add_argument("--source", default=OFFICIAL_PACKAGE_URL, help="Package URL or local ZIP path.")
    ingest.add_argument("--source-url", help="Explicit original URL for a local package, if known.")
    audit = commands.add_parser("audit", help="Audit an explicit raw manifest and segment observations.")
    audit.add_argument("--config", type=Path, default=Path("configs/base.yaml"))
    audit.add_argument("--manifest", type=Path, required=True, help="PB02 raw_manifest.json.")
    audit.add_argument("--output", type=Path, help="New output directory; default: paths.interim/pb03-audit.")
    args = parser.parse_args(argv)
    # Keep check-config/ingest usable without loading the scientific stack.
    if args.command == "audit":
        from metropt3.audit import AuditError, audit_dataset

        try:
            config = load_config(args.config)
            result = audit_dataset(
                args.manifest, config=config,
                output_dir=args.output or config.resolve_path("interim") / "pb03-audit",
            )
        except (ConfigError, AuditError) as exc:
            parser.exit(2, f"metropt3: {exc}\n")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    try:
        config = load_config(args.config)
        if args.command == "ingest":
            result = ingest_package(
                args.source, raw_dir=config.resolve_path("raw"), source_url=args.source_url
            )
            print(json.dumps(result.as_dict(), indent=2, ensure_ascii=False))
            return 0
    except (ConfigError, IngestError) as exc:
        parser.exit(2, f"metropt3: {exc}\n")
    print(
        json.dumps(
            {
                "valid": True,
                "schema_version": config.as_dict()["schema_version"],
                "config_hash": config.config_hash,
                "source": str(config.source),
                "paths": {
                    name: str(config.resolve_path(name))
                    for name in config.as_dict()["paths"]
                },
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
