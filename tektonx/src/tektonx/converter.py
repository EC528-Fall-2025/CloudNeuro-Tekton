from __future__ import annotations

from tektonx.ir import IRValidationError
from tektonx.parsers import get_parser
from tektonx.renderers import get_renderer


class ConversionError(Exception):
    """Raised when conversion between a workflow source and a renderer fails."""


def convert(workflow_yaml: str, target: str = "bash", source: str = "tekton") -> str:
    """
    Convert workflow YAML into the requested renderer output.

    Parameters
    ----------
    workflow_yaml: str
        Raw YAML for the selected source format.
    target: str
        Renderer key. See tektonx.renderers.RENDERERS for options.
    source: str
        Input format: tekton (default), argo, nextflow.
    """
    try:
        parser, parse_errors = get_parser(source)
    except KeyError as exc:
        raise ConversionError(str(exc)) from exc

    try:
        workflow = parser(workflow_yaml)
        workflow.validate()
    except IRValidationError as exc:
        raise ConversionError(str(exc)) from exc
    except parse_errors as exc:
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
    return convert(tekton_yaml, target="bash", source="tekton")
