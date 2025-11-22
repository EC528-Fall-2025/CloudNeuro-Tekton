1. Install uv already have it:

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

2. Set up dependencies:

uv sync

3. Run the example task:
uv run python src/tektonx/cli.py examples/hello-task.yaml
- epected output:
=== Tekton Task/hello-task ===
--- Step: say-hello ---
Hello from Tekton
--- Step: compute ---
5

<<<<<<< Updated upstream
save the output as a script:
=======
   # Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
2. Install dependencies (creates `.venv/` automatically):
   ```bash
   uv sync
   ```

## Running Mac

Install dependencies tools UV:
```bash
uv tool install .
```

```bash
tektonx --help
```

```bash
tektonx examples/hello-task.yaml --target slurm
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
```

> **Note:** If you invoke the CLI without the `convert` subcommand (legacy mode),
> pass the YAML path directly after `tektonx.cli`. Both forms are supported.

### Saving Output

Renderers write to stdout by default. Use `--out` to persist artifacts:

```bash
>>>>>>> Stashed changes
mkdir -p dist
uv run python src/tektonx/cli.py examples/hello-task.yaml --out dist/hello.sh
chmod +x dist/hello.sh
./dist/hello.sh

