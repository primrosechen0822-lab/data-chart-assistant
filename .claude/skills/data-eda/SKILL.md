---
name: data-eda
description: "Explore a local CSV or Excel dataset. Profile column types, missing values, numeric distributions, and recommend suitable charts. Use for exploratory data analysis, understanding a dataset, or generating an interactive HTML EDA report."
argument-hint: "[path-to-csv-or-excel-file]"
---

# Exploratory Data Analysis

Use the installed `data-chart` CLI to profile the requested local CSV or Excel file and optionally create an interactive HTML report.

1. Read the file path from the invoking request. In Claude Code, arguments are available as `$ARGUMENTS`; in Cursor, use the path written with the slash command. Ask for a path if none is provided.
2. Run `data-chart eda <path> --plan-only`, preserving the user-provided path as one shell argument. Do not send file rows or category values to the model. The CLI returns schema and aggregate profile data only.
3. Present the row and column counts, inferred type counts, notable missingness, numeric ranges/percentiles, and recommended charts with their reasons. Clarify that postal codes are not mapped without validated coordinates or a geocoding source.
4. Ask whether to generate the report or adjust the plan. If the user explicitly asked for the report already, proceed without an extra confirmation.
5. On approval, run `data-chart eda <path>` and report the resulting HTML path. The report is self-contained and local; it can contain category labels from the input, so treat it as data-sensitive.
6. If `data-chart` is unavailable, explain that the package must be installed with `python -m pip install .` from the repository root or installed environment.
