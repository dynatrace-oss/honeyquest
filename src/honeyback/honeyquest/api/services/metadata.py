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
from typing import Optional

import mistune
from mistune.renderers.html import HTMLRenderer

from ...common.markdown import read_markdown
from ...common.models.metadata import Metadata
from ..config import get_settings


class MetadataService:
    """Reads the metadata associated with some queries."""

    def __init__(self, honeyquest_data: Path | str):
        self._data_path = (Path(honeyquest_data) / "metadata").resolve()
        self._markdown_to_html_renderer = mistune.create_markdown(
            renderer=HTMLRenderer(escape=False), hard_wrap=False
        )

    def get_markdown(self, metadata_id: str) -> Optional[Metadata]:
        metadata_path = self._data_path.joinpath(f"{metadata_id}.md").resolve()
        if not metadata_path.is_relative_to(self._data_path) or not metadata_path.exists():
            return None

        meta, text = read_markdown(metadata_path)
        return Metadata(**meta, text=text)

    def get_html(self, metadata_id: str) -> Optional[Metadata]:
        meta_markdown = self.get_markdown(metadata_id)
        if meta_markdown is None:
            return None

        meta_html = Metadata(**meta_markdown.model_dump())
        meta_html.text = self._markdown_to_html_renderer(meta_markdown.text)
        return meta_html


@cache
def get_metadata_svc() -> MetadataService:
    """Provides a singleton (cached instance) of `MetadataService`."""
    settings = get_settings()
    assert settings.honeyquest_data is not None
    return MetadataService(settings.honeyquest_data)
