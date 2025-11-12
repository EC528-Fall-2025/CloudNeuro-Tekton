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

save the output as a script:
mkdir -p dist
uv run python src/tektonx/cli.py examples/hello-task.yaml --out dist/hello.sh
chmod +x dist/hello.sh
./dist/hello.sh

