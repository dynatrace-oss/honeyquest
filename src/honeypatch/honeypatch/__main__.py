# Copyright 2024 Dynatrace LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Portions of this code, as identified in remarks, are provided under the
# Creative Commons BY-SA or the MIT license, and are provided without
# any warranty. In each of the remarks, we have provided attribution to the
# original creators and other attribution parties, along with the title of
# the code (if known) a copyright notice and a link to the license, and a
# statement indicating whether or not we have modified the code.

import sys
from pathlib import Path
from textwrap import shorten
from typing import Optional

import typer
from loguru import logger as log

from .injection import inject_honeywire
from .pool import list_honeywires, read_honeywire

app = typer.Typer(add_completion=False)


@app.command("inject")
def inject_cli(
    filename: typer.FileText = typer.Argument(
        "-", encoding="utf8", help="Text data to inject into"
    ),
    honeywire: str = typer.Option(..., "--honeywire", "-w", help="Name of the honeywire to inject"),
    output: typer.FileTextWrite = typer.Option(
        "-", "--output", "-o", encoding="utf8", help="Write result to a file"
    ),
    pool: Optional[Path] = typer.Option(
        None,
        "--pool",
        "-p",
        exists=True,
        dir_okay=True,
        file_okay=False,
        resolve_path=True,
        help="Directory with honeywire templates",
    ),
    quiet: bool = False,
    verbose: bool = False,
):
    """
    Injects a selected honeywire into text-based payload.
    The referenced honeywire must exist in the pool of honeywires.
    """
    _reset_log(quiet=quiet, verbose=verbose)
    log.debug(f"program arguments: {locals()}")

    if filename.isatty():
        raise typer.BadParameter(
            "can not read from terminal device - did you forget to pipe something to STDIN?"
        )

    if pool is None:
        raise typer.BadParameter("pool directory must be provided")

    hwire = read_honeywire(honeywire, pool)
    if not hwire:
        raise typer.BadParameter(
            f"honeywire with name {honeywire} does not exist in pool ({pool.absolute()})"
        )

    data = filename.read()
    result = inject_honeywire(data, hwire)
    output.write(result)


@app.command("list")
def list_cli(
    pool: Optional[Path] = typer.Option(
        None,
        "--pool",
        "-p",
        exists=True,
        dir_okay=True,
        file_okay=False,
        resolve_path=True,
        help="Directory with honeywire templates",
    ),
    verbose: bool = False,
):
    """Lists the available honeywire templates in the pool."""
    _reset_log(verbose=verbose)
    log.debug(f"program arguments: {locals()}")

    if pool is None:
        raise typer.BadParameter("pool directory must be provided")

    honeywires = list_honeywires(pool)

    # retrieve maximum column widths to format a nice table
    col_name = max(len(name) for name in honeywires) + 2
    col_kind = max(len(hwire.kind) for hwire in honeywires.values()) + 2
    typer.echo(f"{'NAME':{col_name}} {'KIND':{col_kind}} {'DESCRIPTION'}")

    # print each honeywire - but sort by kind, then, by name
    for name in sorted(honeywires, key=lambda m: (honeywires[m].kind, honeywires[m].name)):
        hwire = honeywires[name]
        typer.echo(f"{name:{col_name}} {hwire.kind:{col_kind}} {shorten(hwire.description, 120)}")


def _reset_log(quiet: bool = False, verbose: bool = False):
    log.remove()
    if not quiet:
        level = "DEBUG" if verbose else "INFO"
        log.add(sys.stdout, level=level)


if __name__ == "__main__":
    app()
