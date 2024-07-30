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

from ..models.jsonresponse import JsonResponseHoney
from .base import BaseFilter, ValidationResult


class JsonResponseFilter(BaseFilter):
    """Injects fields into a JSON payload."""

    honeywire: JsonResponseHoney

    def __init__(self, honeywire: JsonResponseHoney):
        super().__init__(honeywire)

    def validate(self, data: str) -> ValidationResult:
        # TODO: TR-150 Extend honeypatch with additional honeywire templates
        log.error(f"{type(self).__name__}.validate not implemented")
        return ValidationResult(False)

    def filter(self, data: str) -> str:
        # TODO: TR-150 Extend honeypatch with additional honeywire templates
        log.error(f"{type(self).__name__}.filter not implemented")
        return data
