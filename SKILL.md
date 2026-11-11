# Data Processing and Plotting

The host-specific slash commands live in `.claude/skills/data-clean/` and `.claude/skills/data-plot/`. Cursor also discovers these Claude-compatible skill folders.

Both commands call the installed `data-chart` CLI. Use `data-chart clean <file>` to create a cleaned sibling file, or `data-chart plot <file> --type <line|bar|scatter|heatmap>` to create a chart. The reusable processing implementation lives in `src/data_chart_assistant/`.