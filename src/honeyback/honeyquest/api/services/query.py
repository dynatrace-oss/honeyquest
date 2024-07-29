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
import random
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Dict, List, Literal, Optional, Set

import yaml

from ...common.models.admin import SizeItemsDict
from ...common.models.query import Query, QueryBucket
from ..config import get_settings
from ..services.storage import PersistenceService, get_persistence_svc

# reuse the uvicorn logger
log = logging.getLogger("uvicorn.error")


@dataclass
class QuerySamplerIndex:
    """In-memory store of the query index, optimized for fast look-ups."""

    # maps a query id to its chunk index
    chunk_indexes: Dict[str, int] = field(default_factory=dict)
    # full paths of all query chunks
    chunk_paths: List[str] = field(default_factory=list)

    # a list of all query ids (for sampling)
    query_listing: List[str] = field(default_factory=list)

    # a list of queries organized in a bucket
    bucket_queries: Dict[str, List[str]] = field(default_factory=dict)
    # a list of sampling strategies for each bucket
    bucket_strategies: Dict[str, Literal["random", "sorted"]] = field(default_factory=dict)
    # a list of bucket descriptions for each bucket
    bucket_descriptions: Dict[str, str] = field(default_factory=dict)

    # an enforced bucket order
    bucket_order: List[str] = field(default_factory=list)

    def get_chunk_path(self, query_id: str):
        if query_id not in self.chunk_indexes:
            raise KeyError(f"query id '{query_id}' not found in index - refresh index with dagit?")
        chunk_index = self.chunk_indexes[query_id]
        return self.chunk_paths[chunk_index]

    def sample_query_id(self, avoid_query_ids: Optional[Set[str]] = None) -> Optional[str]:
        avoid_query_ids = avoid_query_ids or set()

        # if given and possible, try to follow an enforced query order first
        if self.bucket_order and (qid := self._next_in_bucket_order(avoid_query_ids)):
            return qid

        # otherwise, sample randomly from the full query listing
        return QuerySamplerIndex._fast_resample(self.query_listing, avoid_query_ids)

    def get_buckets(self) -> Optional[List[QueryBucket]]:
        if not self.bucket_order:
            return None

        buckets: List[QueryBucket] = []
        for bucket in self.bucket_order:
            buckets.append(
                QueryBucket(
                    name=bucket,
                    strategy=self.bucket_strategies[bucket],
                    description=self.bucket_descriptions[bucket],
                    query_size=len(self.bucket_queries[bucket]),
                )
            )

        return buckets

    def _next_in_bucket_order(self, avoid_query_ids: Set[str]) -> Optional[str]:
        for bucket in self.bucket_order:
            queries = self.bucket_queries[bucket]
            strategy = self.bucket_strategies[bucket]

            # first query from this bucket not in `avoid_query_ids`
            if strategy == "sorted":
                for query_id in queries:
                    if query_id not in avoid_query_ids:
                        return query_id

            # random query from this bucket not in `avoid_query_ids`
            elif strategy == "random":
                if qid := QuerySamplerIndex._fast_resample(queries, avoid_query_ids):
                    return qid

        # nothing left to sample from
        return None

    def _refresh_listing(self):
        self.query_listing = list(self.chunk_indexes.keys())

    @staticmethod
    def _fast_resample(elements: List[str], avoid_elements: Set[str]) -> Optional[str]:
        # samples from `elements`, but avoids `avoid_elements`
        # with fast, memory-efficient resampling of ids
        size = len(elements)
        fringe: Set[int] = set()

        while len(fringe) < size:
            # resample until we have a not-sampled-yet index
            i = random.randrange(0, size)
            if i in fringe:
                continue
            fringe.add(i)

            # return if this query id wasn't sampled yet
            # otherwise, continue resampling
            if elements[i] not in avoid_elements:
                return elements[i]

        # nothing left to sample from
        return None


