# Example Tekton Sources

Each file in this directory is a ready-to-run Tekton resource that feeds the
`tektonx` converter. Use them as living test cases for the parser + renderer
stack.

| File | Tekton kind | Purpose | Sample command |
| ---- | ----------- | ------- | -------------- |
| `task-complete.yaml` | `Task` | Standalone multi-step task with scripts, commands, env vars, and working dir changes. | `uv run python -m tektonx.cli convert examples/task-complete.yaml --target bash` |
| `taskrun-complete.yaml` | `TaskRun` | Inline `taskSpec` exercise ensuring TaskRuns funnel into the IR. | `uv run python -m tektonx.cli convert examples/taskrun-complete.yaml --target make` |
| `pipeline-complete.yaml` | `Pipeline` | Demonstrates `runAfter` edges across three inline tasks. | `uv run python -m tektonx.cli convert examples/pipeline-complete.yaml --target snakemake` |
| `pipelinerun-complete.yaml` | `PipelineRun` | Includes params plus both inline steps and external `taskRef` references. | `uv run python -m tektonx.cli convert examples/pipelinerun-complete.yaml --target snakemake` |
| `hello-task.yaml` | `Task` | Minimal quick-start example used in earlier docs. | `uv run python -m tektonx.cli convert examples/hello-task.yaml` |
| `not-tekton.yaml` | — | Negative test that should trigger a parse error. | `uv run python -m tektonx.cli convert examples/not-tekton.yaml` |

Feel free to diff renderer output against the repo to validate future changes:

```bash
TARGET=snakemake
INPUT=examples/pipeline-complete.yaml
uv run python -m tektonx.cli convert "$INPUT" --target "$TARGET" > /tmp/out.txt
diff -u examples/${TARGET}.golden /tmp/out.txt
```

(`*.golden` files are intentionally omitted for now—generate and commit the ones
you need for your workflow engine.)
