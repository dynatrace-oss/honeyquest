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

from typing import List, Set, Tuple

ParsedLAS = List[Tuple[int, int]]


def parse_las(syntax: str) -> ParsedLAS:
    """
    Extracts the ranges specified in the syntax.
    See QUERY_DATABASE.md for details.

    :param syntax: The line annotation syntax (LAS)
    :return: A list of (start, end) tuples (inclusive)
    """
    ranges = []
    for las in syntax.split(","):
        without_prefix = las[1:]
        without_colons = without_prefix.split(":")[0]
        start, end = without_colons, None
        if "-" in without_colons:
            start, end = without_colons.split("-", 1)

        ranges.append((int(start), int(end or start)))

    return ranges


def expand_las(ranges: ParsedLAS) -> Set[int]:
    """
    Expands the ranges to an exhaustive set of line numbers.
    See QUERY_DATABASE.md for details.

    :param ranges: A list of LAS ranges
    :return: A set of line numbers
    """
    lines: Set[int] = set()
    for start, end in ranges:
        lines.update(range(start, end + 1))

    return lines


def in_las(line: int, ranges: ParsedLAS) -> bool:
    """
    Checks if the line is in the range specified in the LAS.
    Use `parse_las` to parse the ranges from a LAS string.
    This is faster than expanding the range and checking.

    :param line: The line number to check
    :param ranges: A list of LAS ranges
    :return: Whether the line is in the range or not
    """
    for start, end in ranges:
        if start <= line <= end:
            return True

    # not in range
    return False
