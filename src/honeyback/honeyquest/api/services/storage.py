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

import gzip
import json
import logging
import shutil
from collections import defaultdict
from functools import cache
from pathlib import Path
from tempfile import mkdtemp
from typing import IO, Dict, List, Literal, Set, cast

from ...common.models.admin import SizeItemsDict
from ...common.models.feedback import FeedbackForStorage
from ...common.models.query import BaseQueryResponseForStorage, QueryResponseForStorage
from ...common.models.user import User
from ...common.timestamps import epoch_time_to_iso_str
from ..config import get_settings

# reuse the uvicorn logger
log = logging.getLogger("uvicorn.error")

ResponseCacheType = Dict[str, Set[str]]


class PersistenceService:
    """Reads and writes user and questionnaire data to the disk."""

    def __init__(self, honeyquest_results: Path | str, compressed: bool = False):
        """
        Initializes the persistence service.

        :param honeyquest_results: Path where results shall be stored
        :param compressed: Stores responses as `.jsonl.gz` instead of `.jsonl`
        """
        self._results_path = Path(honeyquest_results)
        self._compressed = compressed
        self._profiles_path = self._results_path / "profiles"
        self._responses_path = self._results_path / "responses"
        self._feedback_path = self._results_path / "feedback"
        self._response_cache: ResponseCacheType = defaultdict(set)
        self._init_persistence()

    def store_user(self, user: User):
        path = self._profiles_path / f"{user.uid}.json"
        with open(path, mode="w+", encoding="utf8") as stream:
            stream.write(user.model_dump_json())

    def store_feedback(self, uid: str, feedback: FeedbackForStorage):
        path = self._feedback_path / f"{uid}.jsonl"
        with open(path, mode="a+", encoding="utf8") as stream:
            stream.write(feedback.model_dump_json())
            stream.write("\n")

    def store_response(self, uid: str, qid: int, response: QueryResponseForStorage):
        self._response_cache[uid].add(response.query.id)
        qid_iso = epoch_time_to_iso_str(qid)
        path = self._responses_path / f"{uid}_{qid}_{qid_iso}.jsonl"
        with self._fopen_response(path, mode="a+") as stream:
            stream.write(response.model_dump_json())
            stream.write("\n")

    def read_user(self, uid: str) -> User:
        path = self._profiles_path / f"{uid}.json"
        with open(path, encoding="utf8") as stream:
            jzon = json.load(stream)
            user = User(**jzon)
            return user

    def read_feedback(self, uid: str) -> List[FeedbackForStorage]:
        path = self._feedback_path / f"{uid}.jsonl"
        with open(path, encoding="utf8") as stream:
            result = []
            for line in stream:
                jzon = json.loads(line)
                feedback = FeedbackForStorage(**jzon)
                result.append(feedback)
            return result

    def exists_user(self, uid: str) -> bool:
        path = self._profiles_path / f"{uid}.json"
        return path.exists()

    def get_answered_queries(self, uid: str) -> Set[str]:
        # per user session, cache already answered question ids
        return self._response_cache[uid]

    def get_number_of_answered_queries(self, uid: str) -> int:
        return len(self.get_answered_queries(uid))

    def clear_results(self):
        # actually, we just put them into a temporary trash folder
        trash = Path(mkdtemp(prefix="honeyquest_trash_"))
        shutil.move(self._profiles_path, trash / self._profiles_path.name)
        shutil.move(self._responses_path, trash / self._responses_path.name)
        shutil.move(self._feedback_path, trash / self._feedback_path.name)
        log.info(f"Moved results to trash directory {trash}")

        # create empty directories, invalidate caches
        self._init_persistence()

    def sync_cache(self):
        # allows to re-hydrate the response cache from disk during runtime
        # will only append new responses, not overwrite existing ones
        self._hydrate_response_cache()

    def get_diagnostics(self, category: Literal["responses", "users", "feedback"]) -> SizeItemsDict:
        if category == "responses":
            items = {k: SizeItemsDict(v) for k, v in self._response_cache.items()}
            return SizeItemsDict(items)
        if category == "users":
            uids = [p.stem for p in self._profiles_path.iterdir() if p.suffix == ".json"]
            users = {u: self.read_user(u) for u in uids}
            return SizeItemsDict(users)
        if category == "feedback":
            uids = [p.stem for p in self._feedback_path.iterdir() if p.suffix == ".jsonl"]
            feedback = {u: SizeItemsDict(self.read_feedback(u)) for u in uids}
            return SizeItemsDict(feedback)
        return SizeItemsDict({})

    def _init_persistence(self):
        # ensure directories exist
        self._profiles_path.mkdir(parents=True, exist_ok=True)
        self._responses_path.mkdir(parents=True, exist_ok=True)
        self._feedback_path.mkdir(parents=True, exist_ok=True)
        # ensure that the response cache is valid
        self._response_cache.clear()
        self._hydrate_response_cache()

    def _hydrate_response_cache(self):
        """
        Reads ALL responses from disk and caches only the query ids.
        Enables to check if a user has already answered a question.
        """
        for path in self._responses_path.iterdir():
            with self._fopen_response(path, mode="r") as stream:
                for line in stream:
                    response = BaseQueryResponseForStorage.model_validate_json(line)
                    uid, query_id = response.uid, response.query.id
                    self._response_cache[uid].add(query_id)

        nqueries = sum(len(ids) for ids in self._response_cache.values())
        nusers = len(self._response_cache)
        log.info(f"Read {nusers:,d} users and {nqueries:,d} queries into response cache")

    def _fopen_response(self, filepath: Path | str, mode: str) -> IO:
        """
        Transparently open files normally or with gzip compression.
        Either way, files are opened in text-mode with utf8 encoding.

        :param file: Path to the file
        :param mode: Mode like in a normal call to `open()`
        :return: A File object
        """
        if self._compressed:
            filepath = f"{str(filepath).removesuffix('.gz')}.gz"  # ensure suffix
            mode = mode.replace("w", "wt").replace("r", "rt").replace("a", "at")
            return cast(IO[bytes], gzip.open(filepath, mode=mode, encoding="utf8"))  # cast for mypy

        return open(filepath, mode=mode, encoding="utf8")


@cache
def get_persistence_svc() -> PersistenceService:
    """Provides a singleton (cached instance) of `PersistenceService`."""
    settings = get_settings()
    assert settings.honeyquest_results is not None
    return PersistenceService(settings.honeyquest_results, settings.compress_results)
