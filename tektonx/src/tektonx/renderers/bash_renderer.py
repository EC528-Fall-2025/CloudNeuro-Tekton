from __future__ import annotations

import shlex
import textwrap
from typing import List

from tektonx.ir import Step, Task, Workflow


def render(workflow: Workflow) -> str:
    lines: List[str] = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f'echo "=== Workflow: {workflow.name} ==="',
    ]

    for task in workflow.tasks:
        lines.append(f'echo "=== Task: {task.name} ==="')
        lines.extend(_render_task(task))

    return "\n".join(lines).rstrip() + "\n"


def _render_task(task: Task) -> List[str]:
    task_lines: List[str] = []
    for step in task.steps:
        task_lines.append(f'echo "--- Step: {step.name} ---"')
        task_lines.extend(_render_step(step))
        task_lines.append("")
    return task_lines


def _render_step(step: Step) -> List[str]:
    if step.script:
        script = textwrap.dedent(step.script).strip("\n")
        return [script]

    cmdline = _command_line(step)
    if cmdline:
        return [cmdline]

    return ['echo "(no-op step)"']


def _command_line(step: Step) -> str:
    if not step.command and not step.args:
        return ""
    parts = list(step.command) + list(step.args)
    return " ".join(shlex.quote(part) for part in parts if part)
