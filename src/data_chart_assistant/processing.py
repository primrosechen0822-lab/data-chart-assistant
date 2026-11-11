"""Data loading, cleaning, summaries, and chart generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


SUPPORTED_SUFFIXES = {".csv", ".xls", ".xlsx"}
CHART_TYPES = {"line", "bar", "scatter", "heatmap"}


def load_dataset(file_path: str | Path) -> pd.DataFrame:
    path = Path(file_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Input file does not exist: {path}")
    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError("Supported input formats are CSV, XLS, and XLSX.")

    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_excel(path)


def clean_dataset(data: pd.DataFrame) -> pd.DataFrame:
    cleaned = data.dropna(how="all").copy()
    numeric_columns = cleaned.select_dtypes(include="number").columns
    if len(numeric_columns):
        cleaned.loc[:, numeric_columns] = cleaned[numeric_columns].fillna(
            cleaned[numeric_columns].median()
        )
    return cleaned


def save_dataset(data: pd.DataFrame, output_path: str | Path) -> Path:
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".csv":
        data.to_csv(path, index=False)
    elif path.suffix.lower() in {".xls", ".xlsx"}:
        data.to_excel(path, index=False)
    else:
        raise ValueError("Output format must be CSV, XLS, or XLSX.")
    return path


def summarize_dataset(data: pd.DataFrame) -> dict[str, Any]:
    numeric_data = data.select_dtypes(include="number")
    if numeric_data.empty:
        return {"note": "No numeric columns found", "rows": len(data), "columns": len(data.columns)}
    return {
        "rows": len(data),
        "columns": len(data.columns),
        "numeric_summary": numeric_data.describe().to_dict(),
    }


def write_summary(data: pd.DataFrame, output_path: str | Path) -> Path:
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summarize_dataset(data), indent=2, default=str) + "\n")
    return path


def plot_dataset(
    data: pd.DataFrame, chart_type: str, output_path: str | Path
) -> Path:
    if chart_type not in CHART_TYPES:
        raise ValueError(f"Chart type must be one of: {', '.join(sorted(CHART_TYPES))}.")

    numeric_data = data.select_dtypes(include="number")
    if numeric_data.empty:
        raise ValueError("Cannot plot this dataset because it has no numeric columns.")

    sns.set_theme(style="whitegrid")
    figure, axis = plt.subplots(figsize=(10, 6), dpi=200)
    try:
        if chart_type == "line":
            numeric_data.plot(ax=axis)
            axis.set_title("Line Chart")
        elif chart_type == "bar":
            label_column = data.columns[0]
            plot_data = data.head(15)
            axis.bar(plot_data[label_column].astype(str), plot_data[numeric_data.columns[0]])
            axis.set_title(f"{numeric_data.columns[0]} by {label_column}")
            axis.tick_params(axis="x", labelrotation=45)
        elif chart_type == "scatter":
            if len(numeric_data.columns) < 2:
                raise ValueError("Scatter plots require at least two numeric columns.")
            axis.scatter(numeric_data.iloc[:, 0], numeric_data.iloc[:, 1], alpha=0.75)
            axis.set_xlabel(str(numeric_data.columns[0]))
            axis.set_ylabel(str(numeric_data.columns[1]))
            axis.set_title("Scatter Plot")
        else:
            sns.heatmap(numeric_data.corr(), annot=True, cmap="coolwarm", fmt=".2f", ax=axis)
            axis.set_title("Numerical Feature Correlation")

        figure.tight_layout()
        path = Path(output_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path)
        return path
    finally:
        plt.close(figure)