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

from functools import partial

import pandas as pd

from ..counting import get_paired_query_ids
from ..scoring import before_after_contingency_table
from ..testing import deception_effect, mark_preference


def compute_defensive_distraction_table(
    response_ids: pd.DataFrame,
    responses: pd.DataFrame,
    queries: pd.DataFrame,
) -> pd.DataFrame:
    """
    Computes the table on aspect B2 from the paper.
    Answers whether deceptive elements diverting an attackers interest away from true risks.

    The index will be the `applied_honeywire` and an `all` row.
    The columns will be the values of the contingency table,
    and the test statistics (p-values, power, risk reduction).

    Essentially, we compute the `deception_effect` per honeywire.

    :param response_ids: The id frame with the "rid" index
    :param responses: The responses frame with all "ans_*" columns
    :param queries: The queries frame
    :return: A dataframe with the contingency table and test statistics
    """

    def _apply_before_after_contingency_table(df: pd.DataFrame) -> pd.Series:
        return before_after_contingency_table(df.index, response_ids, responses, queries)

    df = get_paired_query_ids(queries)
    result = df.groupby("applied_honeywire").apply(_apply_before_after_contingency_table)

    # sum over all honeywires
    result.loc["all"] = result.sum(axis=0)

    # perform tests
    test = result.apply(deception_effect, axis=1)
    result = pd.concat([result, test], axis=1)
    result.sort_values("pvalue", inplace=True)

    # make nullable int types
    result[(False, False)] = result[(False, False)].astype("Int64")
    result[(False, True)] = result[(False, True)].astype("Int64")
    result[(True, False)] = result[(True, False)].astype("Int64")
    result[(True, True)] = result[(True, True)].astype("Int64")

    return result


def comnpute_defensive_rank_preference_table(
    response_ids: pd.DataFrame,
    responses: pd.DataFrame,
    queries: pd.DataFrame,
    groupby: str,
) -> pd.DataFrame:
    """
    Computes the table on aspect B1 from the paper.
    Answers whether attackers prefered to mark deceptive elements before true risks.

    The index will be the `groupby` field, which should be
    `applied_honeywire` or the `present_risk` string typically.
    The columns will be the counts and test statistics.

    :param response_ids: The id frame with the "rid" index
    :param responses: The responses frame with all "ans_*" columns
    :param queries: The queries frame
    :param groupby: Either "applied_honeywire" or "present_risk"
    :return: A dataframe with the counts and test statistics
    """
    # identify grouper
    base_type = "deceived" if groupby == "applied_honeywire" else "hacked"
    grouper = partial(mark_preference, base_type=base_type)

    # a table that has the responses along with the applied honeywire
    df = pd.merge(response_ids, responses, on="rid", how="left", validate="1:1")
    df = pd.merge(df, queries, on="qid", how="left", validate="m:1")
    result = df.groupby(groupby).apply(grouper).sort_values("pvalue")

    # merge in the query type
    honeywire_to_query_type = (
        queries.reset_index().loc[:, [groupby, "query_type"]].drop_duplicates().set_index(groupby)
    )
    result = result.merge(honeywire_to_query_type, left_index=True, right_index=True)

    # do one test per query type
    for qtype in queries.query_type.unique():
        result.loc[qtype] = mark_preference(df[df.query_type == qtype], base_type=base_type)

    # do also one test on all responses
    result.loc["all"] = mark_preference(df, base_type=base_type)

    # fixup data types and drop query type again
    result.k = result.k.astype("Int64")
    result.n = result.n.astype("Int64")
    result = result.drop(columns="query_type")

    result = result.sort_values("pvalue")
    return result
