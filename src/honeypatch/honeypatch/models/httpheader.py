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

from typing import List, Literal, Optional

from pydantic import BaseModel

from .base import Honeywire


class HeaderOp(BaseModel):
    """Describes an operation on a HTTP header."""

    op: Literal["add", "remove", "replace"]
    key: str
    value: Optional[str] = None


class HttpHeaderHoney(Honeywire):
    """Describes a HTTP header manipulation honeywire."""

    kind: Literal["httpheader"]
    operations: List[HeaderOp]
