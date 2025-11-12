from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence


class IRValidationError(Exception):
    """Raised when the intermediate representation is invalid."""


@dataclass
class Step:
    """Single container step originating from Tekton."""

    name: str
    script: str | None = None
    command: List[str] = field(default_factory=list)
    args: List[str] = field(default_factory=list)
    image: str | None = None
    env: Dict[str, str] = field(default_factory=dict)
    workdir: str | None = None

    def summary(self) -> str:
        """Short description for renderers."""
        if self.script:
            return f"script:{self.name}"
        if self.command:
            parts = self.command + self.args
            return "cmd:" + " ".join(parts[:3])
        return f"noop:{self.name}"


@dataclass
class Task:
    """Workflow task made up of ordered steps."""

    name: str
    steps: List[Step]
    run_after: List[str] = field(default_factory=list)
    description: str | None = None

    def dependencies(self) -> Sequence[str]:
        return tuple(dep for dep in self.run_after if dep)


@dataclass
class Workflow:
    """Top-level workflow, e.g. a Tekton Pipeline."""

    name: str
    tasks: List[Task]
    metadata: Dict[str, object] = field(default_factory=dict)

    def task_names(self) -> List[str]:
        return [task.name for task in self.tasks]

    def as_dict(self) -> Dict[str, object]:
        """Convert IR into a plain dict for simple renderers/debugging."""
        return {
            "name": self.name,
            "tasks": [
                {
                    "name": task.name,
                    "run_after": list(task.run_after),
                    "steps": [
                        {
                            "name": step.name,
                            "script": step.script,
                            "command": list(step.command),
                            "args": list(step.args),
                            "image": step.image,
                            "env": dict(step.env),
                            "workdir": step.workdir,
                        }
                        for step in task.steps
                    ],
                }
                for task in self.tasks
            ],
            "metadata": dict(self.metadata),
        }

    def validate(self) -> None:
        """Basic structural validation."""
        names = set()
        for task in self.tasks:
            if task.name in names:
                raise IRValidationError(f"Duplicate task name: {task.name}")
            names.add(task.name)
            for dep in task.run_after:
                if dep and dep not in names:
                    # Allow forward references but warn renderers later
                    continue
        return None
