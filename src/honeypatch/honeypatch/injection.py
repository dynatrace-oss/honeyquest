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

from loguru import logger as log

from .filters.factory import get_filter
from .models.base import Honeywire


def inject_honeywire(data: str, honeywire: Honeywire) -> str:
    """
    Given text-based input `data`, injects the selected `honeywire`.

    :param data: Arbitrary, text-based input
    :param honeywire: Honeywire to inject
    :return: The input data with the injected honeywire
    """
    nlines = data.count("\n")
    log.info(
        f"about to inject {honeywire.name} (of kind {honeywire.kind}) "
        f"into input ({nlines} lines) ..."
    )

    # retrieve a filter and validate the input data with it
    honeyfilter = get_filter(honeywire)
    validation = honeyfilter.validate(data)
    if not validation.result:
        log.error(
            f"{type(honeyfilter).__name__} can not filter this input text: "
            f"{validation.message} (pass through)"
        )
        return data

    # apply the filter
    result = honeyfilter.filter(data)
    nlines_changed = result.count("\n") - nlines

    log.success(
        f"injected {honeywire.name} (of kind {honeywire.kind}) "
        f"into input ({nlines_changed:+d} lines)"
    )
    return result
