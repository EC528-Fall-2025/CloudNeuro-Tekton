import pytest

from tektonx.parsers import (
    ArgoParseError,
    NextflowParseError,
    WDLParseError,
    parse_argo_yaml,
    parse_nextflow_yaml,
    parse_wdl,
)


def test_parse_argo_dag_dependencies():
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
          - name: report
            template: report-tmpl
            depends: analyze
    - name: prep-tmpl
      script: { source: "echo prep" }
    - name: analyze-tmpl
      container:
        image: ubuntu:22.04
        command: ["/bin/bash", "-lc"]
        args: ["echo analyze"]
    - name: report-tmpl
      script: { source: "echo report" }
"""
    wf = parse_argo_yaml(argo)
    names = [t.name for t in wf.tasks]
    assert names == ["prep", "analyze", "report"]
    assert wf.tasks[1].run_after == ["prep"]
    assert wf.tasks[2].run_after == ["analyze"]
    assert wf.tasks[0].steps[0].script.strip() == "echo prep"
    assert wf.tasks[1].steps[0].command == ["/bin/bash", "-lc"]
    assert wf.tasks[2].steps[0].script.strip() == "echo report"


def test_parse_nextflow_dependencies():
    nf = """
name: nf
processes:
  - name: prep
    script: echo prep
  - name: analyze
    dependsOn: prep
    script: echo analyze
  - name: report
    after: [analyze]
    script: echo report
"""
    wf = parse_nextflow_yaml(nf)
    assert [t.name for t in wf.tasks] == ["prep", "analyze", "report"]
    assert wf.tasks[1].run_after == ["prep"]
    assert wf.tasks[2].run_after == ["analyze"]


def test_parse_wdl_workflow_calls_with_after():
    wdl = """
task prep {
  command { echo "prep" }
}

task analyze {
  command { echo "analyze" }
}

workflow wf {
  call prep
  call analyze after prep
}
"""
    wf = parse_wdl(wdl)
    assert wf.name == "wf"
    assert [t.name for t in wf.tasks] == ["prep", "analyze"]
    assert wf.tasks[1].run_after == ["prep"]
    assert "analyze-command" in wf.tasks[1].steps[0].name


def test_parse_wdl_tasks_without_workflow():
    wdl = """
task lone {
  command { echo "lone" }
}
"""
    wf = parse_wdl(wdl)
    assert wf.name == "unnamed"
    assert [t.name for t in wf.tasks] == ["lone"]
    assert wf.tasks[0].run_after == []


def test_parse_invalid_argo_raises():
    with pytest.raises(ArgoParseError):
        parse_argo_yaml("kind: NotAWorkflow")


def test_parse_invalid_nextflow_raises():
    with pytest.raises(NextflowParseError):
        parse_nextflow_yaml("not: a mapping")


def test_parse_invalid_wdl_raises():
    with pytest.raises(WDLParseError):
        parse_wdl("")
