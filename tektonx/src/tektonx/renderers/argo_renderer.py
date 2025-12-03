from __future__ import annotations

import shlex
import textwrap
from typing import Dict, List

import yaml

from tektonx.ir import Step, Task, Workflow


def render(workflow: Workflow) -> str:
    """
    Render the workflow as an Argo Workflow (script templates).

    - Each Tekton task becomes a script template.
    - Dependencies map to DAG task dependencies.
    """
    templates: List[Dict[str, object]] = []

    # DAG entrypoint template
    dag_tasks = [_dag_task(task) for task in workflow.tasks]
    templates.append({"name": "main", "dag": {"tasks": dag_tasks}})

    # One script template per task
    for task in workflow.tasks:
        templates.append(_script_template(task))

    workflow_obj = {
        "apiVersion": "argoproj.io/v1alpha1",
        "kind": "Workflow",
        "metadata": {"name": workflow.name},
        "spec": {"entrypoint": "main", "templates": templates},
    }

    return yaml.safe_dump(workflow_obj, sort_keys=False)


def _dag_task(task: Task) -> Dict[str, object]:
    dag_task: Dict[str, object] = {"name": task.name, "template": task.name}
    deps = [d for d in task.run_after if d]
    if deps:
        dag_task["dependencies"] = deps
    return dag_task


def _script_template(task: Task) -> Dict[str, object]:
    script_lines: List[str] = ["set -euo pipefail"]
    for step in task.steps or [Step(name="noop")]:
        script_lines.append(f'echo "[{task.name}] Step: {step.name}"')
        script_lines.extend(_step_body(step))

    return {
        "name": task.name,
        "script": {
            "image": "ubuntu:22.04",
            "command": ["/bin/bash", "-lc"],
            "source": "\n".join(script_lines) + "\n",
        },
    }


def _step_body(step: Step) -> List[str]:
    if step.script:
        body = textwrap.dedent(step.script).strip("\n")
        return body.splitlines()

    cmd = _command_line(step)
    if cmd:
        return [cmd]

    return ['echo "(noop step)"']


def _command_line(step: Step) -> str:
    parts = list(step.command) + list(step.args)
    if not parts:
        return ""
    return " ".join(shlex.quote(p) for p in parts if p)
