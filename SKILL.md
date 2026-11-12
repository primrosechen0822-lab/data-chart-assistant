# Data Processing and Plotting

The host-specific slash commands live in `.claude/skills/data-clean/`, `.claude/skills/data-plot/`, and `.claude/skills/data-eda/`. Cursor also discovers these Claude-compatible skill folders.

The skills call the installed `data-chart` CLI. Use `data-chart clean <file>` to create a cleaned sibling file, `data-chart plot <file> --type <line|bar|scatter|heatmap>` to create a chart, or `data-chart eda <file> --plan-only` to profile the dataset and recommend views before generating a report. The reusable processing implementation lives in `src/data_chart_assistant/`.