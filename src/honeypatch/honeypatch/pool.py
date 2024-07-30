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

from functools import cache
from pathlib import Path
from typing import Annotated, Mapping, Optional

import yaml
from loguru import logger as log
from pydantic import BaseModel, Field

from .models.base import Honeywire
from .models.httpheader import HttpHeaderHoney
from .models.jsonresponse import JsonResponseHoney


class _HoneywireDocument(BaseModel):
    """The model we expect when reading a single YAML document file from the pool."""

    honeywire: Annotated[HttpHeaderHoney | JsonResponseHoney, Field(..., discriminator="kind")]


def read_honeywire(name: str, path: Path) -> Optional[Honeywire]:
    """
    Reads a honeywire by name, from disk, located at `path`.
    The honeywire pool stores a language-agnostic description
    on how a certain honeywire is injected into arbitrary text payload.

    :param name: Name of the honeywire to be loaded (`name` field in template)
    :param path: Some directory holding honeywire configuration YAML files
    :return: The parsed and validated `Honeywire` object or `None` on invalid names
    """
    pool = _read_pool(path)
    return pool.get(name)


def list_honeywires(path: Path) -> Mapping[str, Honeywire]:
    """
    Get a dictionary that contains all available honeywires from the pool located at `path`.

    :param path: Some directory holding honeywire configuration YAML files
    :return: A dictionary, mapping honeywire names to their parsed and validated objects
    """
    return _read_pool(path)


@cache
def _read_pool(path: Path) -> Mapping[str, Honeywire]:
    log.debug(f"reading honeywire pool from {path.absolute()} ...")
    pool = {}

    for file in path.iterdir():
        if not file.is_file() or (file.suffix not in (".yml", ".yaml")):
            continue

        with open(file, encoding="utf8") as stream:
            # load, validate, and store each document in this file
            documents = yaml.load_all(stream, yaml.SafeLoader)
            for doc in documents:
                honeywire = _HoneywireDocument(**doc).honeywire
                if honeywire.name in pool:
                    log.warning(
                        f"honeywire {honeywire.name} (in {file.name}) "
                        f"was defined more than once (skipping)"
                    )
                    continue

                pool[honeywire.name] = honeywire
                log.debug(f"loaded {honeywire.name} from {file.name}")

    log.debug(f"honeywire pool: {pool}")
    return pool
