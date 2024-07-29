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

from typing import Iterable, List


def flatten(listoflists: Iterable) -> list:
    """Flattens a list of lists into a single list."""
    return [item for sublist in listoflists for item in sublist]


def map_rounded_numbers_to_probability_distribution(
    nums: List[float], nplaces: int = 0
) -> List[float]:
    """
    Rounds a list of numbers and ensure that they still sum to 100.
    For example, given a list of percentages, e.g. [52.88, 5.60, 13.67, 28.06],
    that will be rounded to `nplaces = 0`, resulting in [53, 6, 14, 28],
    we correct the rounding error by slightly adjusting numbers to ensure that
    they sum to 100 again. This makes the visualizations in the paper more sound.
    Counts will be corrected from the last to the first number.
    """
    presum = round(sum(nums), nplaces)
    assert presum == 100, f"argument does not sum to 100: sum({nums}) = {sum(nums)}"

    nums_rounded = [round(num, nplaces) for num in nums]

    if round(sum(nums_rounded), nplaces) == 100:
        return nums_rounded

    i = len(nums) - 1
    while round(sum(nums_rounded), nplaces) != 100:
        sign = 1 if sum(nums_rounded) < 100 else -1
        delta = sign * (1 / (10**nplaces))
        nums_rounded[i] += delta
        i -= 1

    assert round(sum(nums_rounded), nplaces) == 100
    return nums_rounded
