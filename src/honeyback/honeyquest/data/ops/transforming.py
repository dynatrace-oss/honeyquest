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
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd

from ...common.las import expand_las
from ...common.models.query import Query, QueryResponseForStorage
from ...common.models.user import User
from ..types import HoneyquestResults


def flatten_experiments(results: Dict[str, HoneyquestResults]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Flattens multiple honeyquest results into two pandas DataFrames.
    One contains all responses, and the other contains all user profiles.

    :param results: A dictionary of result objects, keyed by experiment name
    :return: A tuple of data frame for responses and profiles, respectively
    """
    marks_dfs, users_dfs = [], []
    rt = HoneyquestResultsTransformer()

    for name, res in results.items():
        dfm = rt.flatten_responses(res.responses, experiment=name)
        dfu = rt.flatten_users(res.profiles, experiment=name)
        marks_dfs.append(dfm)
        users_dfs.append(dfu)

    marks_df = pd.concat(marks_dfs, axis=0).reset_index(drop=True)
    users_df = pd.concat(users_dfs, axis=0).reset_index(drop=True)

    marks_df.index.name = "mid"
    users_df.index.name = None

    # check if uids are unique per experiment
    if "eid" in users_df.columns:
        unique_uids = users_df.groupby("eid").apply(lambda df: df.uid.nunique() == len(df))
        assert unique_uids.all(), "UIDs are not unique per experiment"

    return marks_df, users_df


class HoneyquestResultsTransformer:
    """
    Holds utility functions for transforming honeyquest results into pandas DataFrames.
    This is a stateful class that keeps track of globally-unique response ids to avoid collisions,
    so you should create a new instance for each analysis session.
    """

    def __init__(self, rid_hash_length: int = 32):
        self._rid_hashes: Set[str] = set()
        self._rid_hash_length = rid_hash_length

    def flatten_users(
        self,
        users: List[User],
        experiment: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Flattens user profiles into a pandas DataFrame that we call `users`.

        :param users: The user profiles
        :param experiment: (optional) experiment column to add to the DataFrame
        :return: A pandas DataFrame containing the user profiles
        """
        rows = []
        for u in users:
            row = dict(
                eid=experiment,
                uid=u.uid,
                job=u.profile.job,
                years=u.profile.years,
                rank=u.profile.rank,
                nickname=u.profile.nickname,
                color=u.profile.color,
            )
            rows.append(row)

        return pd.DataFrame(rows)

    def flatten_responses(
        self,
        responses: List[QueryResponseForStorage],
        experiment: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Flattens query responses into a pandas DataFrame that we call `marks`.
        Every response is expanded into as many rows as there are answer marks.

        :param responses: The query responses and user profiles
        :param experiment: (optional) experiment column to add to the DataFrame
        :return: A pandas DataFrame containing the responses
        """
        rows = []

        for r in responses:
            row = dict(
                eid=experiment,
                uid=r.uid,
                # we don't need the questionnaire id and
                # don't want to confuse it with query ids
                # sid=r.qid,
                rid=self._compute_unique_response_id(experiment, r),
                qid=r.query.id,
                query_label=r.query.label,
                query_type=r.query.type,
                answer_time=pd.Timestamp(r.answer.timestamp),
                response_time=r.answer.response_time.total_seconds(),
            )

            # possibly flatten each answer line into a separate row
            for i, (line, atype) in enumerate(r.answer.lines):
                row.update(dict(answer_rank=i, answer_line=line, answer_type=atype))
                rows.append(row.copy())

            # no lines selected? add a neutral row
            if not r.answer.lines:
                row.update(dict(answer_rank=-1, answer_line=-1, answer_type="neutral"))
                rows.append(row)

        return pd.DataFrame(rows)

    def _compute_unique_response_id(
        self,
        experiment: Optional[str],
        resp: QueryResponseForStorage,
    ) -> str:
        """
        Computes a globally-unique response id for this response.
        This can be used to later associate the marks with the original response.

        :param experiment: The experiment name
        :param resp: The query response
        :return: A globally-unique response id
        """
        message = f"{experiment}/{resp.uid}/{resp.query.id}/{resp.answer.timestamp.timestamp()}"
        digest = hashlib.sha256(message.encode("utf-8")).hexdigest()[: self._rid_hash_length]

        if digest in self._rid_hashes:
            errormsg = f"answer hash collision for message '{message}' - increase hash length?"
            raise TypeError(errormsg)
        self._rid_hashes.add(digest)

        return digest


def flatten_queries(qur: Dict[str, Query], drop_tutorial: bool = False) -> pd.DataFrame:
    """
    Creates a pandas DataFrame containing the query metadata.

    :param qur: The queries, indexed by query id
    :param drop_tutorial: Whether to drop the tutorial queries
    :return: A pandas DataFrame containing the query metadata
    """
    qids = list(qur.keys())

    # basic query metadata
    query_label = [qur[q].label for q in qids]
    query_type = [qur[q].type for q in qids]

    # on deceptive queries
    applied_honeywire = [qur[q].get_annotation("honeypatch/applied-honeywire") for q in qids]
    original_query = [qur[q].get_annotation("honeypatch/original-query") for q in qids]
    original_risky = [qur[q].get_annotation("honeypatch/original-risky") for q in qids]
    original_risky = [e if e is not None else False for e in original_risky]  # None -> False

    # on risky queries
    risk_type = [qur[q].get_annotation("risk/type") for q in qids]
    present_vulnerability = [qur[q].get_annotation("risk/present-vulnerability") for q in qids]
    present_weakness = [qur[q].get_annotation("risk/present-weakness") for q in qids]
    present_attack = [qur[q].get_annotation("risk/present-attack") for q in qids]

    # number of risky and deceptive lines
    num_risky_lines = [len(expand_las(qur[q].get_risky_lines())) for q in qids]
    num_deceptive_lines = [len(expand_las(qur[q].get_deceptive_lines())) for q in qids]
    num_lines = [len(qur[q].data.splitlines()) for q in qids]

    # the first not-None value with preference: weakness > vulnerability > attack
    present_risk = [
        next((e for e in (w, v, a) if e is not None), None)
        for w, v, a in zip(present_weakness, present_vulnerability, present_attack)
    ]

    df = pd.DataFrame(
        {
            "query_label": query_label,
            "query_type": query_type,
            "original_query": original_query,
            "original_risky": original_risky,
            "applied_honeywire": applied_honeywire,
            "risk_type": risk_type,
            "present_vulnerability": present_vulnerability,
            "present_weakness": present_weakness,
            "present_attack": present_attack,
            "present_risk": present_risk,
            "num_risky_lines": num_risky_lines,
            "num_deceptive_lines": num_deceptive_lines,
            "num_lines": num_lines,
        },
        index=qids,
    )
    df.index.name = "qid"

    if drop_tutorial:
        df = df.query("query_type != 'tutorial'")

    return df


def merge_user_activity(users: pd.DataFrame, activity: pd.DataFrame) -> pd.DataFrame:
    """
    Merges the user activity details into the user profiles.
    Also sorts the users by their first seen timestamp.

    :param users: The user profiles dataframe
    :param activity: The user activity dataframe
    :return: The user profiles dataframe with activity details
    """
    df = users.merge(activity, on=["eid", "uid"], how="left").sort_values("first_seen")
    df.reset_index(drop=True, inplace=True)

    return df
