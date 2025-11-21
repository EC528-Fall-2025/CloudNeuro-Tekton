from __future__ import annotations

from typing import Any

import yaml

from tektonx.ir import Step, Task, Workflow


class NextflowParseError(Exception):
    """Raised when Nextflow YAML cannot be converted into the IR."""


def parse_nextflow_yaml(nextflow_yaml: str) -> Workflow:
    """Parse Nextflow workflow YAML into the IR."""
    try:
        document = yaml.safe_load(nextflow_yaml) or {}
    except yaml.YAMLError as exc:
        raise NextflowParseError("Invalid YAML") from exc

    if not isinstance(document, dict):
        raise NextflowParseError("Nextflow document must be a mapping")

    # Nextflow YAML doesn't have a standard apiVersion, look for processes
    workflow_name = str(document.get("name") or document.get("workflow", {}).get("name") or "unnamed")
    
    # Look for processes in different locations
    processes = (
        document.get("processes") or 
        document.get("workflow", {}).get("processes") or 
        []
    )

    if not processes:
        raise NextflowParseError("No processes found in Nextflow workflow")

    tasks = _parse_processes(processes)

    return Workflow(name=workflow_name, tasks=tasks, metadata={})


def _parse_processes(processes: list) -> list[Task]:
    """Convert Nextflow processes into IR Tasks."""
    tasks = []
    for idx, process in enumerate(processes):
        if not isinstance(process, dict):
            continue

        name = str(process.get("name") or f"process{idx+1}")
        
        # Look for script, shell, or exec directive
        script = (
            process.get("script") or 
            process.get("shell") or 
            process.get("exec") or 
            ""
        )

        if script:
            steps = [Step(name=f"{name}-step", script=str(script))]
        else:
            steps = [Step(name=f"{name}-noop", script='echo "No script defined"')]

        tasks.append(Task(name=name, steps=steps))

    return tasks