## TektonX Examples

This directory contains ready-to-run Tekton YAML sources and tests for Bash/Make/Snakemake/ChRIS outputs.

### Files
- `hello-task.yaml` — minimal single task.
- `task-complete.yaml` / `taskrun-complete.yaml` — richer Task/TaskRun coverage.
- `pipeline-complete.yaml` / `pipelinerun-complete.yaml` — multi-task pipelines.
- `pipeline-dag.yaml` — small fan-out/fan-in DAG (fetch → preprocess-a/b → combine).
- `not-tekton.yaml` — negative parse case.

### Prerequisites
- Python 3.11+
- `make`, `snakemake`, `bash`

### Install
```bash
cd /Users/trieutran/CloudNeuro-Tekton/tektonx
uv venv .venv
source .venv/bin/activate
uv pip install -e .
uv pip install chris_plugin snakemake
```

### Test with GNU Make
```bash
python -m tektonx.cli examples/pipeline-dag.yaml --target make --out dist/Makefile
mkdir -p /tmp/gnu_make_test
WORKDIR=/tmp/gnu_make_test make -f dist/Makefile
```

### Test with Snakemake
```bash
python -m tektonx.cli examples/pipeline-dag.yaml --target snakemake --out dist/Snakefile
mkdir -p /tmp/snake_make_test
XDG_CACHE_HOME=/tmp TMPDIR=/tmp WORKDIR=/tmp/snake_make_test snakemake -s dist/Snakefile --cores 1
```

### Test with ChRIS Runner
(Offline/local smoke test: runs the generated runner directly with Python, no container.)

```bash
python -m tektonx.cli examples/pipeline-dag.yaml --target chris --out dist/dag_app.py
mkdir -p /tmp/chris-input /tmp/chris-output /tmp/chris-work
python dist/dag_app.py --workdir /tmp/chris-work /tmp/chris-input /tmp/chris-output
```

Outputs:
- Make: artifacts under `/tmp/gnu_make_test`
- Snakemake: artifacts under `/tmp/snake_make_test`.
- ChRIS: task outputs under `/tmp/chris-work`; report + DAG metadata under `/tmp/chris-output` (`workflow_report.json`, `dag.json`, `dag.dot`).

### Test as a miniChRIS-friendly image
Containerized run: emulates how miniChRIS would execute the plugin image. 

To actually use it in Chris, we would have to push dag-chris to our registry, then register it as a plugin, then run it with appropriate directoy mappings, it will emit `workflow_report.json`, `dag.json`, and `dag.dot` to the output directory.

Build a minimal plugin container (expects `dist/dag_app.py` from the step above):
```bash
docker build -f examples/Dockerfile.minichris -t dag-chris .
```
Run it locally (ChRIS-style runner) mounting input/output/work spaces:
```bash
docker run --rm \
  -v /tmp/chris-input:/input:rw \
  -v /tmp/chris-output:/output:rw \
  -v /tmp/chris-work:/work:rw \
  -e WORKDIR=/work \
  dag-chris /input /output
```
