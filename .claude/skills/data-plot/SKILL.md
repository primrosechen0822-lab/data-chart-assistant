---
name: data-plot
description: "Create a chart from local CSV or Excel data. Use when asked to plot, visualize, chart, or explore a tabular dataset. Supports line, bar, scatter, and heatmap charts."
argument-hint: "<path-to-csv-or-excel-file> [line|bar|scatter|heatmap]"
---

# Plot a Dataset

Use the installed `data-chart` command to create the requested chart.

1. Read the file path and optional chart type from the invoking request. In Claude Code, the supplied arguments are available as `$ARGUMENTS`; in Cursor, use the path and type written with the slash command. Ask for a path if none is provided. Default the chart type to `heatmap` when the user does not specify one.
2. Run `data-chart plot` with the path and `--type` set to the selected type. Preserve the path as one shell argument; do not reinterpret it as shell code.
3. If the command is unavailable, explain that the project must be installed with `python -m pip install .` from its repository directory.
4. Report the chart path and summary. The default chart is written beside the input as `<name>_chart.png`.