class QuerySamplerService:
    """Reads the query index, samples from it, and parses queries."""

    def __init__(
        self,
        honeyquest_data: Path | str,
        index_name: str,
        persistence: PersistenceService,
        duplicates: bool = False,
    ):
        self._data_path: Path = Path(honeyquest_data)
        self._index_name = index_name
        self._persistence = persistence
        self._duplicates = duplicates
        self._index: QuerySamplerIndex = QuerySamplerIndex()
        self._parse_index()

    def sample(self, uid: str) -> Optional[Query]:
        """
        Get a random query from the query store or `None` if there is nothing to sample.
        If `_duplicates` is `False`, samples are drawn without replacement for this user.
        For this, we ask persistence for the query ids that were already answered by this user.

        :param uid: The user id to sample for and avoid duplicates for
        :return: A randomly sampled query
        """
        # TODO: TR-716 sampling duplicates and enforcing a query order is not supported right now
        avoid_ids = None if self._duplicates else self._persistence.get_answered_queries(uid)
        query_id = self._index.sample_query_id(avoid_ids)
        if not query_id:
            return None

        query = self._parse_query(query_id)
        return query

    def get_number_of_queries(self) -> int:
        """Gets the total number of queries in the query sampler index."""
        return len(self._index.query_listing)

    def get_query(self, query_id: str) -> Query:
        """
        Get a query from the query store by its id.
        A `KeyError` is raised for non-existent ids.

        :param query_id: The query id to read
        :return: The Query object
        """
        return self._parse_query(query_id)

    def exists_query(self, query_id: str) -> bool:
        """
        Checks if the query with that id exists in the query store.

        :param query_id: The query id to check
        """
        return query_id in self._index.chunk_indexes

    def get_buckets(self) -> Optional[List[QueryBucket]]:
        """Gets the buckets of the query sampler index, if specified."""
        return self._index.get_buckets()

    def get_diagnostics(self) -> SizeItemsDict:
        items = sorted(self._index.chunk_indexes.keys())
        return SizeItemsDict(items)

    def _parse_query(self, query_id: str) -> Query:
        chunk_path = self._data_path.joinpath(self._index.get_chunk_path(query_id)).resolve()
        with open(chunk_path, encoding="utf8") as stream:
            chunk = yaml.safe_load_all(stream)
            for query in chunk:
                if query["id"] == query_id:
                    return Query(**query)

        raise ValueError(
            f"query id '{query_id}' not found in chunk {chunk_path} - refresh index with dagit?"
        )

    def _parse_index(self):
        qsi = QuerySamplerIndex()
        index_path = self._data_path / "index" / f"{self._index_name}.yaml"

        with open(index_path, encoding="utf8") as stream:
            document = yaml.safe_load(stream)

            # parse entries to custom data structure
            index = document["index"]
            if "order" in document:
                qsi.bucket_order = document["order"]
            if "buckets" in document:
                buckets = document["buckets"].items()
                qsi.bucket_queries = {k: v["queries"] for k, v in buckets}
                qsi.bucket_strategies = {k: v["strategy"] for k, v in buckets}
                qsi.bucket_descriptions = {k: v.get("description", k) for k, v in buckets}

            assert not (
                self._duplicates and len(qsi.bucket_order) > 0
            ), "sampling duplicates AND enforcing a bucket order is not supported right now"

            # we invert the index to be fast on lookup but still memory-efficient, i.e.,
            # we map each query id in `query_ids` to an integer index in `chunk_paths`
            # from where on we make to the real lookup to the file path
            nchunks, nqueries = len(index), 0
            for i, (chunk_path, query_ids) in enumerate(index.items()):
                qsi.chunk_paths.append(chunk_path)

                nqueries += len(query_ids)
                for qid in query_ids:
                    qsi.chunk_indexes[qid] = i

            qsi._refresh_listing()
            self._index = qsi
            log.info(f"Read {nqueries:,d} query ids (in {nchunks:,d} chunks) from {index_path}")


@cache
def get_query_sampler_svc() -> QuerySamplerService:
    """Provides a singleton (cached instance) of `QuerySamplerService`."""
    settings = get_settings()
    persistence = get_persistence_svc()
    assert settings.honeyquest_data is not None
    assert settings.honeyquest_index is not None
    return QuerySamplerService(
        honeyquest_data=settings.honeyquest_data,
        index_name=settings.honeyquest_index,
        persistence=persistence,
        duplicates=settings.sample_duplicates,
    )
