
import shlex
import textwrap
from typing import Dict, List

from tektonx.ir import Step, Workflow


def render(workflow: Workflow) -> str:
    """
    Render the workflow as a bash script that submits one Sun Grid Engine job per task.

    - Each Tekton Task becomes a single `qsub` job.
    - Task `run_after` dependencies become `-hold_jid <job-ids>`.
    """
    lines: List[str] = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f'echo "Submitting Sun Grid Engine workflow: {workflow.name}"',
        "",
    ]

    # Map Tekton task name -> bash variable holding its SGE job ID
    job_ids: Dict[str, str] = {}

    for task in workflow.tasks:
        job_var = _job_var(task.name)
        deps = [dep for dep in task.run_after if dep in job_ids]

        hold_opt = ""
        if deps:
            dep_expr = ",".join(f"${job_ids[d]}" for d in deps)
            hold_opt = f"-hold_jid {dep_expr} "

        lines.append(f'echo "Submitting task {task.name}..."')

        # Typical qsub output: "Your job 12345 ("name") has been submitted"
        lines.append(
            f'{job_var}=$(qsub {hold_opt}<< "EOF" | awk \'{{print $3}}\')'
        )
        lines.append("#!/usr/bin/env bash")
        lines.append("set -euo pipefail")

        for step in task.steps or [Step(name="noop")]:
            lines.append(f'echo "[{task.name}] Step: {step.name}"')
            for cmd in _step_commands(step):
                lines.append(cmd)

        lines.append("EOF")
        lines.append(f'echo "  Task {task.name} submitted as ${job_var}"')
        lines.append("")

        job_ids[task.name] = job_var

    lines.append('echo "All Sun Grid Engine jobs submitted."')
    return "\n".join(lines).rstrip() + "\n"


def _step_commands(step: Step) -> List[str]:
    """Turn a Step into a list of shell commands."""
    if step.script:
        return textwrap.dedent(step.script).strip().splitlines()

    cmd = _command_line(step)
    if cmd:
        return [cmd]

    return ['echo "(noop step)"']


def _command_line(step: Step) -> str:
    parts = list(step.command) + list(step.args)
    if not parts:
        return ""
    return " ".join(shlex.quote(part) for part in parts if part)


def _job_var(task_name: str) -> str:
    """Create a safe bash variable name for storing a job id."""
    base = "".join(ch if ch.isalnum() else "_" for ch in task_name)
    if not base:
        base = "task"
    if base[0].isdigit():
        base = f"t_{base}"
    return f"JOB_{base}"
