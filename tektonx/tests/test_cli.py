from pathlib import Path

from tektonx.cli import convert_command


def test_cli_convert_outputs_to_stdout(tmp_path: Path, capsys):
    yaml_path = tmp_path / "pipeline.yaml"
    yaml_path.write_text(
        """\
apiVersion: tekton.dev/v1
kind: Pipeline
metadata: { name: cli-test }
spec:
  tasks:
    - name: hello
      taskSpec:
        steps:
          - name: step
            script: echo "hello"
        """
    )
    # Invoke the underlying command directly to avoid Click parsing quirks.
    convert_command(input=yaml_path, out=None, target="bash", source="tekton")
    output = capsys.readouterr().out
    assert "Workflow: cli-test" in output
    assert 'echo "hello"' in output
