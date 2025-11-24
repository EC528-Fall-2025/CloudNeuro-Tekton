from __future__ import annotations

from typing import Any, Dict, List, Sequence

import yaml

from tektonx.ir import Step, Task, Workflow


class TektonParseError(Exception):
    """Raised when Tekton YAML cannot be converted into the IR."""


def parse_tekton_yaml(tekton_yaml: str) -> Workflow:
    """Parse Tekton YAML (Task/TaskRun/Pipeline/PipelineRun) into the IR."""
    try:
        documents = [doc for doc in yaml.safe_load_all(tekton_yaml) if doc]
    except yaml.YAMLError as exc:
        raise TektonParseError("Invalid YAML") from exc

    if not documents:
        raise TektonParseError("Tekton document must be a mapping")

    primary = _select_primary_doc(documents)
    if primary is None or not isinstance(primary, dict):
        raise TektonParseError("Tekton document must be a mapping")

    api_version = str(primary.get("apiVersion") or "")
    if not api_version.startswith("tekton.dev/"):
        raise TektonParseError("Unsupported apiVersion")

    kind = str(primary.get("kind") or "")
    metadata = primary.get("metadata") or {}
    workflow_name = str(metadata.get("name") or "unnamed")

    task_catalog = _catalog_tasks(documents)

    if kind in {"Task", "TaskRun"}:
        tasks = [_parse_task_like(primary)]
    elif kind in {"Pipeline", "PipelineRun"}:
        tasks = _parse_pipeline_like(primary, task_catalog)
    else:
        raise TektonParseError(f"Unsupported Tekton kind: {kind}")

    if not tasks:
        raise TektonParseError("No tasks extracted from Tekton document")

    return Workflow(name=workflow_name, tasks=tasks, metadata=dict(metadata))


def _select_primary_doc(documents: Sequence[object]) -> Dict[str, Any] | None:
    """Pick the primary Tekton document to parse."""
    for doc in documents:
        if isinstance(doc, dict) and str(doc.get("kind") or "") in {"Pipeline", "PipelineRun"}:
            return doc
    for doc in documents:
        if isinstance(doc, dict):
            return doc
    return None


def _catalog_tasks(documents: Sequence[object]) -> Dict[str, Dict[str, Any]]:
    """Build a lookup of Task definitions by name for inlining taskRefs."""
    tasks: Dict[str, Dict[str, Any]] = {}
    for doc in documents:
        if not isinstance(doc, dict):
            continue
        kind = str(doc.get("kind") or "")
        if kind != "Task":
            continue
        md = doc.get("metadata") or {}
        name = str(md.get("name") or "")
        if name:
            tasks[name] = doc
    return tasks


def _parse_task_like(document: Dict[str, Any]) -> Task:
    """Convert Tekton Task/TaskRun into a single IR Task."""
    kind = document.get("kind")
    metadata = document.get("metadata") or {}
    task_name = str(metadata.get("name") or "task")

    if kind == "Task":
        spec = document.get("spec") or {}
        steps = _parse_steps(spec.get("steps") or [])
    else:  # TaskRun
        spec = document.get("spec") or {}
        task_spec = spec.get("taskSpec") or {}
        if not task_spec and spec.get("taskRef"):
            ref = spec["taskRef"]
            ref_name = ref.get("name") or "referenced-task"
            steps = [
                Step(
                    name="external-task",
                    script=(
                        'echo "TaskRun references existing Tekton Task '
                        f'({ref_name}); fetch and inline it to render commands."'
                    ),
                )
            ]
        else:
            steps = _parse_steps(task_spec.get("steps") or [])

    if not steps:
        raise TektonParseError("Task/TaskRun does not define any steps")

    return Task(name=task_name, steps=steps)


def _parse_pipeline_like(document: Dict[str, Any], task_catalog: Dict[str, Dict[str, Any]]) -> List[Task]:
    """Convert a Tekton Pipeline/PipelineRun into IR Tasks."""
    if document.get("kind") == "PipelineRun":
        spec = (document.get("spec") or {}).get("pipelineSpec") or {}
    else:
        spec = document.get("spec") or {}

    task_defs = spec.get("tasks") or []
    tasks: List[Task] = []
    for idx, task_def in enumerate(task_defs):
        if not isinstance(task_def, dict):
            continue
        name = str(task_def.get("name") or f"task{idx+1}")
        run_after = [str(dep) for dep in task_def.get("runAfter") or []]

        if "taskSpec" in task_def:
            steps = _parse_steps((task_def.get("taskSpec") or {}).get("steps") or [])
        elif "taskRef" in task_def:
            ref = task_def.get("taskRef") or {}
            ref_name = ref.get("name") or "referenced-task"
            if ref_name in task_catalog:
                steps = _steps_from_task_doc(task_catalog[ref_name])
            else:
                steps = [
                    Step(
                        name=f"reference-{ref_name}",
                        script=(
                            'echo "This task references Tekton Task '
                            f'{ref_name}. Inline its spec before rendering."'
                        ),
                    )
                ]
        else:
            steps = []

        if not steps:
            steps = [
                Step(
                    name=f"{name}-noop",
                    script='echo "No steps defined in Tekton task; nothing to run."',
                )
            ]

        tasks.append(Task(name=name, steps=steps, run_after=run_after))

    return tasks


def _parse_steps(step_defs: List[Dict[str, Any]]) -> List[Step]:
    steps: List[Step] = []
    for idx, step_def in enumerate(step_defs):
        if not isinstance(step_def, dict):
            continue
        name = str(step_def.get("name") or f"step{idx+1}")
        script = step_def.get("script")
        command = _ensure_list(step_def.get("command"))
        args = _ensure_list(step_def.get("args"))
        env = _env_as_dict(step_def.get("env"))
        image = step_def.get("image")
        workdir = step_def.get("workingDir")
        steps.append(
            Step(
                name=name,
                script=script,
                command=command,
                args=args,
                env=env,
                image=image,
                workdir=workdir,
            )
        )
    return steps


def _steps_from_task_doc(task_doc: Dict[str, Any]) -> List[Step]:
    spec = task_doc.get("spec") or {}
    return _parse_steps(spec.get("steps") or [])


def _ensure_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v is not None]
    return [str(value)]


def _env_as_dict(env_value: Any) -> Dict[str, str]:
    if isinstance(env_value, dict):
        return {str(k): str(v) for k, v in env_value.items()}
    if isinstance(env_value, list):
        env_dict: Dict[str, str] = {}
        for item in env_value:
            if isinstance(item, dict) and "name" in item:
                name = str(item["name"])
                value = item.get("value")
                if value is not None:
                    env_dict[name] = str(value)
        return env_dict
    return {}
