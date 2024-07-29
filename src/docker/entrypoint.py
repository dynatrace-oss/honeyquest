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

import os
import sys

from circus import get_arbiter

api = dict(
    name="api",
    cmd="honeyquest",
    args=sys.argv[1:],
    virtualenv="/opt/honeyquest/honeyback/.venv",
    working_dir="/opt/honeyquest/honeyback",
    copy_env=True,
    copy_path=True,
    numprocesses=1,
    singleton=True,
)

nginx = dict(
    name="nginx",
    cmd="/usr/sbin/nginx",
    args=["-g", "daemon off;"],
    copy_env=False,
    copy_path=False,
    numprocesses=1,
    singleton=True,
)

# set environment variables directly because setting it via
# the env argument in get_arbiter seems to not be implemented
os.environ["GIT_COMMIT"] = open("GIT_COMMIT", encoding="utf8").read().strip()
os.environ["GIT_BRANCH"] = open("GIT_BRANCH", encoding="utf8").read().strip()
os.environ["GIT_MESSAGE"] = open("GIT_MESSAGE", encoding="utf8").read().strip()

arbiter = get_arbiter([api, nginx])

try:
    arbiter.start()
finally:
    arbiter.stop()
