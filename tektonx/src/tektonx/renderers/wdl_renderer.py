from __future__ import annotations

import shlex
import textwrap
from typing import List

from tektonx.ir import Step, Task, Workflow


def render(workflow: Workflow) -> str:
    """Render the workflow as a minimal WDL document (tasks + workflow block)."""
    safe_wf_name = _identifier(workflow.name) or "workflow"
    task_blocks = [_task_block(task) for task in workflow.tasks]
    workflow_block = _workflow_block(safe_wf_name, workflow.tasks)
    return "\n\n".join(task_blocks + [workflow_block]) + "\n"


def _task_block(task: Task) -> str:
    body: List[str] = ["task {name} {{".format(name=_identifier(task.name))]
    body.append("  command {")
    body.append("    set -euo pipefail")
    for step in task.steps or [Step(name="noop")]:
        body.extend(_render_step(step, indent="    "))
    body.append("  }")
    body.append("}")
    return "\n".join(body)


def _workflow_block(name: str, tasks: List[Task]) -> str:
    lines: List[str] = [f"workflow {name} {{"]
    for task in tasks:
        call = f"  call {_identifier(task.name)}"
        lines.append(call)
        if task.run_after:
            deps = ", ".join(_identifier(dep) for dep in task.run_after if dep)
            lines.append(f"  # after: {deps}")
    lines.append("}")
    return "\n".join(lines)


def _render_step(step: Step, indent: str) -> List[str]:
    lines: List[str] = []
    lines.append(f'{indent}# Step: {step.name}')
    if step.script:
        script = textwrap.dedent(step.script).strip()
        for line in script.splitlines():
            lines.append(f"{indent}{line}")
        return lines

    cmd = _command_line(step)
    if cmd:
        lines.append(f"{indent}{cmd}")
        return lines

    lines.append(f'{indent}echo "(noop step)"')
    return lines


def _command_line(step: Step) -> str:
    parts = list(step.command) + list(step.args)
    if not parts:
        return ""
    return " ".join(shlex.quote(p) for p in parts if p)


def _identifier(name: str) -> str:
    filtered = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in name)
    if not filtered:
        filtered = "task"
    if filtered[0].isdigit():
        filtered = f"t_{filtered}"
    return filtered
