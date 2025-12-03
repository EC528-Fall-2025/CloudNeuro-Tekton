from __future__ import annotations

import shlex
import textwrap
from typing import List

from tektonx.ir import Step, Task, Workflow


def render(workflow: Workflow) -> str:
    task_names = [task.name for task in workflow.tasks]
    phony_targets = " ".join(["all"] + task_names)
    lines: List[str] = ["SHELL := bash", f".PHONY: {phony_targets}", ""]
    all_deps = " ".join(task_names)
    lines.append(f"all: {all_deps}".rstrip())
    lines.append("\t@echo \"Completed workflow: {name}\"".format(name=workflow.name))
    lines.append("")

    for task in workflow.tasks:
        deps = " ".join(dep for dep in task.run_after if dep)
        lines.append(f".PHONY: {task.name}")
        lines.append(f"{task.name}:{(' ' + deps) if deps else ''}".rstrip())
        if not task.steps:
            lines.append(f'\t@echo "Task {task.name} has no steps"')
        else:
            lines.extend(_render_task(task))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_task(task: Task) -> List[str]:
    task_lines: List[str] = []
    for step in task.steps:
        task_lines.append(f'\t@echo "[{task.name}] Step: {step.name}"')
        if step.script:
            task_lines.append(_script_block(step.script))
        else:
            # If any arg contains newlines, render via inline bash block for safety.
            if any("\n" in arg for arg in step.args):
                script_body = "\n".join(step.args)
                task_lines.append(_heredoc_block(script_body))
            else:
                cmd = _command_line(step)
                if cmd:
                    task_lines.append(f"\t{_indent_multiline(_escape_make(cmd))}")
                else:
                    task_lines.append('\t@echo "(noop step)"')
    return task_lines


def _command_line(step: Step) -> str:
    parts = list(step.command) + list(step.args)
    if not parts:
        return ""
    return " ".join(shlex.quote(part) for part in parts if part)


def _indent_multiline(command: str) -> str:
    """Ensure embedded newlines stay within the same make recipe."""
    if "\n" not in command:
        return command
    return command.replace("\n", "\n\t")


def _escape_make(text: str) -> str:
    """Escape dollar signs so Make passes them to the shell."""
    return text.replace("$", "$$")


def _script_block(script: str) -> str:
    """Render scripts as a single bash -lc invocation (works on make 3.81)."""
    return _bash_inline_block(script)


def _heredoc_block(content: str) -> str:
    """Render arbitrary multiline content via a single bash -lc invocation."""
    return _bash_inline_block(content)


def _bash_inline_block(script: str) -> str:
    """Encode the script for bash -lc using ANSI-C quoting, safe for old make."""
    body = textwrap.dedent(script).strip()
    if not body:
        return '\t@echo "(noop step)"'

    # Escape for make expansion, then for bash $'...' ANSI-C quoting.
    make_safe = _escape_make(body)
    ansi_safe = (
        make_safe.replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\n", "\\n")
    )
    return f"\tbash -lc $$'{ansi_safe}'"
