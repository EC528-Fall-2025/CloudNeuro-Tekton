# tektonx - Workflow Translation for Clinical Research Pipelines

## Overview

`tektonx` converts Tekton Tasks / TaskRuns / Pipelines / PipelineRuns into other
workflow backends using a shared intermediate representation. Today the bundled
renderers target Bash (default), GNU Make, Snakemake, and a ChRIS plugin
(`app.py`) skeleton suitable for miniChRIS. Argo and Nextflow YAML can also be
ingested with `--source` to reuse the same renderers.
`tektonx` is a workflow-translation tool that converts **Tekton Tasks / TaskRuns / Pipeline / PipelineRuns** into multiple workflow backends using a shared intermediate representation.
It currently supports:

- **SLURM**
- **Sungrid**
- **GNU Make**
- **ChRIS**
- **NextFlow**
- **Bash**

The goal of `tektonx` is to make clinical research workflow components *portable* across infrastructure boundaries—helping IT/research engineers deploy computational imaging pipelines consistently, whether the execution environment is a local server, HPC cluster, Snakemake-driven lab workflow, or a ChRIS/miniChRIS environment used by clinicians. 

---


## Background & Rationale

Modern clinical research teams often build and share pipelines with other teams that do not use the same execution environement. These pipelines must run in **multiple execution environments**:

- Clinicians may run GUI-based ChRIS plugins.  
- Research engineers may prototype workflows using Snakemake or Make.  
- DevOps or IT teams may operate Tekton/OpenShift environments inside hospitals.  
- HPC admins may require SLURM-submit scripts.

This creates fragmentation, duplicated workflow logic, and maintenance burden.

`tektonx` solves this problem by allowing pipeline authors to write **one Tekton YAML definition**, then convert it to the execution backend their infrastructure requires.  
This provides:

- Consistent execution semantics  
- Reproducible builds  
- Clear separation between **workflow definition** and **runtime environment**  
- Easier QA and validation for clinically relevant pipelines  

---

## Intended Audience

**Primary users:**  
IT specialists, DevOps engineers, research engineers, lab technologists, and HPC administrators supporting clinical imaging workflows.

**Secondary users:**  
Clinicians using ChRIS applications that were generated or supported via `tektonx`.

This tool assumes familiarity with containers and basic workflow concepts, but **no Tekton expertise is required**.

---

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) for environment + dependency management

## Setup

1. Install `uv` if you haven’t already:
   ```bash
   # macOS / Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

save the output as a script:
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
uv run python -m tektonx.cli convert <workflow-yaml> --source <tekton|argo|nextflow|wdl> --target <bash|make|snakemake>
```
---

## Examples:

```bash
# Default bash renderer
uv run python -m tektonx.cli convert examples/hello-task.yaml

# GNU Make
uv run python -m tektonx.cli convert examples/taskrun-complete.yaml --target make

# Snakemake
uv run python -m tektonx.cli convert examples/pipeline-complete.yaml --target snakemake

# ChRIS plugin (writes app.py that runs steps sequentially in one container)
uv run python -m tektonx.cli convert examples/task-complete.yaml --target chris --out dist/app.py

# ChRIS plugin with a simple DAG (fan-out/fan-in)
uv run python -m tektonx.cli convert examples/pipeline-dag.yaml --target chris --out dist/dag_app.py
```

Use `--source argo`, `--source nextflow`, or `--source wdl` to take those formats through the same renderers (default is `tekton`).

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
- DAG metadata is emitted to `dag.json` and `dag.dot` (Graphviz) alongside the report.

## Example Inputs / Tests

`examples/` includes ready-to-run Tekton sources that exercise every supported
kind plus an error case. See [`examples/README.md`](examples/README.md) for a
table of files and suggested commands (bash/make/snakemake) to validate parser
and renderer behavior.

## Project Scope & Roadmap
**Implemented**
- Tekton → Bash
- Tekton → Make
- Tekton → Snakemake
- Tekton → ChRIS (miniChRIS)
- Tekton → SLURM
- Tekton → Sungrid

**In Progress**
- Experimental reverse translation: Snakemake → Intermediate Representation → Tekton

## Software License
This project is released under the MIT License.

You may freely:
- Use
- Modify
- Distribute
- Incorporate into commercial or non-commercial medical research workflows

### Disclaimer
`tektonx` is not a medical device and does not perform diagnostic or clinical functions.
Compliance with local regulatory or institutional requirements is the responsibility of the deploying organization.