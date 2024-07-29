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

import json
from datetime import datetime
from http.client import responses
from pathlib import Path

import typer

app = typer.Typer(add_completion=False)


def format_harfile(path: Path | str):
    """
    Reads a HAR file and returns a list with the entries formatted as a string.
    The entries are sorted by time and look like this:

    ```
    0.000 GET https://www.google.com/ 200 OK
    0.168 GET https://www.google.com/logo.gif 200 OK
    0.179 GET https://www.google.com/images/sprite.webp 200 OK
    0.184 GET https://fonts.gstatic.com/24px.svg 200 OK
    ```

    :param path: The path to the HAR file.
    :return: A list of strings, each string representing one entry.
    """
    with open(path, "r", encoding="utf8") as f:
        jzon = json.load(f)
    assert jzon is not None

    pages = jzon["log"]["pages"]
    first_page = pages[0]["id"] if pages else None
    assert len(pages) <= 1, "multi-page HAR files are not supported"

    # pre-process some fields in the entry
    entries = []
    for e in jzon["log"]["entries"]:
        if first_page is not None and ("pageref" not in e or e["pageref"] != first_page):
            continue  # skip if there are multiple pages, and this one is not the first page

        time = datetime.fromisoformat(e["startedDateTime"].removesuffix("Z"))
        url = e["request"]["url"]
        status = int(e["response"]["status"])
        method = e["request"]["method"]

        # sometimes invalid dates are in the HAR file, ignore ...
        if time.year < 2000:
            continue

        # read body size or content size
        size = e["response"]["bodySize"]
        if size == -1 and "content" in e["response"] and "size" in e["response"]["content"]:
            size = e["response"]["content"]["size"]

        entries.append(
            dict(
                time=time,
                url=url,
                status=status,
                method=method,
                size=size,
            )
        )

    entries = sorted(entries, key=lambda e: e["time"].timestamp(), reverse=False)
    earlierst_time = entries[0]["time"] if entries else datetime.now()

    # format the entries line-by-line
    lines = []
    for e in entries:
        delta = (e["time"] - earlierst_time).total_seconds()
        method, url = e["method"], e["url"]
        statuscode = f' {e["status"]}' if e["status"] > 0 else ""
        statustext = f' {responses[e["status"]]}' if e["status"] in responses else ""
        size = f' ({_format_bytes(e["size"])})' if e["size"] > 0 else ""

        line = f"{delta:.3f} {method} {url}{statuscode}{statustext}{size}"
        lines.append(line)

    return lines


def _format_bytes(size):
    if size < 100:
        return f"{size} bytes"
    if size < 1000 * 1000:
        return f"{size / 1000:.1f} kB"
    if size < 1000 * 1000 * 1000:
        return f"{size / 1000 / 1000:.1f} MB"
    raise ValueError(f"no formatter set for size: {size} bytes")


@app.command(help="Reads a HAR file and returns a list with the entries formatted as a string")
def cli(
    path: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=True,
        file_okay=True,
        resolve_path=True,
        help="HAR file path",
    )
):
    if path.is_dir():
        for p in path.glob("*.har"):
            print(p.name, end="\n\n")
            lines = format_harfile(p)
            lines = "\n".join(lines)
            print(lines)
            print()
    elif path.is_file():
        lines = format_harfile(path)
        lines = "\n".join(lines)
        print(lines)


if __name__ == "__main__":
    app()
