from __future__ import annotations

from collections import deque
import shlex
import textwrap
from typing import Dict, Iterable, List, Set

from tektonx.ir import Step, Task, Workflow


def render(workflow: Workflow) -> str:
    """Render the workflow as a minimal Nextflow DSL2 script."""
    header = ["nextflow.enable.dsl=2", ""]
    processes = [_process_block(task) for task in workflow.tasks]
    ordered_tasks = _toposort(workflow.tasks)
    workflow_calls = _workflow_block(ordered_tasks)
    return "\n\n".join(header + processes + [workflow_calls]) + "\n"


def _process_block(task: Task) -> str:
    lines: List[str] = [f"process {_identifier(task.name)} {{", "    script:", '    """']
    body = ["set -euo pipefail"]
    for step in task.steps or [Step(name="noop")]:
        body.append(f'echo "[{task.name}] Step: {step.name}"')
        body.extend(_step_lines(step))
    for line in body:
        lines.append(f"    {line}")
    lines.append('    """')
    lines.append("}")
    return "\n".join(lines)


def _step_lines(step: Step) -> List[str]:
    if step.script:
        script = textwrap.dedent(step.script).strip()
        return script.splitlines()

    cmd = _command_line(step)
    if cmd:
        return [cmd]

    return ['echo "(noop step)"']


def _workflow_block(tasks: List[Task]) -> str:
    lines: List[str] = ["workflow {"]
    for task in tasks:
        deps = [d for d in task.run_after if d]
        dep_comment = f" // after {', '.join(deps)}" if deps else ""
        lines.append(f"    {_identifier(task.name)}(){dep_comment}")
    lines.append("}")
    return "\n".join(lines)


def _toposort(tasks: Iterable[Task]) -> List[Task]:
    """Simple topo sort based on run_after; preserves input order when possible."""
    name_to_task: Dict[str, Task] = {t.name: t for t in tasks}
    indegree: Dict[str, int] = {t.name: 0 for t in tasks}
    graph: Dict[str, Set[str]] = {t.name: set() for t in tasks}

    for task in tasks:
        for dep in task.run_after:
            if dep in graph:
                graph[dep].add(task.name)
                indegree[task.name] += 1

    queue = deque([name for name, deg in indegree.items() if deg == 0])
    ordered: List[Task] = []
    while queue:
        name = queue.popleft()
        ordered.append(name_to_task[name])
        for neighbor in graph.get(name, []):
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

    # Append any leftover tasks (cycles/unresolved) in original order
    for task in tasks:
        if task not in ordered:
            ordered.append(task)
    return ordered


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
    reserved = {
        "as",
        "assert",
        "break",
        "case",
        "catch",
        "class",
        "const",
        "continue",
        "def",
        "default",
        "do",
        "else",
        "enum",
        "extends",
        "false",
        "finally",
        "for",
        "goto",
        "if",
        "implements",
        "import",
        "in",
        "instanceof",
        "interface",
        "new",
        "null",
        "package",
        "return",
        "super",
        "switch",
        "this",
        "throw",
        "throws",
        "trait",
        "true",
        "try",
        "while",
    }
    if filtered in reserved:
        filtered = f"t_{filtered}"
    return filtered
