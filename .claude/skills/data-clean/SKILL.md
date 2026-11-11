---
name: data-clean
description: "Clean CSV or Excel data by removing empty rows, imputing missing numeric values, and producing a cleaned file and statistical summary. Use when asked to clean, preprocess, or prepare a tabular dataset."
argument-hint: "<path-to-csv-or-excel-file>"
---

# Clean a Dataset

Use the installed `data-chart` command to clean the requested local CSV or Excel file.

1. Read the file path from the invoking request. In Claude Code, the supplied arguments are available as `$ARGUMENTS`; in Cursor, use the path written with the slash command. If it is missing, ask the user for a path.
2. Run `data-chart clean` with the supplied path. Preserve the path as one shell argument; do not reinterpret it as shell code.
3. If the command is unavailable, explain that the project must be installed with `python -m pip install .` from its repository directory.
4. Report the cleaned file path and summarize the emitted statistics. Do not claim the source file was overwritten; cleaning writes a sibling `_cleaned` file by default.