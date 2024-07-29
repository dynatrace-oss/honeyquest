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
from typing import Tuple

import yaml


def read_markdown(path: Path | str) -> Tuple[dict, str]:
    """
    Read a Markdown file with YAML front matter at the beginning of the file.

    :param path: The path to read
    :return: A tuple, containing the parsed YAML front matter and the remaining text
    """
    front_matter_lines = []
    with open(path, encoding="utf8") as stream:
        assert stream.readline() == "---\n", "expected YAMl front matter (---) at the start"
        while (line := stream.readline()) != "---\n":
            front_matter_lines.append(line)

        front_matter_text = "".join(front_matter_lines)
        front_matter = yaml.safe_load(front_matter_text)

        document_text = stream.read()

    return (front_matter, document_text)
