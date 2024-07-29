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

import logging
from functools import cache
from pathlib import Path

import yaml

# reuse the uvicorn logger
log = logging.getLogger("uvicorn.error")

DEFAULT_CONFIG_PATH = STATIC_PATH = Path(__file__).parent / "config.yaml"
LOCAL_CONFIG_PATH = STATIC_PATH = Path(__file__).parent / "config.local.yaml"


def read_config(job: str, path: Path | str):
    """
    Loads the configuration, sub-selects nodes for the current job, but still adds global resources.

    :param job: the name of the job ops to select from `config.yaml`
    :param path: the path of the configuration file
    :return: a Dagster-compatible configuration for the ops of the selected job
    """
    with open(path, "r", encoding="utf8") as f:
        payload = yaml.safe_load(f)

    # select only ops for this one job
    job_ops = payload["ops"].get(job, {})
    del payload["ops"]
    payload["ops"] = job_ops

    return payload


@cache
def get_cached_config(job: str):
    """
    Like `read_config` but will cache the result and only read on first invocation.
    Also, this function will auto-select the local configuration if it exists.

    :param job: the name of the job ops to select from `config.yaml`
    :return: a Dagster-compatible configuration for the ops of the selected job
    """
    return read_config(job, test_config_path())


def test_config_path():
    """
    Uses the local configuration if it exists, otherwise uses the default configuration.

    :return: the path to the configuration file
    """
    local_config_exists = LOCAL_CONFIG_PATH.exists()
    if not local_config_exists:
        log.warning(
            f"no local dagster configuration found at {LOCAL_CONFIG_PATH}. "
            f"using default configuration at {DEFAULT_CONFIG_PATH} instead."
        )

    return LOCAL_CONFIG_PATH if LOCAL_CONFIG_PATH.exists() else DEFAULT_CONFIG_PATH
