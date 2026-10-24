"""Allow python -m metropt3 as well as python -m metropt3.cli."""

from metropt3.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
