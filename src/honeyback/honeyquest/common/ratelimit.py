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

from time import time


class LeakyBucket:
    """
    Implements the leaky bucket algorithm for simple rate limiting.

    A bucket has a certain capacity ("burst limit").
    A user can consume tokens (e.g., for API requests) from the bucket.
    The bucket will refill at a certain rate (tokens per second = "rate limit").

    Upon initialization, the bucket is full.
    If the bucket is empty, the request will be rejected.
    """

    def __init__(self, capacity: int, rate: float):
        self._capacity = capacity
        self._rate = rate
        self._tokens = capacity
        self._last_update = time()

    def _refill_tokens(self):
        now = time()
        diff = now - self._last_update

        # re-fill `rate` tokens per second, without exceeding capacity
        self._tokens = min(self._capacity, self._tokens + diff * self._rate)
        self._last_update = now

    def consume(self) -> bool:
        """Attempts to consume a token from the bucket."""
        self._refill_tokens()
        if self._tokens > 0:
            self._tokens -= 1
            return True
        return False
