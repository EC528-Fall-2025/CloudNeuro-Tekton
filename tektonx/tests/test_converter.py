import pytest

from tektonx.converter import ConversionError, convert


def test_convert_invalid_source():
    with pytest.raises(ConversionError):
        convert("kind: Pipeline", target="bash", source="unknown")


def test_convert_invalid_target():
    with pytest.raises(ConversionError):
        convert("kind: Pipeline", target="nope", source="tekton")


def test_convert_argo_to_snakemake_dag():
    argo = """
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata: { name: argo-dag }
spec:
  templates:
    - name: dag
      dag:
        tasks:
          - name: prep
            template: prep-tmpl
          - name: analyze
            template: analyze-tmpl
            dependencies: [prep]
    - name: prep-tmpl
      script: { source: "echo prep" }
    - name: analyze-tmpl
      script: { source: "echo analyze" }
"""
    out = convert(argo, target="snakemake", source="argo")
    assert "rule analyze" in out
    assert '"prep.done"' in out
    assert "prep" in out and "analyze" in out


def test_convert_nextflow_to_make():
    nf = """
name: nf
processes:
  - name: prep
    script: echo prep
  - name: analyze
    dependsOn: prep
    script: echo analyze
"""
    out = convert(nf, target="make", source="nextflow")
    assert "analyze: prep" in out
    assert "prep" in out
    assert "analyze" in out


def test_convert_tekton_to_argo():
    tekton = """
apiVersion: tekton.dev/v1
kind: Pipeline
metadata: { name: t-argo }
spec:
  tasks:
    - name: prep
      taskSpec:
        steps:
          - name: s1
            script: echo "prep"
    - name: analyze
      runAfter: [prep]
      taskSpec:
        steps:
          - name: s2
            script: echo "analyze"
"""
    out = convert(tekton, target="argo", source="tekton")
    assert "apiVersion: argoproj.io/v1alpha1" in out
    assert "dependencies:" in out and "prep" in out


def test_convert_tekton_to_nextflow():
    tekton = """
apiVersion: tekton.dev/v1
kind: Pipeline
metadata: { name: t-nextflow }
spec:
  tasks:
    - name: prep
      taskSpec:
        steps:
          - name: s1
            script: echo "prep"
    - name: analyze
      runAfter: [prep]
      taskSpec:
        steps:
          - name: s2
            script: echo "analyze"
"""
    out = convert(tekton, target="nextflow", source="tekton")
    assert "nextflow.enable.dsl=2" in out
    assert "process prep" in out
    assert "workflow" in out
    assert "after prep" in out or "afterprep" in out.replace(" ", "")


def test_convert_wdl_to_bash():
    wdl = """
task prep {
  command { echo "prep" }
}

workflow wf {
  call prep
}
"""
    out = convert(wdl, target="bash", source="wdl")
    assert "Workflow: wf" in out
    assert "prep" in out


def test_convert_tekton_to_wdl():
    tekton = """
apiVersion: tekton.dev/v1
kind: Pipeline
metadata: { name: t-wdl }
spec:
  tasks:
    - name: prep
      taskSpec:
        steps:
          - name: s1
            script: echo "prep"
    - name: analyze
      runAfter: [prep]
      taskSpec:
        steps:
          - name: s2
            script: echo "analyze"
"""
    out = convert(tekton, target="wdl", source="tekton")
    assert "workflow t_wdl" in out or "workflow t-wdl" in out
    assert "task prep" in out and "task analyze" in out
    assert "call analyze" in out
