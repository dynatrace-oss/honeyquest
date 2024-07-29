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

from collections import Counter
from typing import Dict

import pandas as pd

from ...common.las import expand_las
from ...common.models.query import Query
from ..types import HoneyquestResults


def get_overview_counts(marks: pd.DataFrame) -> pd.DataFrame:
    """
    Sums the number of users, responses and marks per experiment.

    :param marks: The flattened marks dataframe
    :return: A dataframe containing the overview statistics
    """
    df = pd.DataFrame(
        {
            "users": marks.groupby("eid").uid.nunique(),
            "responses": marks.groupby("eid").rid.nunique(),
            "marks": marks.groupby("eid").size(),
        }
    )

    df.loc["total"] = df.sum()
    return df


def get_query_counts(results: Dict[str, HoneyquestResults]) -> Dict[str, int]:
    """
    Total number of queries per user, over all experiments.

    :param results: A dictionary of HoneyquestResults, keyed by experiment
    :return: A dictionary of query counts, keyed by uid
    """
    counter: Counter[str] = Counter()
    for res in results.values():
        counter.update([r.uid for r in res.responses])

    return dict(counter)


def get_user_activity(results: Dict[str, HoneyquestResults], marks: pd.DataFrame) -> pd.DataFrame:
    """
    Retrieves the first and last time a user was seen in the experiment.
    This is inferred from the first and last time they submitted a response.

    :param results: The flattened marks dataframe
    :param marks: The flattened marks dataframe
    :return: A dataframe containing "first_seen" and "last_seen" for each user
    """
    df_times = (
        marks.groupby(["eid", "uid"])
        .agg({"answer_time": ["min", "max"]})
        .rename(columns={"min": "first_seen", "max": "last_seen"})
    )

    # flatten hierarchical columns and reset index
    df_times.columns = df_times.columns.get_level_values(1)
    df_times.reset_index(inplace=True)
    df_times.index.name = None

    # put the query counts into a dataframe
    df_counts = pd.DataFrame.from_dict(get_query_counts(results), orient="index")
    df_counts.index.name = "uid"
    df_counts.columns = pd.Index(["num_answers"])
    df_counts = df_counts.astype({"num_answers": "Int64"})

    # merge the counts and times
    df = df_times.merge(df_counts, on="uid")
    return df


def get_paired_query_ids(queries: pd.DataFrame) -> pd.DataFrame:
    """
    Retrieves those query ids that belong to a matched pair.
    That means that there is an original (risky) query and a derived deceptive query.

    :param queries: Queries frame with "original_query" and "applied_honeywire" columns
    :return: A dataframe with "original_query" and "applied_honeywire" columns
    """
    df_dcpt = queries.query("original_risky")[["original_query", "applied_honeywire"]]
    df_risk = df_dcpt.copy().reset_index(drop=True).set_index("original_query")
    df_risk.index.name = "qid"

    # risky and deceptive queries, with their matching honeywires
    return pd.concat([df_dcpt, df_risk])


def get_query_rating(query_id: str, marks: pd.DataFrame, queries: Dict[str, Query]) -> pd.DataFrame:
    """
    Summarizes statistics for a single query.
    Retrieves a dataframe with the query text, line number, and the number of
    hack and trap marks for each line, and whether the line is deceptive or risky.

    :param query_id: The query id to analyse
    :param marks: The marks dataframe
    :param queries: The queries dict, keyed by query id
    :return: A dataframe with the query text, line number, marks and annotations
    """
    marks = marks.query("qid == @query_id")
    hack_lines = marks.query("answer_type == 'hack'").answer_line.value_counts()
    trap_lines = marks.query("answer_type == 'trap'").answer_line.value_counts()
    hack_lines.name = "hack"
    trap_lines.name = "trap"

    query = queries[query_id]
    text_lines = query.data.splitlines()
    dcpt_lines = expand_las(query.get_deceptive_lines())
    risk_lines = expand_las(query.get_risky_lines())

    # dataframe with text and index that starts at 1
    df = pd.DataFrame(text_lines, columns=["text"], index=range(1, len(text_lines) + 1))
    df["deceptive"] = df.index.isin(dcpt_lines)
    df["risky"] = df.index.isin(risk_lines)

    # add the hack and trap counts
    df["hack"] = hack_lines
    df["hack"] = df.hack.fillna(0).astype(int)
    df["trap"] = trap_lines
    df["trap"] = df.trap.fillna(0).astype(int)

    return df
