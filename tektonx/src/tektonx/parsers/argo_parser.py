from __future__ import annotations

from typing import Any, Dict, List, Set

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
    template_lookup = _index_templates(templates)

    tasks = _parse_templates(templates, template_lookup)

    if not tasks:
        raise ArgoParseError("No templates found in Argo Workflow")

    return Workflow(name=workflow_name, tasks=tasks, metadata=dict(metadata))


def _parse_templates(templates: list, template_lookup: Dict[str, Dict[str, Any]]) -> list[Task]:
    """Convert Argo templates into IR Tasks with DAG edges if present."""
    tasks: List[Task] = []
    referenced_templates: Set[str] = set()

    # First, expand DAG templates into individual tasks with dependencies.
    for template in templates:
        if not isinstance(template, dict):
            continue
        if "dag" in template:
            dag_tasks = _expand_dag_template(template, template_lookup)
            referenced_templates.update(_collect_referenced_templates(template))
            tasks.extend(dag_tasks)

    # Next, add non-DAG templates that were not consumed by a DAG.
    for idx, template in enumerate(templates):
        if not isinstance(template, dict):
            continue
        name = str(template.get("name") or f"template{idx+1}")
        if "dag" in template or name in referenced_templates:
            continue
        tasks.append(_task_from_template(name, template))

    return tasks


def _index_templates(templates: list) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    for idx, template in enumerate(templates):
        if isinstance(template, dict):
            name = str(template.get("name") or f"template{idx+1}")
            lookup[name] = template
    return lookup


def _collect_referenced_templates(template: Dict[str, Any]) -> Set[str]:
    dag = template.get("dag") or {}
    dag_tasks = dag.get("tasks") or []
    refs = set()
    for task in dag_tasks:
        if isinstance(task, dict) and task.get("template"):
            refs.add(str(task.get("template")))
    return refs


def _expand_dag_template(template: Dict[str, Any], template_lookup: Dict[str, Dict[str, Any]]) -> List[Task]:
    """Expand a DAG template into IR Tasks with run_after dependencies."""
    dag = template.get("dag") or {}
    dag_tasks = dag.get("tasks") or []
    tasks: List[Task] = []
    template_name = str(template.get("name") or "dag")

    for idx, dag_task in enumerate(dag_tasks):
        if not isinstance(dag_task, dict):
            continue
        name = str(dag_task.get("name") or f"{template_name}-task{idx+1}")
        template_ref = str(dag_task.get("template") or name)
        deps = _parse_dependencies(dag_task)

        target_template = template_lookup.get(template_ref, {})
        steps = _steps_from_template(target_template, template_ref)

        tasks.append(Task(name=name, steps=steps, run_after=deps))

    return tasks


def _task_from_template(name: str, template: Dict[str, Any]) -> Task:
    """Convert a single Argo template into an IR Task (no DAG semantics)."""
    steps = _steps_from_template(template, name)
    return Task(name=name, steps=steps)


def _steps_from_template(template: Dict[str, Any], name: str) -> List[Step]:
    if "script" in template:
        script_def = template.get("script") or {}
        source = script_def.get("source") or ""
        return [Step(name=f"{name}-script", script=source)]

    if "container" in template:
        container = template.get("container") or {}
        command = _ensure_list(container.get("command"))
        args = _ensure_list(container.get("args"))
        image = container.get("image")
        return [Step(name=f"{name}-container", command=command, args=args, image=image)]

    if "steps" in template:
        return [
            Step(
                name=f"{name}-orchestration",
                script=f'echo "Steps template ({name}) - orchestrates other templates"',
            )
        ]

    return [Step(name=f"{name}-noop", script='echo "Empty template"')]


def _parse_dependencies(dag_task: Dict[str, Any]) -> List[str]:
    """Extract dependencies from Argo DAG task (dependencies or depends expression)."""
    deps = dag_task.get("dependencies") or []
    parsed = _ensure_list(deps)

    depends_expr = dag_task.get("depends")
    if depends_expr:
        parsed.extend(_split_dep_expr(str(depends_expr)))

    # Deduplicate while preserving order
    seen: Set[str] = set()
    ordered: List[str] = []
    for dep in parsed:
        if dep and dep not in seen:
            seen.add(dep)
            ordered.append(dep)
    return ordered


def _split_dep_expr(expr: str) -> List[str]:
    """Split simple Argo 'depends' expressions (AND/OR) into dependency names."""
    parts = (
        expr.replace("&&", ",")
        .replace("||", ",")
        .replace(" ", ",")
        .split(",")
    )
    return [p for p in (part.strip() for part in parts) if p]


def _ensure_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v is not None]
    return [str(value)]
