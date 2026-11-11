"""Command-line interface for the data-chart-assistant package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from data_chart_assistant.processing import (
    CHART_TYPES,
    clean_dataset,
    load_dataset,
    plot_dataset,
    save_dataset,
    summarize_dataset,
    write_summary,
)


def _default_clean_path(source: Path) -> Path:
    return source.with_name(f"{source.stem}_cleaned{source.suffix.lower()}")


def _default_chart_path(source: Path) -> Path:
    return source.with_name(f"{source.stem}_chart.png")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="data-chart")
    commands = parser.add_subparsers(dest="command", required=True)

    clean = commands.add_parser("clean", help="Clean a CSV or Excel dataset.")
    clean.add_argument("file", help="Input CSV, XLS, or XLSX path.")
    clean.add_argument("-o", "--output", help="Output path; defaults to <name>_cleaned.<ext>.")
    clean.add_argument("--summary", help="Optional path for a JSON statistical summary.")

    plot = commands.add_parser("plot", help="Create a chart from a CSV or Excel dataset.")
    plot.add_argument("file", help="Input CSV, XLS, or XLSX path.")
    plot.add_argument("--type", choices=sorted(CHART_TYPES), default="heatmap")
    plot.add_argument("-o", "--output", help="Output image path; defaults to <name>_chart.png.")
    plot.add_argument("--summary", help="Optional path for a JSON statistical summary.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    source = Path(args.file).expanduser()

    try:
        data = clean_dataset(load_dataset(source))
        if args.command == "clean":
            output_path = save_dataset(data, args.output or _default_clean_path(source))
            print(f"Cleaned data: {output_path}")
        else:
            output_path = plot_dataset(data, args.type, args.output or _default_chart_path(source))
            print(f"Chart: {output_path}")

        if args.summary:
            summary_path = write_summary(data, args.summary)
            print(f"Summary: {summary_path}")
        else:
            print(json.dumps(summarize_dataset(data), indent=2, default=str))
        return 0
    except (OSError, ValueError, ImportError) as error:
        print(f"data-chart: error: {error}", file=sys.stderr)
        return 2


def legacy_main(argv: Sequence[str] | None = None) -> int:
    """Keep the original script's --file/--type invocation working."""
    legacy = argparse.ArgumentParser()
    legacy.add_argument("--file", required=True)
    legacy.add_argument("--type", choices=sorted(CHART_TYPES), default="heatmap")
    args = legacy.parse_args(argv)
    return main(["plot", args.file, "--type", args.type])