"""Renderer registry for TektonX."""

from __future__ import annotations

from typing import Callable, Dict

from tektonx.ir import Workflow

from . import bash_renderer, chris_renderer, make_renderer, snakemake_renderer, slurm_renderer, sungrid_renderer

Renderer = Callable[[Workflow], str]

RENDERERS: Dict[str, Renderer] = {
    "bash": bash_renderer.render,
    "chris": chris_renderer.render,
    "make": make_renderer.render,
    "snakemake": snakemake_renderer.render,
    "slurm": slurm_renderer.render,
    "sungrid": sungrid_renderer.render,
}


def get_renderer(name: str) -> Renderer:
    key = name.lower()
    if key not in RENDERERS:
        available = ", ".join(sorted(RENDERERS))
        raise KeyError(f"Unknown renderer '{name}'. Available: {available}")
    return RENDERERS[key]
