## Overview

`tektonx` converts Tekton Tasks / TaskRuns / Pipelines / PipelineRuns into other
workflow backends using a shared intermediate representation. Today the bundled
renderers target Bash (default), GNU Make, Snakemake, and a ChRIS plugin
(`app.py`) skeleton suitable for miniChRIS.

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) for environment + dependency management

## Setup

1. Install `uv` if you haven’t already:
   ```bash
   # macOS / Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
2. Install dependencies (creates `.venv/` automatically):
   ```bash
   uv sync
   ```

## Running Conversions

From the `tektonx/` directory, run:

```bash
uv run python -m tektonx.cli convert <tekton-yaml> --target <bash|make|snakemake>
```

Examples:

```bash
# Default bash renderer
uv run python -m tektonx.cli convert examples/hello-task.yaml

# GNU Make
uv run python -m tektonx.cli convert examples/taskrun-complete.yaml --target make

# Snakemake
uv run python -m tektonx.cli convert examples/pipeline-complete.yaml --target snakemake

# ChRIS plugin (writes app.py that runs steps sequentially in one container)
uv run python -m tektonx.cli convert examples/task-complete.yaml --target chris --out dist/app.py
```

> **Note:** If you invoke the CLI without the `convert` subcommand (legacy mode),
> pass the YAML path directly after `tektonx.cli`. Both forms are supported.

### Saving Output

Renderers write to stdout by default. Use `--out` to persist artifacts:

```bash
mkdir -p dist
uv run python -m tektonx.cli convert examples/hello-task.yaml --target bash --out dist/hello.sh
chmod +x dist/hello.sh
./dist/hello.sh
```

### ChRIS Renderer Notes

- Emits a minimal `app.py` compatible with the [`python-chrisapp-template`](https://github.com/FNNDSC/python-chrisapp-template).
- Steps run sequentially inside one container (miniChRIS-friendly); Tekton step images are logged but not pulled.
- The plugin writes `workflow_report.json` to the output directory summarizing successes/failures.

## Example Inputs / Tests

`examples/` includes ready-to-run Tekton sources that exercise every supported
kind plus an error case. See [`examples/README.md`](examples/README.md) for a
table of files and suggested commands (bash/make/snakemake) to validate parser
and renderer behavior.
