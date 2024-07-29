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

import shutil
import zipfile
from io import BytesIO
from logging import Logger
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, List, Optional

import requests
import yaml

from ...common.models.query import Query, QueryResponseForStorage
from ...common.models.user import User
from ..types import HoneyquestResults


def load_experiments(
    local_base: str,
    local_paths: Dict[str, str],
    live_url: str,
    live_tokens: Dict[str, str],
) -> Dict[str, HoneyquestResults]:
    """
    Loads both local and live honeyquest results for multiple experiments.

    :param local_base: The base path to the folder containing the local results
    :param local_paths: A mapping from experiment name to the folder name in `local_base`
    :param live_url: The URL of the live instances, with `EXPERIMENT` placeholder to be replaced
    :param live_tokens: A mapping from experiment name to the admin token for that live instance
    :return: A dictionary of result objects, keyed by experiment name
    """
    assert len(local_paths) > 0 or len(live_tokens) > 0, "no experiments specified"
    assert len(local_paths) == 0 or Path(local_base).exists(), "local base path does not exist"
    assert "EXPERIMENT" in live_url, "live URL must contain EXPERIMENT placeholder"

    results = {}

    # load and parse local results
    for name, path in local_paths.items():
        res = parse_results(Path(local_base) / path)
        results[name] = res

    # download, load and parse live results
    for name, token in live_tokens.items():
        archive_path = download_responses(live_url.replace("EXPERIMENT", name), token)
        res = parse_results(archive_path)
        cleanup_responses(archive_path)
        results[name] = res

    return results


def download_responses(host: str, token: str) -> str:
    """
    Downloads query responses from a live honeyquest instance to a temporary directory.
    The caller is responsible for cleaning up the temporary directory again.
    You can use the `cleanup_responses` function for this.

    :param host: The full URL of the live instance
    :param token: The admin token to use for authentication
    :return: Path to a temporary directory containing the data
    """
    host = host.removesuffix("/")

    # authenticate as admin
    session = requests.Session()
    auth = session.post(host + "/api/admin/auth", json={"token": token})
    assert auth.status_code == 204, "invalid admin token"

    # download the archive
    results = session.get(host + "/api/admin/results", stream=True)
    assert results.status_code == 200, "failed to download results"

    # unpack archive
    archive_path = TemporaryDirectory(prefix="honeyquest_showcase_").name
    with zipfile.ZipFile(BytesIO(results.content)) as zipf:
        zipf.extractall(archive_path)

    return archive_path


def cleanup_responses(path: Path | str):
    """
    Cleans up a temporary directory containing honeyquest results.

    :param path: The path to the temporary directory.
    """
    path = Path(path)
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def parse_results(path: Path | str) -> HoneyquestResults:
    """
    Parses a honeyquest results folder.

    :param path: The path to the honeyquest data directory.
    :return: The query responses and user profiles
    """
    path = Path(path).resolve()
    responses_path = path / "results" / "responses"
    profiles_path = path / "results" / "profiles"

    responses = []
    if responses_path.exists():
        for p in responses_path.iterdir():
            if p.suffix == ".jsonl":
                lines = p.read_text(encoding="utf8").splitlines()
                parsed = [QueryResponseForStorage.model_validate_json(line) for line in lines]
                responses.extend(parsed)

    profiles = []
    if profiles_path.exists():
        for p in profiles_path.iterdir():
            if p.suffix == ".json":
                text = p.read_text(encoding="utf8")
                profile = User.model_validate_json(text)
                profiles.append(profile)

    return HoneyquestResults(
        profiles=profiles,
        responses=responses,
    )


def parse_all_queries(path: Path | str, log: Optional[Logger] = None) -> Dict[str, Query]:
    """
    Parses all queries from the queries directory.
    Assumes that there are no duplicate ids.
    Use the index job if you want to find duplicates.

    :param path: The path to the honeyquest data directory.
    :param log: The logger to use for logging.
    :return: A dictionary of queries, indexed by their id.
    """
    path = Path(path).resolve()
    queries = {}

    yaml_globber = (path / "queries").rglob("*.yaml")
    for file in yaml_globber:
        if log:
            relative_file = file.relative_to(path)
            log.info(f"parsing {relative_file} ...")

        with open(file, encoding="utf8") as stream:
            yaml_docs = yaml.safe_load_all(stream)
            parsed_queries = (Query(**d) for d in yaml_docs)
            queries.update({q.id: q for q in parsed_queries})

    return queries


def parse_index_buckets(path: Path | str) -> Dict[str, List[str]]:
    """
    Parses all buckets from the query index.

    :return: A dictionary with bucket keys and their queries.
    """
    path = Path(path).resolve()
    payload = yaml.safe_load(open(path, encoding="utf8"))

    buckets = {}
    for key, val in payload["buckets"].items():
        buckets[key] = val["queries"]
    return buckets
