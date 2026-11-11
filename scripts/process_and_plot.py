#!/usr/bin/env python3
"""Backward-compatible entry point for the original plotting command."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from data_chart_assistant.cli import legacy_main


if __name__ == "__main__":
    raise SystemExit(legacy_main())