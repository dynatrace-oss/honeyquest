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

from typing import cast

from ..models.httpheader import HttpHeaderHoney
from ..models.jsonresponse import JsonResponseHoney
from .base import BaseFilter, Honeywire
from .httpheader import HttpHeaderFilter
from .jsonreponse import JsonResponseFilter


def get_filter(honeywire: Honeywire) -> BaseFilter:
    """
    Given a honeywire template, instantiate the correct filter for it.

    :param honeywire: Honeywire template object
    """
    # inline imports are ugly, but we need to avoid cyclic imports
    # without resorting to absolute imports - so, this is the way, sorry!
    # feel free to change this later if you got a better idea ;)
    # pylint: disable=import-outside-toplevel

    match honeywire:
        case HttpHeaderHoney():
            return HttpHeaderFilter(cast(HttpHeaderHoney, honeywire))
        case JsonResponseHoney():
            return JsonResponseFilter(cast(JsonResponseHoney, honeywire))
        case _:
            raise ValueError(f"no filter implemented for honeywire template {honeywire.kind}")
