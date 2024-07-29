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

from typing import Tuple

import numpy as np
import pandas as pd


def compute_mark_statistics(
    marks: pd.DataFrame,
    queries: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Computes a table with statistics about each marked line.

    This function returns a 3-tuple of dataframes:
    - The first dataframe counts the mark statistics, grouped by `mrk_line`.
    - The second dataframe counts the mark statistics, grouped by `applied_honeywire`.
    - The third dataframe counts the mark statistics, grouped by `present_risk`.

    :param marks: A dataframe containing the flattened responses
    :param queries: A dataframe containing the queries
    :return: A 3-tuple of dataframes with the mark statistics
    """
    # merge in the annotations and simply sum the mark counts
    df = pd.merge(marks, queries, on="qid", how="left", validate="m:1")

    assert "applied_honeywire" in df.columns
    assert "present_risk" in df.columns
    assert "mrk_line" in df.columns

    # per honeywire
    df_dcpt_grp = df.groupby("applied_honeywire")[["mrk_hack_on_dcpt", "mrk_trap_on_dcpt"]]
    df_dcpt = df_dcpt_grp.sum().astype(int).sort_values("mrk_hack_on_dcpt", ascending=False)

    # per risk
    df_risk_grp = df.groupby("present_risk")[["mrk_hack_on_risk", "mrk_trap_on_risk"]]
    df_risk = df_risk_grp.sum().astype(int).sort_values("mrk_hack_on_risk", ascending=False)

    str_cols = ["mrk_query_type", "applied_honeywire", "present_risk"]
    cols = [
        "mrk_on_dcpt",
        "mrk_on_risk",
        "mrk_hack_on_dcpt",
        "mrk_trap_on_dcpt",
        "mrk_hack_on_risk",
        "mrk_trap_on_risk",
        "mrk_hack",
        "mrk_trap",
        "mrk_neutral",
    ] + str_cols

    # per line (neglecting if the line has any annotations)
    df_lines_grp = df.groupby("mrk_line")[cols]

    # sum over all lines, but exclude the string columns
    df_lines = df_lines_grp.agg({k: "sum" if k not in str_cols else "first" for k in cols})
    df_lines = df_lines.astype({k: int for k in cols if k not in str_cols})
    df_lines = df_lines[df_lines.sum(axis=1, numeric_only=True) > 0]

    # replace 0 values in string columns with None
    df_lines.applied_honeywire = df_lines.applied_honeywire.replace(0, None)
    df_lines.present_risk = df_lines.present_risk.replace(0, None)

    # right now, it can never be the case that a line is both risky and deceptive,
    # however, note that this could happen some day because we group by lines ...
    assert not np.all((df_lines.mrk_on_risk > 0) & (df_lines.mrk_on_dcpt > 0))

    return df_lines, df_dcpt, df_risk


def compute_mark_ranking(marks: pd.DataFrame) -> pd.DataFrame:
    """
    Computes a table that lists what query ids received the most marks.
    The index will be the query id `qid` and the only column will be `count`.

    :param marks: A dataframe containing the flattened responses
    :return: A dataframe with the query ids and their respective mark counts
    """
    assert "qid" in marks.columns

    df = marks.query("answer_line > 0").groupby("qid").size().to_frame("count")
    df = df.sort_values(by="count", ascending=False)
    return df


def compute_mark_distribution_by_mark_variant(responses: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the distribution of mark variants over responses.
    The index will be the mark variant (type `AnswerVariant`)
    and the columns will be all the `_var` columns from the responses.

    :param responses: The responses frame with all `*_var` columns
    :return: A dataframe with the mark variant distribution
    """
    cols = [c for c in responses.columns if c.endswith("_var")]
    counts = responses[cols].apply(pd.Series.value_counts)
    counts = counts / responses.shape[0] * 100.0
    return counts


def compute_mark_distribution_by_mark_completeness(responses: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the distribution of responses that placed marks on all lines.
    The index will be the condition (`False` or `True`)
    and the columns will be all the `_all` columns from the responses.

    :param responses: The responses frame with all "ans_all_*" columns
    :return: A dataframe with the mark completeness distribution
    """
    assert "ans_all" in responses.columns
    assert "ans_all_hack" in responses.columns
    assert "ans_all_trap" in responses.columns

    cols = ["ans_all", "ans_all_hack", "ans_all_trap"]
    counts = responses[cols].apply(pd.Series.value_counts).fillna(0)
    counts = counts / responses.shape[0] * 100.0
    return counts


def compute_mark_distribution_by_line_annotation_length(queries: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the distribution of the number of line annotations in queries.
    The index will be the number of line annotations and the only column will be `count`.

    :param queries: Queries frame with "num_risky_lines" and "num_deceptive_lines" columns
    :return: A dataframe with the line annotation length distribution
    """
    assert "num_risky_lines" in queries.columns
    assert "num_deceptive_lines" in queries.columns

    cols = ["num_risky_lines", "num_deceptive_lines"]
    counts = queries[cols].apply(pd.Series.value_counts).fillna(0)
    counts = counts / queries.shape[0] * 100.0
    return counts
