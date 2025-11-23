import json
import textwrap
from typing import Dict

from tektonx.ir import Workflow


def render(workflow: Workflow) -> str:
    """Render a Tekton workflow into a ChRIS plugin `app.py` skeleton."""
    payload = workflow.as_dict()
    return _plugin_template(workflow.name, payload)


def _plugin_template(name: str, workflow_payload: Dict[str, object]) -> str:
    workflow_json = json.dumps(workflow_payload, indent=4)
    template = """#!/usr/bin/env python
\"\"\"ChRIS plugin auto-generated from Tekton workflow '__WORKFLOW_NAME__'.

Limitations for miniChRIS:
- All Tekton steps run inside a single plugin container.
- Original Tekton step images are reported for review only.
- Ensure the container bundles the tools needed by each step.
\"\"\"

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from textwrap import dedent
from typing import Dict, List

from chris_plugin import chris_plugin

__version__ = "0.1.0"

WORKFLOW: Dict[str, object] = json.loads(r\"\"\"__WORKFLOW_JSON__\"\"\")

parser = argparse.ArgumentParser(
    description=dedent(
        \"\"\"Run the Tekton workflow '__WORKFLOW_NAME__' sequentially inside a ChRIS plugin.
Tekton images are not pulled; commands run in this container.\"\"\"
    ),
)
parser.add_argument(
    "--workdir",
    default=None,
    help="Workspace inside the container to run steps (default: outputdir)",
)
parser.add_argument(
    "--continue-on-error",
    action="store_true",
    help="Record failures and move on instead of aborting on first error.",
)


@chris_plugin(
    parser=parser,
    title="Tekton workflow: __WORKFLOW_NAME__",
    category="Workflow",
    plugin_type="ds",
    min_number_of_workers=1,
    max_number_of_workers=1,
)
def main(options: argparse.Namespace, inputdir: Path, outputdir: Path) -> None:
    workspace = Path(options.workdir or outputdir)
    workspace.mkdir(parents=True, exist_ok=True)
    env = _base_env(options, inputdir, outputdir)
    report: Dict[str, object] = {
        "workflow": WORKFLOW.get("name", "__WORKFLOW_NAME__"),
        "metadata": WORKFLOW.get("metadata", {}),
        "tasks": [],
    }

    try:
        for task in _ordered_tasks(WORKFLOW.get("tasks", [])):
            task_report: Dict[str, object] = {"name": task.get("name"), "steps": []}
            print(f"=== Task: {task.get('name')} ===")
            try:
                _run_task(task, workspace, env, task_report, options.continue_on_error)
                task_report["status"] = "completed"
            except subprocess.CalledProcessError as exc:
                task_report["status"] = "failed"
                task_report["error"] = str(exc)
                report["tasks"].append(task_report)
                _write_report(report, outputdir)
                if not options.continue_on_error:
                    raise
            else:
                report["tasks"].append(task_report)
    finally:
        _write_report(report, outputdir)


def _base_env(options: argparse.Namespace, inputdir: Path, outputdir: Path) -> Dict[str, str]:
    env = dict(os.environ)
    env.setdefault("INPUTDIR", str(inputdir))
    env.setdefault("OUTPUTDIR", str(outputdir))
    env.setdefault("WORKDIR", str(options.workdir or outputdir))
    return env


def _ordered_tasks(tasks: List[Dict[str, object]]):
    pending: Dict[str, Dict[str, object]] = {}
    for task in tasks:
        name = str(task.get("name"))
        pending[name] = task

    completed: set[str] = set()
    while pending:
        progressed = False
        for name, task in list(pending.items()):
            deps = [d for d in task.get("run_after", []) if d]
            if not set(deps).issubset(completed):
                continue
            yield task
            completed.add(name)
            pending.pop(name)
            progressed = True
        if not progressed:
            unresolved = ", ".join(sorted(pending))
            raise RuntimeError(
                f"Unresolvable or cyclic dependencies across tasks: {unresolved}"
            )


def _run_task(
    task: Dict[str, object],
    workspace: Path,
    base_env: Dict[str, str],
    task_report: Dict[str, object],
    continue_on_error: bool,
) -> None:
    for step in task.get("steps", []):
        step_result: Dict[str, object] = {
            "name": step.get("name"),
            "image": step.get("image"),
        }
        try:
            _run_step(step, workspace, base_env)
        except subprocess.CalledProcessError as exc:
            step_result["status"] = "failed"
            step_result["error"] = str(exc)
            task_report["steps"].append(step_result)
            if not continue_on_error:
                raise
        else:
            step_result["status"] = "completed"
            task_report["steps"].append(step_result)


def _run_step(step: Dict[str, object], workspace: Path, base_env: Dict[str, str]) -> None:
    name = step.get("name") or "step"
    image = step.get("image")
    if image:
        print(
            f"[info] Tekton step '{name}' referenced image '{image}'; running inside plugin container."
        )
    env = dict(base_env)
    env.update({str(k): str(v) for k, v in (step.get("env") or {}).items()})
    cwd = Path(step.get("workdir") or workspace)
    cmd = _materialize_command(step)
    if not cmd:
        print(f"[skip] {name}: no command or script to run.")
        return
    print(f"[run] {name}: {' '.join(cmd)} (cwd={cwd})")
    subprocess.run(cmd, check=True, cwd=cwd, env=env)


def _materialize_command(step: Dict[str, object]) -> List[str]:
    script = step.get("script")
    if script:
        body = dedent(str(script)).strip("\\n")
        if not body:
            return []
        return ["bash", "-lc", body]
    parts = []
    parts.extend([str(p) for p in step.get("command") or [] if p is not None])
    parts.extend([str(p) for p in step.get("args") or [] if p is not None])
    return [p for p in parts if p]


def _write_report(report: Dict[str, object], outputdir: Path) -> None:
    outputdir.mkdir(parents=True, exist_ok=True)
    report_path = outputdir / "workflow_report.json"
    report_path.write_text(json.dumps(report, indent=2))
    print(f"[info] Wrote execution report to {report_path}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        sys.stderr.write(f"Workflow failed: {exc}\\n")
        sys.exit(1)
"""
    return (
        textwrap.dedent(template)
        .replace("__WORKFLOW_NAME__", name)
        .replace("__WORKFLOW_JSON__", workflow_json)
        .rstrip()
        + "\n"
    )
