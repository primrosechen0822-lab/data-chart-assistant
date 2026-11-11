# Data Chart Assistant

Clean CSV/Excel datasets and create charts from the command line or from Claude Code and Cursor chat. The chat skills are thin adapters; the Python package owns the processing behavior so future interfaces can reuse it.

## Install From a Downloaded Repository

Use Python 3.10 or newer. From the repository root, create an environment and install the project:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
```

Open the repository folder in Claude Code or Cursor. The checked-in `.claude/skills/` folder provides `/data-clean` and `/data-plot` in both clients. Run `/data-clean path/to/data.csv` or `/data-plot path/to/data.csv scatter`.

To make the commands available in other projects on this machine, install the package in the Python environment used by the terminal, then copy `.claude/skills/data-clean` and `.claude/skills/data-plot` into `~/.claude/skills/`. Cursor also discovers skills from `~/.claude/skills/`. Restart or reload skills in the chat client if they do not appear.

```bash
mkdir -p ~/.claude/skills
cp -R .claude/skills/data-clean .claude/skills/data-plot ~/.claude/skills/
```

## CLI

```bash
data-chart clean path/to/data.csv
data-chart clean path/to/data.xlsx --output results/clean.csv --summary results/summary.json
data-chart plot path/to/data.csv --type scatter
data-chart plot path/to/data.csv --type bar --output results/chart.png
```

Cleaning removes fully empty rows and fills missing numeric values with each column's median. It writes a new file by default, named `<input>_cleaned` with the original extension, and does not modify the source. Charts are written beside the input as `<input>_chart.png` unless `--output` is supplied. Both commands print a statistical summary; use `--summary` to save it as JSON.

Supported formats are CSV, XLS, and XLSX. Chart types are `line`, `bar`, `scatter`, and `heatmap`. A scatter plot needs at least two numeric columns; bar charts use the first column as labels and the first numeric column as values.

## Install From Git

After the repository is public, users can install the CLI with `python -m pip install git+https://github.com/<owner>/data-chart-assistant.git`. A versioned PyPI release can later provide the shorter `python -m pip install data-chart-assistant` command. Installing the Python package alone does not install chat skills; use the repo's skill files or copy them to the host's skill directory.

For project-specific installs, clone or download this repository and open its root in Claude Code or Cursor. Try `/data-clean examples/sample.csv` or `/data-plot examples/sample.csv scatter`. For a one-click install across projects, the next distribution step is publishing this package's skill folders through a Claude plugin and/or Cursor marketplace plugin.

## Test

After installing the project in the active environment, run:

```bash
python -m unittest discover -s tests
```