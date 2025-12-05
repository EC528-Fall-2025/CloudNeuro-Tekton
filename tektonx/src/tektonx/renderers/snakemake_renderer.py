from __future__ import annotations

import shlex
import textwrap
from typing import Dict, List

from tektonx.ir import Step, Task, Workflow


def render(workflow: Workflow) -> str:
    safe_names = _unique_rule_names(workflow.tasks)
    outputs = ", ".join(f'"{task.name}.done"' for task in workflow.tasks)
    lines: List[str] = ["rule all:", "    input:", f"        {outputs}", ""]

    for task in workflow.tasks:
        lines.extend(_render_task(task, safe_names[task.name]))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_task(task: Task, rule_name: str) -> List[str]:
    task_lines: List[str] = [f"# Tekton task: {task.name}", f"rule {rule_name}:"]
    if task.run_after:
        task_lines.append("    input:")
        deps = ", ".join(f'"{dep}.done"' for dep in task.run_after)
        task_lines.append(f"        {deps}")
    task_lines.append("    output:")
    task_lines.append(f'        "{task.name}.done"')
    task_lines.append("    run:")
    task_lines.append("        shell(r'''")
    for step in task.steps or [Step(name="noop")]:
        task_lines.append(f'            echo "[{task.name}] Step: {step.name}"')
        for line in _step_commands(step):
            task_lines.append(f"            {line}")
    task_lines.append("            touch {output}")
    task_lines.append("        ''')")
    return task_lines


def _step_commands(step: Step) -> List[str]:
    if step.script:
        script = textwrap.dedent(step.script).strip()
        # Escape braces so Snakemake's formatter does not treat shell ${VAR} as placeholders
        script = script.replace("{", "{{").replace("}", "}}")
        return script.splitlines()
    cmd = _command_line(step)
    if cmd:
        return [cmd]
    return ['echo "(noop step)"']


def _command_line(step: Step) -> str:
    parts = list(step.command) + list(step.args)
    if not parts:
        return ""
    return " ".join(shlex.quote(part) for part in parts if part)


def _unique_rule_names(tasks: List[Task]) -> Dict[str, str]:
    """Map Tekton task names to valid, unique Snakemake rule names."""
    safe: Dict[str, str] = {}
    used: set[str] = {"all"}
    for task in tasks:
        base = _identifier(task.name)
        candidate = base
        i = 1
        while candidate in used:
            candidate = f"{base}_{i}"
            i += 1
        used.add(candidate)
        safe[task.name] = candidate
    return safe


def _identifier(name: str) -> str:
    filtered = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in name)
    if not filtered:
        filtered = "task"
    if filtered[0].isdigit():
        filtered = f"t_{filtered}"
    return filtered
