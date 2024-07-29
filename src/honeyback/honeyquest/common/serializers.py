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

from typing import Any, Sequence

import yaml

# Code Snippet: Control PyYAML scalar form
#
# (c) 2011 Gary van der Merwe https://stackoverflow.com/a/7445560/927377
# (c) 2011 jfs https://stackoverflow.com/a/8641732/927377
# Dynatrace has made changes to this code.
# This code snippet is supplied without warranty.
# This code snippet is licensed under CC BY-SA 3.0.


def _yaml_str_presenter(dumper, data):
    """
    Configures yaml for dumping multiline strings.
    Note that this only works when the lines have no trailing whitespace.


    """
    if data.count("\n") > 1:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


def yaml_dump(payload: Any, sort_keys=False):
    """Serializes an object to yaml, with correct multiline strings and indentation."""
    yaml.representer.SafeRepresenter.add_representer(str, _yaml_str_presenter)
    return yaml.safe_dump(payload, indent=2, sort_keys=sort_keys)


def yaml_dump_all(iterable: Sequence[Any], sort_keys=False):
    """Same as `yaml_dump`, but creates a document for each object in the iterable."""
    yaml.representer.SafeRepresenter.add_representer(str, _yaml_str_presenter)
    return yaml.safe_dump_all(iterable, indent=2, sort_keys=sort_keys)
