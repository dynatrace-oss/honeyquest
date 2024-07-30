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

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from ..models.base import Honeywire


@dataclass
class ValidationResult:
    """The result of validating if a filter is applicable to some data."""

    result: bool
    message: Optional[str] = None

    @staticmethod
    def new(result: bool, message: Optional[str]):
        """
        Helps to construct a new `ValidationResult` object.
        This is used to keep the message in case of a negative result.
        """
        return ValidationResult(True) if result else ValidationResult(False, message)


class BaseFilter(ABC):
    """Abstract base filter for all honeywire filter implementations."""

    def __init__(self, honeywire: Honeywire):
        super().__init__()
        self.honeywire = honeywire

    @abstractmethod
    def validate(self, data: str) -> ValidationResult:
        """
        Checks if the input data can be transformed by this filter.

        :param data: Some text-based input that might be processed by this filter
        :return: A tuple containing the validation result and an optional message
        """

    @abstractmethod
    def filter(self, data: str) -> str:
        """
        Injects the honeywire into the input data.

        Takes arbitrary, text-based input, applies the honeywire-specific
        filter rules, as specified in the template `self.honeywire` and
        returns the result, i.e., injects the honeywire into `data`.

        :param data: Some text-based input that can be processed by this filter
        :return: The data plus the injected honeywire
        """
