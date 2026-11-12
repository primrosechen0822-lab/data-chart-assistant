"""Local dataset profiling and interactive exploratory report generation."""

from __future__ import annotations

import html
import math
import re
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.io as pio


DATE_NAME_PATTERN = re.compile(r"date|time|timestamp|day", re.IGNORECASE)
ID_NAME_PATTERN = re.compile(r"(^id$|_id$|^id_|identifier|record.?key)", re.IGNORECASE)
POSTAL_NAME_PATTERN = re.compile(r"postal|zip.?code|zipcode", re.IGNORECASE)
MAX_RECOMMENDED_COLUMNS = 8
MAX_RECOMMENDED_CATEGORIES = 8
TIME_FREQUENCIES = {"day": "D", "week": "W", "month": "M", "quarter": "Q", "year": "Y"}


def _json_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    return value


def _infer_datetime(series: pd.Series, name: str) -> pd.Series | None:
    if not DATE_NAME_PATTERN.search(str(name)) or series.dropna().empty:
        return None
    parsed = pd.to_datetime(series, errors="coerce", format="mixed")
    if parsed.notna().mean() >= 0.8:
        return parsed
    return None


def profile_dataset(
    data: pd.DataFrame,
    max_categories: int = 12,
    time_frequency: str = "month",
) -> dict[str, Any]:
    """Return structural and aggregate statistics without returning raw rows."""
    if max_categories < 1:
        raise ValueError("max_categories must be at least 1.")
    if time_frequency not in TIME_FREQUENCIES:
        raise ValueError(f"Time frequency must be one of: {', '.join(TIME_FREQUENCIES)}.")
    columns: list[dict[str, Any]] = []
    type_counts = {"numeric": 0, "categorical": 0, "datetime": 0, "identifier": 0, "other": 0}

    for column in data.columns:
        series = data[column]
        non_null = series.dropna()
        unique_count = int(series.nunique(dropna=True))
        missing_count = int(series.isna().sum())
        parsed_dates = _infer_datetime(series, str(column))

        if pd.api.types.is_bool_dtype(series.dtype):
            data_type = "categorical"
        elif POSTAL_NAME_PATTERN.search(str(column)):
            data_type = "categorical"
        elif pd.api.types.is_numeric_dtype(series.dtype):
            id_like = bool(ID_NAME_PATTERN.search(str(column))) and unique_count > 1
            data_type = "identifier" if id_like else "numeric"
        elif parsed_dates is not None:
            data_type = "datetime"
        elif ID_NAME_PATTERN.search(str(column)) and unique_count > 1:
            data_type = "identifier"
        elif pd.api.types.is_string_dtype(series.dtype) or pd.api.types.is_object_dtype(series.dtype):
            data_type = "categorical"
        else:
            data_type = "other"

        type_counts[data_type] += 1
        details: dict[str, Any] = {
            "name": str(column),
            "type": data_type,
            "missing_count": missing_count,
            "missing_percent": round(missing_count * 100 / len(data), 2) if len(data) else 0.0,
            "unique_count": unique_count,
        }
        if data_type == "numeric":
            details["statistics"] = {
                key: _json_value(value)
                for key, value in {
                    "min": non_null.min() if not non_null.empty else None,
                    "median": non_null.median() if not non_null.empty else None,
                    "p99": non_null.quantile(0.99) if not non_null.empty else None,
                    "max": non_null.max() if not non_null.empty else None,
                    "mean": non_null.mean() if not non_null.empty else None,
                }.items()
            }
        if data_type == "categorical":
            details["high_cardinality"] = unique_count > max_categories
        columns.append(details)

    numeric = [item["name"] for item in columns if item["type"] == "numeric"]
    categorical = [item for item in columns if item["type"] == "categorical"]
    dates = [item["name"] for item in columns if item["type"] == "datetime"]
    recommendations: list[dict[str, Any]] = []

    for name in numeric[:MAX_RECOMMENDED_COLUMNS]:
        recommendations.append({
            "chart": "histogram",
            "columns": [name],
            "reason": "Inspect the numeric feature's distribution and possible skew or outliers.",
        })
    chartable_categories = [item for item in categorical if not item["high_cardinality"]]
    for item in chartable_categories[:MAX_RECOMMENDED_CATEGORIES]:
        recommendations.append({
            "chart": "category_frequency",
            "columns": [item["name"]],
            "reason": "Compare category frequencies; only the most common categories are shown.",
        })
    for name in dates[:3]:
        recommendations.append({
            "chart": "time_series",
            "columns": [name],
            "reason": f"Inspect row counts over time, grouped by {time_frequency}.",
        })
    if len(numeric) >= 2:
        recommendations.append({
            "chart": "scatter",
            "columns": numeric[:2],
            "reason": "Inspect the relationship between the first two numeric features.",
        })
        recommendations.append({
            "chart": "correlation_heatmap",
            "columns": numeric[:MAX_RECOMMENDED_COLUMNS],
            "reason": "Review pairwise linear correlations among numeric features.",
        })

    omitted_numeric = max(0, len(numeric) - MAX_RECOMMENDED_COLUMNS)
    if omitted_numeric:
        recommendations.append({
            "note": f"{omitted_numeric} additional numeric columns were not selected for individual charts.",
        })
    omitted_categories = max(0, len(chartable_categories) - MAX_RECOMMENDED_CATEGORIES)
    if omitted_categories:
        recommendations.append({
            "note": f"{omitted_categories} additional low-cardinality categorical columns were not selected for charts.",
        })
    high_cardinality = [item["name"] for item in categorical if item["high_cardinality"]]
    if high_cardinality:
        recommendations.append({
            "note": "High-cardinality categorical columns were profiled but not charted: "
            + ", ".join(high_cardinality),
        })
    if any(re.search(r"zip|postal|latitude|longitude|\blat\b|\blon\b", name, re.IGNORECASE) for name in data.columns):
        recommendations.append({
            "note": "Location-like columns were detected. A map requires validated coordinates or a geocoding source; no locations were inferred.",
        })

    return {
        "rows": int(len(data)),
        "columns": int(len(data.columns)),
        "type_counts": type_counts,
        "column_profiles": columns,
        "recommendations": recommendations,
        "time_frequency": time_frequency,
        "privacy": "Profile contains aggregate statistics and schema only; raw data rows are not included.",
    }


