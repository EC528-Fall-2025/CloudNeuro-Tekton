import pytest

from tektonx.converter import convert


LINEAR_PIPELINE = """
apiVersion: tekton.dev/v1
kind: Pipeline
metadata:
  name: linear
spec:
  tasks:
    - name: prep
      taskSpec:
        steps:
          - name: prep-step
            script: |
              echo "prep"
    - name: analyze
      runAfter: [prep]
      taskSpec:
        steps:
          - name: analyze-step
            script: |
              echo "analyze"
"""

DAG_PIPELINE = """
apiVersion: tekton.dev/v1
kind: Pipeline
metadata:
  name: daggy
spec:
  tasks:
    - name: prep
      taskSpec:
        steps:
          - name: prep-step
            script: |
              echo "prep"
    - name: branch-a
      runAfter: [prep]
      taskSpec:
        steps:
          - name: branch-a-step
            script: |
              echo "branch-a"
    - name: branch-b
      runAfter: [prep]
      taskSpec:
        steps:
          - name: branch-b-step
            script: |
              echo "branch-b"
    - name: combine
      runAfter: [branch-a, branch-b]
      taskSpec:
        steps:
          - name: combine-step
            script: |
              echo "combine"
"""


def _normalized(text: str) -> str:
    return "".join(text.split())


LINEAR_CHECKS = {
    "bash": lambda out: "Task: prep" in out and "Task: analyze" in out,
    "argo": lambda out: "name: prep" in out and "dependencies:" in out,
    "make": lambda out: "analyze: prep" in out,
    "nextflow": lambda out: "nextflow.enable.dsl=2" in out and "process prep" in out and "workflow" in out,
    "snakemake": lambda out: 'rule analyze' in out and '"prep.done"' in out,
    "chris": lambda out: '"run_after":["prep"]' in _normalized(out),
    "slurm": lambda out: "--dependency=afterok:$JOB_prep" in out,
    "sungrid": lambda out: "-hold_jid $JOB_prep" in out,
    "wdl": lambda out: "task prep" in out and "call analyze" in out,
}

DAG_CHECKS = {
    "bash": lambda out: "Task: prep" in out and "Task: combine" in out,
    "argo": lambda out: "dependencies:" in out and "branch-a" in out and "branch-b" in out,
    "make": lambda out: "combine: branch-a branch-b" in out or "combine: branch-b branch-a" in out,
    "nextflow": lambda out: "process combine" in out and "after branch_a" in out.replace("-", "_"),
    "snakemake": lambda out: 'rule combine' in out and '"branch-a.done"' in out and '"branch-b.done"' in out,
    "chris": lambda out: '"run_after":["branch-a","branch-b"]' in _normalized(out)
    or '"run_after":["branch-b","branch-a"]' in _normalized(out),
    "slurm": lambda out: "afterok:$JOB_branch_a:$JOB_branch_b" in out or "afterok:$JOB_branch_b:$JOB_branch_a" in out,
    "sungrid": lambda out: "-hold_jid $JOB_branch_a,$JOB_branch_b" in out or "-hold_jid $JOB_branch_b,$JOB_branch_a" in out,
    "wdl": lambda out: "call combine" in out,
}


@pytest.mark.parametrize("target", LINEAR_CHECKS.keys())
def test_linear_pipeline_renders(target: str):
    output = convert(LINEAR_PIPELINE, target=target, source="tekton")
    assert "prep" in output and "analyze" in output
    assert LINEAR_CHECKS[target](output), f"Dependency/structure missing for {target}"


@pytest.mark.parametrize("target", DAG_CHECKS.keys())
def test_dag_pipeline_renders(target: str):
    output = convert(DAG_PIPELINE, target=target, source="tekton")
    for name in ["prep", "branch-a", "branch-b", "combine"]:
        assert name in output
    assert DAG_CHECKS[target](output), f"DAG dependencies missing for {target}"


def test_make_renderer_inline_scripts():
    output = convert(LINEAR_PIPELINE, target="make", source="tekton")
    assert "SHELL := bash" in output
    assert "__TEKTONX__" not in output
    assert "bash -lc $$'echo \"prep\"'" in output
