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

from pathlib import Path
from typing import Optional

import typer

from .api import run_server
from .api.config import Settings

app = typer.Typer(add_completion=False)


@app.command(help="Start the honeyquest backend")
def ui_cli(
    data_directory: Path = typer.Option(
        None,
        "--data",
        "-d",
        exists=True,
        dir_okay=True,
        file_okay=False,
        resolve_path=True,
        help="Directory with the query database",
    ),
    data_url: str = typer.Option(
        None, "--data-url", "-u", help="URL with the query database as a .tar.gz file"
    ),
    results: Path = typer.Option(
        None,
        "--results",
        "-r",
        exists=False,
        dir_okay=True,
        file_okay=False,
        resolve_path=True,
        help="Directory for user profiles, responses, and feedback",
    ),
    index_name: str = typer.Option(None, "--index", "-i", help="Name of the query index"),
    compress: bool = typer.Option(False, help="Compress results with gzip"),
    duplicates: bool = typer.Option(False, help="Sample duplicate queries"),
    cookie_secret: Optional[str] = typer.Option(None, help="Secret to sign session cookies"),
    admin_token: Optional[str] = typer.Option(None, help="Token for the admin panel"),
    debug: bool = typer.Option(False, help="Enable development mode"),
):
    kwargs = {
        "honeyquest_data": data_directory.resolve().as_posix() if data_directory else None,
        "honeyquest_index": index_name,
        "honeyquest_data_url": data_url,
        "honeyquest_results": results.resolve().as_posix() if results else None,
        "compress_results": compress,
        "sample_duplicates": duplicates,
        "cookie_secret": cookie_secret,
        "admin_token": admin_token,
    }

    # TODO: RT-2490 make handling of config and secrets more consistent
    # do not pass non-None values, because if we would pass None values here
    # they can not be overwritten by environment variables or env files later
    settings = Settings.model_validate(
        {k: v for (k, v) in kwargs.items() if v is not None}, strict=True
    )

    # TODO: RT-2490 let pydantic handle this rule
    # the fully-resolved settings object may only have a data path or url, not none, not both
    if not bool(settings.honeyquest_data) ^ bool(settings.honeyquest_data_url):
        raise typer.BadParameter(
            "please specify either --data or --data-url via the CLI or the environment"
        )

    run_server(settings, debug=debug)


if __name__ == "__main__":
    app()
