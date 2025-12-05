import os
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

from tektonx.converter import convert


LINEAR_TEKTON = textwrap.dedent(
    """\
    apiVersion: tekton.dev/v1
    kind: Pipeline
    metadata: { name: exec-linear }
    spec:
      tasks:
        - name: prep
          taskSpec:
            steps:
              - name: prep-step
                script: |
                  echo "prep" > prep.txt
        - name: analyze
          runAfter: [prep]
          taskSpec:
            steps:
              - name: analyze-step
                script: |
                  echo "analyze" >> prep.txt
    """
)


def test_bash_execution_creates_output(tmp_path: Path):
    script_text = convert(LINEAR_TEKTON, target="bash", source="tekton")
    script_path = tmp_path / "workflow.sh"
    script_path.write_text(script_text)
    script_path.chmod(0o755)

    result = subprocess.run(
        ["bash", str(script_path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"

    output_file = tmp_path / "prep.txt"
    assert output_file.exists(), "prep.txt should be created by the bash run"
    content = output_file.read_text().strip().splitlines()
    assert "prep" in content and "analyze" in content


@pytest.mark.skipif(not shutil.which("snakemake"), reason="snakemake not installed")
def test_snakemake_execution_creates_done_files(tmp_path: Path, monkeypatch):
    snake_text = convert(LINEAR_TEKTON, target="snakemake", source="tekton")
    snakefile = tmp_path / "Snakefile"
    snakefile.write_text(snake_text)

    env = os.environ.copy()
    env.setdefault("XDG_CACHE_HOME", str(tmp_path))
    env.setdefault("TMPDIR", str(tmp_path))
    env.setdefault("WORKDIR", str(tmp_path))

    result = subprocess.run(
        ["snakemake", "-s", str(snakefile), "--cores", "1"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"

    # Snakemake renderer touches <task>.done for each task
    for name in ("prep.done", "analyze.done"):
        assert (tmp_path / name).exists(), f"{name} should be produced by snakemake run"
