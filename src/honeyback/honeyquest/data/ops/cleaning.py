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

from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Set, Tuple

from ..types import HoneyquestResults
from .counting import get_query_counts


def filter_experiments(
    results: Dict[str, HoneyquestResults],
    experiments: Optional[List[str]] = None,
) -> Dict[str, HoneyquestResults]:
    """
    Drop all results that do not belong to the specified experiments.

    :param results: A dictionary of HoneyquestResults, keyed by experiment
    :param experiments: List of experiment names, defaults to None (all experiments)
    :return: A new dictionary with only the specified experiments
    """
    if experiments is None:
        return results
    return {k: v for k, v in results.items() if k in experiments}


def merge_experiments(
    results: Dict[str, HoneyquestResults],
    experiments: List[str],
) -> Dict[str, HoneyquestResults]:
    """
    Merges the given experiments into one experiment.
    The target experiment is the one mentioned first in the list.

    :param results: A dictionary of HoneyquestResults, keyed by experiment
    :param experiments: A list of experiments to merge
    """
    assert len(experiments) > 1, "need at least two experiments to merge"
    target_experiment = experiments[0]
    drop_experiments = experiments[1:]

    for exp in drop_experiments:
        results[target_experiment].responses.extend(results[exp].responses)
        results[target_experiment].profiles.extend(results[exp].profiles)

    return {exp: res for exp, res in results.items() if exp not in drop_experiments}


def drop_tutorial(results: Dict[str, HoneyquestResults], clean_profiles: bool = True):
    """
    Drop responses that have type "tutorial".
    Data is modified IN-PLACE.

    :param results: A dictionary of HoneyquestResults, keyed by experiment
    :param clean_profiles: Whether to also drop profiles of users that only had tutorial responses
    """
    previous_counts = get_query_counts(results)

    for exp, res in results.items():
        new_responses = [r for r in res.responses if r.query.type != "tutorial"]

        new_profiles = res.profiles
        if clean_profiles:
            remaining_uids = {r.uid for r in new_responses}
            new_profiles = [p for p in res.profiles if p.uid in remaining_uids]

        results[exp] = HoneyquestResults(responses=new_responses, profiles=new_profiles)

    new_counts = get_query_counts(results)
    num_dropped = len(previous_counts.keys() - new_counts.keys())
    print(f"dropped {num_dropped} users with only tutorial queries")


def drop_inactive(results: Dict[str, HoneyquestResults], min_responses: int) -> int:
    """
    Drop all users with less than `min_responses` responses.
    Counts are computed over all experiments.
    Data is modified IN-PLACE.

    :param results: A dictionary of HoneyquestResults, keyed by experiment
    :param min_responses: Minimum number of responses per user
    :return: Number of users that were dropped
    """
    counts = get_query_counts(results)
    keep_uids = set(uid for uid, count in counts.items() if count >= min_responses)

    for exp, res in results.items():
        new_responses = [r for r in res.responses if r.uid in keep_uids]
        new_profiles = [p for p in res.profiles if p.uid in keep_uids]
        results[exp] = HoneyquestResults(responses=new_responses, profiles=new_profiles)

    num_dropped = len(counts.keys() - keep_uids)
    print(f"dropped {num_dropped} users with fewer than {min_responses} queries")
    return num_dropped


def drop_users(
    results: Dict[str, HoneyquestResults],
    drop_uids: Optional[Iterable[str]] = None,
    keep_uids: Optional[Iterable[str]] = None,
):
    """
    Drop all responses and profiles of the given users.
    One can either specify uids to drop or uids to keep.
    Data is modified IN-PLACE.

    :param results: A dictionary of HoneyquestResults, keyed by experiment
    :param drop_uids: A list of uids to drop, defaults to None
    :param keep_uids: A list of uids to keep, defaults to None
    """
    assert (drop_uids is not None) ^ (keep_uids is not None), "cannot drop and keep uids"

    def __filter_uid(uid: str) -> bool:
        if keep_uids is not None:
            return uid in keep_uids
        if drop_uids is not None:
            return uid not in drop_uids
        return True  # unreachable

    for exp, res in results.items():
        new_responses = [r for r in res.responses if __filter_uid(r.uid)]
        new_profiles = [p for p in res.profiles if __filter_uid(p.uid)]
        results[exp] = HoneyquestResults(responses=new_responses, profiles=new_profiles)


