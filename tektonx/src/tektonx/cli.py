from pathlib import Path
import sys
import typer
from rich import print
from tektonx.converter import convert_tekton_to_script, ConversionError

app = typer.Typer(help="Convert K8s Job/Pod or Tekton Task/TaskRun to a bash script")

@app.command()
def convert(
    input: Path = typer.Argument(..., exists=True, readable=True, help="K8s/Tekton YAML file"),
    out: Path | None = typer.Option(None, "--out", help="Write script to this path"),
):
    """Read YAML and output a bash script."""
    try:
        data = input.read_text()
        script = convert_tekton_to_script(data)
    except ConversionError as e:
        print(f"[red]Conversion failed:[/red] {e}")
        raise typer.Exit(code=2)
    except Exception as e:
        print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(code=1)

    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(script)
        print(f"[green]Wrote script to {out}[/green]")
    else:
        sys.stdout.write(script)

if __name__ == "__main__":
    app()
