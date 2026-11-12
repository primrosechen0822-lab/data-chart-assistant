# Data Chart Assistant

Clean CSV/Excel datasets and create charts from the command line or from Claude Code and Cursor chat. The chat skills are thin adapters; the Python package owns the processing behavior so future interfaces can reuse it.

## Install From a Downloaded Repository

Use Python 3.10 or newer. From the repository root, create an environment and install the project:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
```

Open the repository folder in Claude Code or Cursor. The checked-in `.claude/skills/` folder provides `/data-clean`, `/data-plot`, and `/data-eda` in both clients. Run `/data-clean path/to/data.csv`, `/data-plot path/to/data.csv scatter`, or `/data-eda path/to/data.csv`.

To make the commands available in other projects on this machine, install the package in the Python environment used by the terminal, then copy `.claude/skills/data-clean`, `.claude/skills/data-plot`, and `.claude/skills/data-eda` into `~/.claude/skills/`. Cursor also discovers skills from `~/.claude/skills/`. Restart or reload skills in the chat client if they do not appear.

```bash
mkdir -p ~/.claude/skills
cp -R .claude/skills/data-clean .claude/skills/data-plot .claude/skills/data-eda ~/.claude/skills/
```

## CLI

```bash
data-chart clean path/to/data.csv
data-chart clean path/to/data.xlsx --output results/clean.csv --summary results/summary.json
data-chart plot path/to/data.csv --type scatter
data-chart plot path/to/data.csv --type bar --output results/chart.png
data-chart eda path/to/data.csv --plan-only
data-chart eda path/to/data.csv --output results/eda-report.html
data-chart eda path/to/data.csv --time-frequency quarter
```

Cleaning removes fully empty rows and fills missing numeric values with each column's median. It writes a new file by default, named `<input>_cleaned` with the original extension, and does not modify the source. Charts are written beside the input as `<input>_chart.png` unless `--output` is supplied. Both commands print a statistical summary; use `--summary` to save it as JSON.

Supported formats are CSV, XLS, and XLSX. Chart types are `line`, `bar`, `scatter`, and `heatmap`. A scatter plot needs at least two numeric columns; bar charts use the first column as labels and the first numeric column as values.

## Exploratory Analysis

Run `data-chart eda <file> --plan-only` to print a local schema/profile and recommended charts as JSON without creating a report. It does not include raw rows or category values in that output. Run `data-chart eda <file>` to generate a self-contained interactive HTML report beside the input. Numeric columns get distributions, low-cardinality categories get frequency charts, date-like columns get row counts grouped by month by default, and the first two numeric columns get a scatter plot and correlation heatmap. Choose `--time-frequency day|week|month|quarter|year` to change date aggregation. High-cardinality columns are profiled but omitted from category charts. Location-like fields are not geocoded; map recommendations require validated coordinates or a separate geocoding source.

In Claude Code or Cursor, use `/data-eda examples/eda_sample.csv`. The skill presents the profile and visualization plan first, then asks before generating the HTML report unless the user explicitly requested immediate report generation. The report is local and self-contained; it may include category labels from the input file, so treat it like the source data.

## Install From Git

After the repository is public, users can install the CLI with `python -m pip install git+https://github.com/<owner>/data-chart-assistant.git`. A versioned PyPI release can later provide the shorter `python -m pip install data-chart-assistant` command. Installing the Python package alone does not install chat skills; use the repo's skill files or copy them to the host's skill directory.

For project-specific installs, clone or download this repository and open its root in Claude Code or Cursor. Try `/data-clean examples/sample.csv` or `/data-plot examples/sample.csv scatter`. For a one-click install across projects, the next distribution step is publishing this package's skill folders through a Claude plugin and/or Cursor marketplace plugin.

## Test

After installing the project in the active environment, run:

```bash
python -m unittest discover -s tests
```