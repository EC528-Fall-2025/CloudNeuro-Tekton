from __future__ import annotations

import re
from typing import Dict, Iterable, List, Tuple

from tektonx.ir import Step, Task, Workflow


class WDLParseError(Exception):
    """Raised when WDL cannot be converted into the IR."""


def parse_wdl(wdl_text: str) -> Workflow:
    """Parse a minimal subset of WDL into the IR."""
    if not wdl_text.strip():
        raise WDLParseError("Empty WDL document")

    task_defs = _extract_tasks(wdl_text)
    workflow_name, calls = _extract_workflow_calls(wdl_text)

    tasks: List[Task] = []

    if calls:
        for call in calls:
            steps = _clone_steps(task_defs.get(call["task_ref"], []))
            if not steps:
                steps = [
                    Step(
                        name=f'{call["name"]}-missing',
                        script=f'echo "Task {call["task_ref"]} not defined in WDL"',
                    )
                ]
            tasks.append(Task(name=call["name"], steps=steps, run_after=call["deps"]))
    elif task_defs:
        for name, steps in task_defs.items():
            tasks.append(Task(name=name, steps=_clone_steps(steps)))
    else:
        raise WDLParseError("No tasks found in WDL document")

    return Workflow(name=workflow_name or "unnamed", tasks=tasks, metadata={})


def _extract_tasks(src: str) -> Dict[str, List[Step]]:
    tasks: Dict[str, List[Step]] = {}
    for name, block in _extract_blocks(src, "task"):
        command_block = _extract_block(block, "command")
        if command_block:
            script = command_block.strip()
        else:
            script = f'echo "Task {name} has no command block"'
        tasks[name] = [Step(name=f"{name}-command", script=script)]
    return tasks


def _extract_workflow_calls(src: str) -> Tuple[str | None, List[Dict[str, object]]]:
    workflow_blocks = list(_extract_blocks(src, "workflow"))
    if not workflow_blocks:
        return None, []

    workflow_name, body = workflow_blocks[0]
    calls: List[Dict[str, object]] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("call "):
            continue
        match = re.match(
            r"call\s+([A-Za-z0-9_\.]+)(?:\s+as\s+([A-Za-z0-9_]+))?(?:\s+after\s+(.+))?",
            stripped,
        )
        if not match:
            continue
        task_ref = match.group(1)
        alias = match.group(2)
        deps_expr = match.group(3) or ""

        name = alias or task_ref.split(".")[-1]
        deps = _split_dep_expr(deps_expr)

        calls.append({"name": name, "task_ref": task_ref.split(".")[-1], "deps": deps})

    return workflow_name, calls


def _split_dep_expr(expr: str) -> List[str]:
    parts = (
        expr.replace("&&", ",")
        .replace("||", ",")
        .replace(",", " ")
        .split()
    )
    return [p for p in parts if p]


def _clone_steps(steps: List[Step]) -> List[Step]:
    cloned: List[Step] = []
    for step in steps:
        cloned.append(
            Step(
                name=step.name,
                script=step.script,
                command=list(step.command),
                args=list(step.args),
                image=step.image,
                env=dict(step.env),
                workdir=step.workdir,
            )
        )
    return cloned


def _extract_blocks(src: str, keyword: str) -> Iterable[Tuple[str, str]]:
    pattern = re.compile(rf"{keyword}\s+([A-Za-z0-9_]+)\s*\{{", re.MULTILINE)
    for match in pattern.finditer(src):
        name = match.group(1)
        open_idx = match.end() - 1
        close_idx = _find_matching_brace(src, open_idx)
        if close_idx == -1:
            continue
        body = src[open_idx + 1 : close_idx]
        yield name, body


def _extract_block(src: str, keyword: str) -> str | None:
    pattern = re.compile(rf"{keyword}\s*\{{", re.MULTILINE)
    match = pattern.search(src)
    if not match:
        return None
    open_idx = match.end() - 1
    close_idx = _find_matching_brace(src, open_idx)
    if close_idx == -1:
        return None
    return src[open_idx + 1 : close_idx]


def _find_matching_brace(src: str, open_idx: int) -> int:
    depth = 0
    for idx in range(open_idx, len(src)):
        char = src[idx]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return idx
    return -1
