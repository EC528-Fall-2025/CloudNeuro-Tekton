"""Parsers translate workflow descriptions into the TektonX IR."""

from typing import Callable, Dict, Tuple

from tektonx.ir import Workflow

from .argo_parser import ArgoParseError, parse_argo_yaml
from .nextflow_parser import NextflowParseError, parse_nextflow_yaml
from .tekton_parser import TektonParseError, parse_tekton_yaml
from .wdl_parser import WDLParseError, parse_wdl

Parser = Callable[[str], Workflow]
ParserEntry = Tuple[Parser, tuple[type[Exception], ...]]

PARSERS: Dict[str, ParserEntry] = {
    "tekton": (parse_tekton_yaml, (TektonParseError,)),
    "argo": (parse_argo_yaml, (ArgoParseError,)),
    "nextflow": (parse_nextflow_yaml, (NextflowParseError,)),
    "wdl": (parse_wdl, (WDLParseError,)),
}


def get_parser(name: str) -> ParserEntry:
    key = name.lower()
    if key not in PARSERS:
        available = ", ".join(sorted(PARSERS))
        raise KeyError(f"Unknown source '{name}'. Available: {available}")
    return PARSERS[key]


__all__ = [
    "ArgoParseError",
    "NextflowParseError",
    "WDLParseError",
    "TektonParseError",
    "get_parser",
    "parse_argo_yaml",
    "parse_nextflow_yaml",
    "parse_tekton_yaml",
    "parse_wdl",
    "PARSERS",
]
