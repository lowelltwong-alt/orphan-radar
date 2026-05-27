from __future__ import annotations

from pathlib import Path
import json
import typer

from orphan_radar.core.pipeline import run_eval, run_scan, run_status
from orphan_radar.core.settings import RadarSettings

app = typer.Typer(help='Local-first orphan-note radar for reviewable knowledge-graph maintenance.')


@app.command()
def scan(
    src: Path = typer.Option(..., '--src', help='Source folder containing .md/.txt notes.'),
    out: Path = typer.Option(Path('./radar_output'), '--out', help='Output directory.'),
    config: Path | None = typer.Option(None, '--config', help='Optional JSON settings file.'),
    allow_output_inside_source: bool = typer.Option(False, help='Allow output inside source directory. Off by default.'),
):
    settings = RadarSettings.from_json_file(config)
    summary = run_scan(src, out, settings, allow_output_inside_source=allow_output_inside_source)
    typer.echo(json.dumps(summary.__dict__, indent=2))


@app.command()
def status(
    src: Path = typer.Option(..., '--src', help='Source folder containing .md/.txt notes.'),
    config: Path | None = typer.Option(None, '--config', help='Optional JSON settings file.'),
):
    settings = RadarSettings.from_json_file(config)
    typer.echo(json.dumps(run_status(src, settings), indent=2))


@app.command()
def eval(
    src: Path = typer.Option(..., '--src', help='Source folder containing .md/.txt notes.'),
    out: Path = typer.Option(Path('./radar_eval'), '--out', help='Output directory.'),
    config: Path | None = typer.Option(None, '--config', help='Optional JSON settings file.'),
):
    settings = RadarSettings.from_json_file(config)
    typer.echo(json.dumps(run_eval(src, out, settings), indent=2))


@app.command()
def lineage():
    typer.echo('Hubs route attention. Specific links reduce uncertainty. Review keeps the graph honest.')
    typer.echo('Lineage: PageRank-style graph authority + Shannon-style uncertainty reduction + human curation.')


if __name__ == '__main__':
    app()
