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

import re
from collections import OrderedDict
from typing import Dict, NamedTuple

from loguru import logger as log

from ..models.httpheader import HttpHeaderHoney
from .base import BaseFilter, ValidationResult


class HttpHeaderFilter(BaseFilter):
    """Injects HTTP headers into a HTTP response message."""

    honeywire: HttpHeaderHoney

    def __init__(self, honeywire: HttpHeaderHoney):
        super().__init__(honeywire)
        # regex that checks for a HTTP response message (no request messages),
        # payloads are not permitted, but extra whitespace at the end is okay
        # see https://datatracker.ietf.org/doc/html/rfc7230#section-3 for true protocol format
        self.http_regex = re.compile(r"^HTTP.*\n(?:[A-Za-z0-9\-]+: .+\n)*\s*$")

    def validate(self, data: str) -> ValidationResult:
        match = self.http_regex.match(data)
        return ValidationResult.new(
            bool(match), f"data does not match pattern '{self.http_regex.pattern}'"
        )

    def filter(self, data: str) -> str:
        message = HttpHeaderFilter._parse_http_response_message(data)
        log.debug(f"parsed http response: {message}")

        # header keys must match case-insensitive, but,we don't want to mangle
        # the data unnecessarily, thus, we keep a map from canonical
        # (lower-case) names back to their original ones
        canonical_keys = {key.lower(): key for key in message.headers.keys()}

        no_operations = 0
        for item in self.honeywire.operations:
            canonical_key = item.key.lower()
            match item.op:

                case "add":
                    if canonical_key in canonical_keys:
                        log.warning(
                            f"can not add already existing header {canonical_key} (ignoring)"
                        )
                        continue

                    # we add new headers as-is and don't make them lower-case
                    message.headers[item.key] = item.value or ""
                    no_operations += 1

                case "remove":
                    if canonical_key not in canonical_keys:
                        log.warning(
                            f"can not remove non-existent header {canonical_key} (ignoring)"
                        )
                        continue

                    del message.headers[canonical_keys[canonical_key]]
                    no_operations += 1

                case "replace":
                    if canonical_key not in canonical_keys:
                        log.warning(
                            f"can not replace non-existent header {canonical_key} (ignoring)"
                        )
                        continue

                    message.headers[canonical_keys[canonical_key]] = item.value or ""
                    no_operations += 1

        if no_operations == 0:
            log.warning(
                "the filter did not modify any headers "
                "- are you using the correct template and data?"
            )

        header_block = "\n".join([f"{key}: {val}" for key, val in message.headers.items()])
        return f"{message.status_line}\n{header_block}\n"

    class _HttpResponse(NamedTuple):
        status_line: str
        headers: Dict[str, str]

    @staticmethod
    def _parse_http_response_message(data: str) -> _HttpResponse:
        lines = data.rstrip().splitlines()
        status_line, header_block = lines[0], lines[1:]

        # store headers in a dict, but don't mangle with the order
        headers = OrderedDict()
        for header_line in header_block:
            key, value = header_line.split(": ", 1)
            if key in headers:
                log.warning(
                    f"header key {key} (in '{header_line}') "
                    f"was defined more than once (overwriting)"
                )
            headers[key] = value

        return HttpHeaderFilter._HttpResponse(status_line, headers)
