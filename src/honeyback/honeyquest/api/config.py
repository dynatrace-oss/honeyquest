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
from typing import Optional

from pydantic_settings import BaseSettings

# reuse the uvicorn logger
log = logging.getLogger("uvicorn.error")


class Settings(BaseSettings):
    """
    Specifies application settings, which will be read from the environment.

    Read more on https://pydantic-docs.helpmanual.io/usage/settings/
    """

    honeyquest_data: Optional[str] = None
    honeyquest_index: Optional[str] = None
    honeyquest_data_url: Optional[str] = None
    honeyquest_results: Optional[str] = None
    compress_results: bool = False
    cookie_secret: Optional[str] = None
    cookie_expire_days: int = 365
    session_timeout_mins: int = 60
    admin_token: Optional[str] = None
    sample_duplicates: bool = False
    api_burst_limit: int = 10
    api_rate_limit: float = 1


@cache
def get_settings() -> Settings:
    """Provides a singleton (cached instance) of `Settings`."""
    settings = Settings()
    log.info(settings)
    return settings
