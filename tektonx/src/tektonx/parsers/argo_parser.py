from __future__ import annotations

from typing import Any, Dict

import yaml

from tektonx.ir import Step, Task, Workflow


class ArgoParseError(Exception):
    """Raised when Argo YAML cannot be converted into the IR."""


def parse_argo_yaml(argo_yaml: str) -> Workflow:
    """Parse Argo Workflow YAML into the IR."""
    try:
        document = yaml.safe_load(argo_yaml) or {}
    except yaml.YAMLError as exc:
        raise ArgoParseError("Invalid YAML") from exc

    if not isinstance(document, dict):
        raise ArgoParseError("Argo document must be a mapping")

    api_version = str(document.get("apiVersion") or "")
    if not api_version.startswith("argoproj.io/"):
        raise ArgoParseError("Unsupported apiVersion (expected argoproj.io/*)")

    kind = str(document.get("kind") or "")
    if kind != "Workflow":
        raise ArgoParseError(f"Unsupported Argo kind: {kind} (only Workflow supported)")

    metadata = document.get("metadata") or {}
    workflow_name = str(metadata.get("name") or "unnamed")

    spec = document.get("spec") or {}
    templates = spec.get("templates") or []

    tasks = _parse_templates(templates)

    if not tasks:
        raise ArgoParseError("No templates found in Argo Workflow")

    return Workflow(name=workflow_name, tasks=tasks, metadata=dict(metadata))


def _parse_templates(templates: list) -> list[Task]:
    """Convert Argo templates into IR Tasks."""
    tasks = []
    for idx, template in enumerate(templates):
        if not isinstance(template, dict):
            continue

        name = str(template.get("name") or f"template{idx+1}")
        
        # Handle script template
        if "script" in template:
            script_def = template.get("script") or {}
            source = script_def.get("source") or ""
            steps = [Step(name=f"{name}-script", script=source)]
        
        # Handle container template
        elif "container" in template:
            container = template.get("container") or {}
            command = _ensure_list(container.get("command"))
            args = _ensure_list(container.get("args"))
            image = container.get("image")
            steps = [Step(name=f"{name}-container", command=command, args=args, image=image)]
        
        # Handle DAG/steps (just note them)
        elif "dag" in template or "steps" in template:
            steps = [Step(
                name=f"{name}-orchestration",
                script=f'echo "DAG/Steps template ({name}) - orchestrates other templates"'
            )]
        
        # Empty template
        else:
            steps = [Step(name=f"{name}-noop", script='echo "Empty template"')]

        tasks.append(Task(name=name, steps=steps))

    return tasks


def _ensure_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v is not None]
    return [str(value)]