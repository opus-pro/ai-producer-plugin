#!/usr/bin/env python3
"""Run public, deterministic checks without credentials or network access."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    commands = [
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        [sys.executable, "scripts/validate.py"],
    ]
    # Run every check even after one fails, so a single run reports the full set.
    failures = [
        command
        for command in commands
        if subprocess.run(command, cwd=ROOT).returncode
    ]
    if failures:
        for command in failures:
            print(f"FAILED: {' '.join(command)}", file=sys.stderr)
        return 1
    print("OK: offline unit tests and package validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
