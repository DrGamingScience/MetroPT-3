"""CLI entry point. Only commands with implemented behavior are registered."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from metropt3 import __version__
from metropt3.config import ConfigError, load_config


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
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError as exc:
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
