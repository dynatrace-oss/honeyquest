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

from datetime import datetime, timedelta
from typing import Dict, List, Literal, Optional, Set, Tuple

from pydantic import BaseModel, Field, StrictBool, StrictInt

from ..las import ParsedLAS, parse_las

QueryLabel = Literal["neutral", "risky", "deceptive"]
QueryType = Literal["tutorial", "httpheaders", "htaccess", "filesystem", "networkrequests"]

# using 'StrictBool | StrictInt | str' is intentional, because
# pydantic will try to parse these values in order from left to right
QueryKVTypeValue = Optional[StrictBool | StrictInt | str]
QueryKVType = Dict[str, QueryKVTypeValue]

ANNOTATION_RISKY_LINES = "risk/risky-lines"
ANNOTATION_DECEPTIVE_LINES = "honeypatch/deceptive-lines"


class BaseQuery(BaseModel):
    """Most minimal, backwards-compatible query."""

    id: str


class Query(BaseQuery):
    """
    Represents any query that me presented to the user.
    See QUERY_DATABASE.md for a description of its properties.
    """

    # ######################################################
    # # NOTE: if you modify this, bump the version in      #
    # # `QueryResponseForStorage` and `FeedbackForStorage` #
    # ######################################################

    label: QueryLabel
    type: QueryType
    references: List[QueryKVType] = []
    annotations: List[QueryKVType] = []
    data: str

    def get_reference(
        self, key: str, complete: bool = False
    ) -> QueryKVTypeValue | List[QueryKVTypeValue] | None:
        result: List[QueryKVTypeValue] = []
        for reference in self.references:
            if val := reference.get(key):
                if not complete:
                    return val
                result.append(val)
        return result if len(result) > 0 else None

    def get_annotation(
        self, key: str, complete: bool = False
    ) -> QueryKVTypeValue | List[QueryKVTypeValue] | None:
        result: List[QueryKVTypeValue] = []
        for annotation in self.annotations:
            if val := annotation.get(key):
                if not complete:
                    return val
                result.append(val)
        return result if len(result) > 0 else None

    def get_risky_lines(self) -> ParsedLAS:
        if annotation := self.get_annotation(ANNOTATION_RISKY_LINES):
            return parse_las(str(annotation))
        return []

    def get_deceptive_lines(self) -> ParsedLAS:
        if annotation := self.get_annotation(ANNOTATION_DECEPTIVE_LINES):
            return parse_las(str(annotation))
        return []


class QueryWrapper(BaseModel):
    """Represents a query along with some metadata about the state of the user's session."""

    query: Query
    answered_queries: int
    total_queries: int


class QueryBucket(BaseModel):
    """Represents a collection of queries that are presented to the user at once."""

    name: str
    strategy: Literal["sorted", "random"]
    description: str
    query_size: int


class QueryBucketsWrapper(BaseModel):
    """The API response for a query bucket request."""

    buckets: Optional[List[QueryBucket]] = None


# if you change this, create a new type and add a union in `Answer` or a migration
LineAnswerV2 = Tuple[int, Literal["hack", "trap"]]


class Answer(BaseModel):
    """The marks that a user placed on the lines of a query."""

    # ###########################################################################
    # # NOTE: if you modify this, bump the version in `QueryResponseForStorage` #
    # ###########################################################################

    timestamp: datetime
    lines: List[LineAnswerV2] = []
    response_time: timedelta = Field(default_factory=timedelta)

    def get_hacks(self) -> Set[int]:
        return set(line for line, answer in self.lines if answer == "hack")

    def get_traps(self) -> Set[int]:
        return set(line for line, answer in self.lines if answer == "trap")


class QueryResponseForApi(BaseModel):
    """
    Represents a user response to some query.
    This is the DTO as processed by the backend REST API.
    Must be kept in sync with QueryCardGroup.jsx
    """

    query_id: str
    answer: Answer


class BaseQueryResponseForStorage(BaseModel):
    """Most minimal, backwards-compatible stored query response."""

    uid: str
    qid: int
    query: BaseQuery


class QueryResponseForStorage(BaseQueryResponseForStorage):
    """
    Represents a user response to some query.
    This is the DTO as as stored on disk in a self-contained manner.
    """

    query: Query
    answer: Answer
    version: Optional[str] = "response/v3"