def _build_figures(data: pd.DataFrame, profile: dict[str, Any], max_categories: int) -> list[tuple[str, Any]]:
    figures: list[tuple[str, Any]] = []
    column_types = {item["name"]: item["type"] for item in profile["column_profiles"]}
    numeric = [name for name, kind in column_types.items() if kind == "numeric"]
    chartable_categories = {
        item["name"]
        for item in profile["column_profiles"]
        if item["type"] == "categorical" and not item.get("high_cardinality", False)
    }
    category_columns = [
        name for name, kind in column_types.items()
        if kind == "categorical" and name in chartable_categories
    ][:MAX_RECOMMENDED_CATEGORIES]
    date_columns = [name for name, kind in column_types.items() if kind == "datetime"]

    for name in numeric[:MAX_RECOMMENDED_COLUMNS]:
        figures.append((f"Distribution: {name}", px.histogram(data, x=name, title=f"Distribution: {name}")))
    for name in category_columns:
        counts = data[name].dropna().astype(str).value_counts().head(max_categories).sort_values()
        if not counts.empty:
            chart_data = pd.DataFrame({"category": [html.escape(value) for value in counts.index], "count": counts.values})
            figures.append((f"Category frequency: {name}", px.bar(chart_data, x="count", y="category", orientation="h", title=f"Category frequency: {name}")))
    for name in date_columns[:3]:
        parsed = _infer_datetime(data[name], name)
        if parsed is not None:
            period = parsed.dropna().dt.to_period(TIME_FREQUENCIES[profile["time_frequency"]]).astype(str)
            counts = period.value_counts().sort_index()
            if not counts.empty:
                chart_data = pd.DataFrame({"period": counts.index, "rows": counts.values})
                figures.append((f"Rows over time: {name}", px.line(chart_data, x="period", y="rows", markers=True, title=f"Rows over time: {name}")))
    if len(numeric) >= 2:
        figures.append((
            f"Relationship: {numeric[0]} and {numeric[1]}",
            px.scatter(data, x=numeric[0], y=numeric[1], title=f"{numeric[0]} vs {numeric[1]}"),
        ))
        corr = data[numeric[:MAX_RECOMMENDED_COLUMNS]].corr(numeric_only=True)
        figures.append(("Numeric correlation", px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", title="Numeric correlation")))
    return figures


def write_eda_report(
    data: pd.DataFrame,
    profile: dict[str, Any],
    output_path: str | Path,
    max_categories: int = 12,
) -> Path:
    """Write a self-contained HTML report; source data remains local."""
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    figures = _build_figures(data, profile, max_categories)
    sections: list[str] = []
    include_plotlyjs: bool | str = True
    for title, figure in figures:
        sections.append(
            f"<section><h2>{html.escape(title)}</h2>"
            + pio.to_html(figure, full_html=False, include_plotlyjs=include_plotlyjs)
            + "</section>"
        )
        include_plotlyjs = False

    counts = profile["type_counts"]
    metrics = "".join(
        f"<li><strong>{html.escape(label.title())}</strong><span>{counts[label]}</span></li>"
        for label in ("numeric", "categorical", "datetime", "identifier", "other")
    )
    column_rows_parts: list[str] = []
    for item in profile["column_profiles"]:
        statistics = item.get("statistics", {})
        statistics_text = "; ".join(
            f"{key}: {value}" for key, value in statistics.items()
        ) or "-"
        column_rows_parts.append(
            "<tr>"
            f"<td>{html.escape(item['name'])}</td><td>{item['type']}</td>"
            f"<td>{item['missing_count']}</td><td>{item['missing_percent']:.2f}%</td>"
            f"<td>{item['unique_count']}</td><td>{html.escape(statistics_text)}</td></tr>"
        )
    column_rows = "".join(column_rows_parts)
    notes = "".join(
        f"<li>{html.escape(item['note'])}</li>"
        for item in profile["recommendations"] if "note" in item
    )
    if not sections:
        sections.append("<p>No chartable columns were found. Review the column profile above.</p>")

    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Exploratory Data Analysis</title>
<style>
body{{font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;max-width:1180px;margin:32px auto;padding:0 20px;color:#202b35;background:#f5f7f8}}
h1,h2{{line-height:1.2}}h1{{font-size:30px}}h2{{font-size:20px}}.metrics{{display:flex;flex-wrap:wrap;gap:12px;padding:0;list-style:none}}
.metrics li{{background:white;border:1px solid #dce3e7;padding:12px 16px;min-width:120px;display:flex;justify-content:space-between;gap:20px}}
table{{border-collapse:collapse;width:100%;background:white}}th,td{{text-align:left;padding:9px;border-bottom:1px solid #dce3e7}}th{{background:#e8eef1}}
section{{background:white;border:1px solid #dce3e7;margin:20px 0;padding:16px;overflow-x:auto}}.note{{color:#46535d}}
</style></head><body>
<h1>Exploratory Data Analysis</h1>
<p>{profile['rows']} rows · {profile['columns']} columns</p>
<ul class="metrics">{metrics}</ul>
<h2>Column profile</h2><table><thead><tr><th>Column</th><th>Type</th><th>Missing</th><th>Missing %</th><th>Unique values</th><th>Numeric summary</th></tr></thead>
<tbody>{column_rows}</tbody></table>
<h2>Notes</h2><ul class="note">{notes or '<li>No additional profiling notes.</li>'}</ul>
<h2>Recommended views</h2>{''.join(sections)}
</body></html>"""
    path.write_text(document, encoding="utf-8")
    return path