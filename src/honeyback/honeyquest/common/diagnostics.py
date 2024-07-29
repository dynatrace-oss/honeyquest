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

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from ..api.config import Settings
from .archive import create_zip_archive


def enrich_settings(settings: Settings) -> dict:
    # enrich the settings object with some environment info
    return dict(settings=settings.model_dump(), env=get_git_info())


def create_results_archive(settings: Settings) -> str:
    data_dir = settings.honeyquest_data
    results_dir = settings.honeyquest_results
    assert data_dir is not None
    assert results_dir is not None

    # store the settings as json into a temporary file
    settings_tmp = NamedTemporaryFile(mode="w+", encoding="utf8", delete=False)
    settings_tmp.write(json.dumps(enrich_settings(settings), indent=2))
    settings_tmp.close()
    settings_file = Path(settings_tmp.name)

    # zip and rename the directories and files
    names = ["data", "results", "settings.json"]
    archive = create_zip_archive([data_dir, results_dir, settings_file], names)

    # clean-up settings file
    settings_file.unlink(missing_ok=True)

    return archive


def get_git_info():
    return dict(
        GIT_COMMIT=os.getenv("GIT_COMMIT"),
        GIT_MESSAGE=os.getenv("GIT_MESSAGE"),
        GIT_BRANCH=os.getenv("GIT_BRANCH"),
    )