def drop_timeframe(
    results: Dict[str, HoneyquestResults],
    min_timestamp: Optional[datetime] = None,
    max_timestamp: Optional[datetime] = None,
):
    """
    Drop all responses that were made outside of the given timeframe.
    Data is modified IN-PLACE.

    :param results: A dictionary of HoneyquestResults, keyed by experiment
    :param min_timestamp: Minimum timestamp, defaults to None
    :param max_timestamp: Maximum timestamp, defaults to None
    """
    for exp, res in results.items():
        new_responses = [
            r
            for r in res.responses
            if (min_timestamp is None or r.answer.timestamp >= min_timestamp)
            and (max_timestamp is None or r.answer.timestamp <= max_timestamp)
        ]

        results[exp] = HoneyquestResults(responses=new_responses, profiles=res.profiles)


def drop_duplicate_responses(results: Dict[str, HoneyquestResults]):
    """
    Drop extraneous duplicate responses from the same user.
    Only the first response is kept.
    Data is modified IN-PLACE.

    :param results: A dictionary of HoneyquestResults, keyed by experiment
    """
    dropped_responses: Dict[Tuple[str, str], Counter[str]] = defaultdict(Counter)

    for exp, res in results.items():
        seen_responses: Dict[str, Set[str]] = defaultdict(set)
        new_responses = []
        for r in res.responses:
            if r.query.id not in seen_responses[r.uid]:
                new_responses.append(r)
                seen_responses[r.uid].add(r.query.id)
            else:
                dropped_responses[(exp, r.uid)][r.query.id] += 1

        results[exp] = HoneyquestResults(responses=new_responses, profiles=res.profiles)

    for (exp, uid), counter in dropped_responses.items():
        for qid, cnt in counter.items():
            print(f"dropped {cnt} duplicate responses from [{exp}] {uid} to {qid}")


def merge_users(results: Dict[str, HoneyquestResults], uids: List[str]):
    """
    Merges the given users into one user, across experiments.
    The uid with the most recent responses is kept.
    Data is modified IN-PLACE.

    :param results: A dictionary of HoneyquestResults, keyed by experiment
    :param uids: A list of uids to merge
    """
    most_recent_uid = _check_if_users_can_be_merged(results, uids)

    for res in results.values():
        # replace uid in responses
        for r in res.responses:
            if r.uid in uids:
                r.uid = most_recent_uid

        # replace uid in profiles
        for p in res.profiles:
            if p.uid in uids:
                p.uid = most_recent_uid

        # remove duplicate profiles based on uid (per experiment)
        res.profiles = list({p.uid: p for p in res.profiles}.values())


def _check_if_users_can_be_merged(results: Dict[str, HoneyquestResults], uids: List[str]):
    """
    In preparation for merging the given users, check if the merge is possible.
    Checks if the answers from this user are unique per experiment.

    Further returns the UID that had a response most recently.

    :param results: A dictionary of HoneyquestResults, keyed by experiment
    :param uids: A list of uids to merge
    :return: The UID that had a response most recently
    """
    # store all queries that were answered by the given uids, per experiment
    queries_per_experiment: Dict[str, Set[str]] = defaultdict(set)

    # find the uid that provided the most recent response
    most_recent_uid = None
    most_recent_timestamp = None

    for exp, res in results.items():
        for r in res.responses:
            if r.uid in uids:
                # ensure that the same query is not answered twice by the same user,
                # for the same experiment, if we would proceed with the merge now
                if r.query.id in queries_per_experiment[exp]:
                    raise ValueError(f"duplicate query {r.query.id} for {r.uid} in {exp}")
                queries_per_experiment[exp].add(r.query.id)

                # find the most recent uid
                if not most_recent_timestamp or r.answer.timestamp > most_recent_timestamp:
                    most_recent_uid = r.uid
                    most_recent_timestamp = r.answer.timestamp

    return most_recent_uid
