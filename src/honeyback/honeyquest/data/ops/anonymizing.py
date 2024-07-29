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

import hashlib
from typing import Dict, Set

from ...common.models.query import Query
from ..types import HoneyquestResults


def anonymize_results(results: Dict[str, HoneyquestResults], anonymize_qids: Set[str]):
    """
    Anonymize the query ids in the given results by replacing them with a hash.
    Data is modified IN-PLACE.

    :param results: A dictionary of HoneyquestResults, keyed by experiment
    :param anonymize_qids: A set of query ids to anonymize
    """
    for exp, res in results.items():
        for r in res.responses:
            if r.query.id in anonymize_qids:
                r.query.id = _anonymized_qid(r.query.id)
        results[exp] = HoneyquestResults(**res.model_dump())


def anonymize_queries(queries: Dict[str, Query], anonymize_qids: Set[str]) -> Dict[str, Query]:
    """
    Anonymize the query ids in the given query dictionary by replacing them with a hash.
    Data is modified IN-PLACE.

    :param queries: A dictionary of queries, keyed by query id
    :param anonymize_qids: A set of query ids to anonymize
    """
    result = {}
    for qid, q in queries.items():
        if qid in anonymize_qids:
            q.id = _anonymized_qid(qid)
        result[q.id] = Query(**q.model_dump())

    return result


def _anonymized_qid(qid: str) -> str:
    return "ANONYMIZED." + hashlib.sha256(qid.encode("utf-8")).hexdigest()
