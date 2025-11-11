from __future__ import annotations
from typing import Any, Dict, List, Tuple
import textwrap
import yaml


class ConversionError(Exception):
    """Custom error for invalid or unsupported Tekton YAMLs."""
    pass


def _header(title: str) -> str:
    return textwrap.dedent(f"""\
#!/usr/bin/env bash
set -euo pipefail
echo "=== {title} ==="
""")


def _join_cmd_args(command, args) -> str:
    """Combine command and args into one line of bash."""
    parts: List[str] = []
    if isinstance(command, list): parts += command
    elif isinstance(command, str) and command: parts.append(command)
    if isinstance(args, list): parts += args
    elif isinstance(args, str) and args: parts.append(args)
    return " ".join(parts) if parts else 'echo "(no explicit command/args)"'


def _kind_name(doc: Dict[str, Any]) -> Tuple[str, str]:
    """Return (kind, metadata.name) from a Tekton doc."""
    kind = str(doc.get("kind", ""))
    name = str((doc.get("metadata") or {}).get("name", "unnamed"))
    return kind, name


def _convert_tekton(doc: Dict[str, Any]) -> str:
    """Convert a Tekton Task or TaskRun into a bash script."""
    kind, name = _kind_name(doc)
    if kind not in {"Task", "TaskRun"}:
        raise ConversionError(f"Unsupported kind: {kind}. Only Task or TaskRun supported.")

    # Extract steps
    if kind == "Task":
        steps = ((doc.get("spec") or {}).get("steps") or [])
    else:  # TaskRun
        spec = (doc.get("spec") or {}).get("taskSpec") or {}
        steps = spec.get("steps", []) or []

    if not steps:
        raise ConversionError("No steps found in Tekton spec")

    lines: List[str] = [_header(f"Tekton {kind}/{name}")]
    for i, step in enumerate(steps, 1):
        sname = step.get("name", f"step{i}")
        lines.append(f'echo "--- Step: {sname} ---"')
        script = step.get("script")
        if script:
            lines.append(textwrap.dedent(script).lstrip())
            lines.append("")
            continue
        lines.append(_join_cmd_args(step.get("command"), step.get("args")))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def convert_tekton_to_script(tekton_yaml: str) -> str:
    """
    Convert Tekton Task or TaskRun YAML → bash script.
    Raises ConversionError if YAML is invalid or unsupported.
    """
    doc = yaml.safe_load(tekton_yaml) or {}
    if not isinstance(doc, dict):
        raise ConversionError("YAML must be a single document mapping")

    api = str(doc.get("apiVersion", ""))
    if not api.startswith("tekton.dev/"):
        raise ConversionError("Not a Tekton YAML (apiVersion should start with 'tekton.dev/')")

    return _convert_tekton(doc)

