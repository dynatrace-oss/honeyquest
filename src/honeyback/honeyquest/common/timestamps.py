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

from datetime import datetime, timezone
from typing import Optional


def epoch_time(dt: Optional[datetime] = None) -> int:
    """
    Gets an UTC epoch timestamp of the supplied time.

    :param dt: The `datetime` to get the timestamp for (default: now)
    :return: An epoch timestamp as an integer
    """
    dt = dt if dt is not None else datetime.utcnow()
    return int(dt.replace(tzinfo=timezone.utc).timestamp())


def epoch_time_to_iso_str(ts: Optional[int] = None, timespec: str = "minutes"):
    """
    Convert an epoch timestamp (in seconds) to a human-readable string.
    The result may also be taken as a filename. E.g., 1653506843 becomes '2022-05-25T1927Z'.

    The `timespec` precision may be 'auto', 'hours', 'minutes',
    'seconds', 'milliseconds' or 'microseconds'.

    :param ts: UNIX epoch timestamp in seconds (default: now)
    :param timespec: The precision of the timestamp (default: minutes)
    :return: File-system safe string representation in format 'YYYY-MM-DDTHHMMZ'
    """
    ts = ts if ts is not None else epoch_time()
    dt = datetime.fromtimestamp(ts).astimezone(timezone.utc)
    iso_str = dt.isoformat(timespec=timespec, sep="T")
    safe_str = iso_str.replace("+00:00", "Z").replace(":", "").replace(".", "")
    return safe_str
