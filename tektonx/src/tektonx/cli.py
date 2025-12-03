from __future__ import annotations

from pathlib import Path
import sys
import typer
from rich import print

from tektonx.converter import ConversionError, convert
from tektonx.parsers import PARSERS
from tektonx.renderers import RENDERERS

app = typer.Typer(help="Convert Tekton/Argo/Nextflow resources to multiple workflow formats.")


@app.command(name="convert")
def convert_command(
    input: Path = typer.Argument(..., exists=True, readable=True, help="Tekton YAML file"),
    out: Path | None = typer.Option(None, "--out", "-o", help="Write output to this path"),
    target: str = typer.Option(
        "bash",
        "--target",
        "-t",
        help=f"Renderer to use ({', '.join(sorted(RENDERERS))})",
    ),
    source: str = typer.Option(
        "tekton",
        "--source",
        "-s",
        help=f"Input format ({', '.join(sorted(PARSERS))})",
    ),
):
    """Read workflow YAML and emit the selected backend."""
    try:
        data = input.read_text()
        artifact = convert(data, target=target.lower(), source=source.lower())
    except ConversionError as e:
        print(f"[red]Conversion failed:[/red] {e}")
        raise typer.Exit(code=2)
    except Exception as e:  # pragma: no cover
        print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(code=1)

    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(artifact)
        print(f"[green]Wrote {target} artifact to {out}[/green]")
    else:
        sys.stdout.write(artifact)


if __name__ == "__main__":
    app()
