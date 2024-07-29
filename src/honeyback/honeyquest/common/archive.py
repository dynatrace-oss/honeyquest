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
from os.path import isfile
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Optional, Sequence, cast
from zipfile import ZipFile


def create_zip_archive(
    targets: (Path | str) | List[Path | str],
    names: Optional[str | Sequence[Optional[str]]] = None,
) -> str:
    """
    Archives the target directories or files into a single ZIP file.
    The caller is responsible for deleting the (temporary) archive file.
    Also allows you to possibly rename the parent name of the target file or directory.

    :param targets: A single file or directory or a list of files and directories
    :param names: Change the parent directory name or file name in the archive (optional)
    :return: The path to the ZIP file
    """
    targets = targets if isinstance(targets, list) else [targets]
    names = names if names is not None else [None] * len(targets)
    names = names if isinstance(names, Sequence) else [cast(Optional[str], names)]  # for mypy
    assert len(targets) == len(names)

    archive = NamedTemporaryFile(suffix=".zip", delete=False)
    with ZipFile(archive, "w") as zipfer:
        for target, name in zip(targets, names):
            target = Path(target)

            # hack the iterator to make it work for single files as well
            it = iter([(".", [], [str(target)])]) if isfile(target) else os.walk(target)
            for root, _, files in it:
                rootpath = Path(root)
                for filename in files:
                    filepath = rootpath.joinpath(filename)
                    arcname = (
                        filepath.relative_to(target.parent)  # keep parent name
                        if name is None
                        else name / filepath.relative_to(target)  # rename parent
                    )

                    # add filename with its arcname
                    zipfer.write(filepath, arcname)

    archive.close()
    return archive.name
