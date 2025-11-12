from __future__ import annotations

from tektonx.ir import IRValidationError
from tektonx.parsers import TektonParseError, parse_tekton_yaml
from tektonx.renderers import get_renderer


class ConversionError(Exception):
    """Raised when conversion between Tekton and a renderer fails."""


def convert(tekton_yaml: str, target: str = "bash") -> str:
    """
    Convert Tekton YAML into the requested renderer output.

    Parameters
    ----------
    tekton_yaml: str
        Raw Tekton YAML (Task, TaskRun, Pipeline, or PipelineRun).
    target: str
        Renderer key. See tektonx.renderers.RENDERERS for options.
    """
    try:
        workflow = parse_tekton_yaml(tekton_yaml)
        workflow.validate()
    except (TektonParseError, IRValidationError) as exc:
        raise ConversionError(str(exc)) from exc

    try:
        renderer = get_renderer(target)
    except KeyError as exc:
        raise ConversionError(str(exc)) from exc

    try:
        return renderer(workflow)
    except Exception as exc:  # pragma: no cover - renderer specific
        raise ConversionError(f"Renderer '{target}' failed: {exc}") from exc


def convert_tekton_to_script(tekton_yaml: str) -> str:
    """Backward-compatible helper to keep the original CLI behavior."""
    return convert(tekton_yaml, target="bash")
