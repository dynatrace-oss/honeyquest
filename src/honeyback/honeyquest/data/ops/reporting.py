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

from typing import Callable, Dict, List, Optional, cast

import pandas as pd

from ...common.models.query import Query
from ..util.listutil import flatten


def apply_multi_level(
    df: pd.DataFrame,
    apply_fn: Callable[[pd.DataFrame], pd.Series],
) -> pd.DataFrame:
    """
    Applies the given function at multiple hierarchy levels of the full dataframe.
    The "lvl" column indicates the hierarchy level.

    :param df: The original dataframe
    :param apply_fn: The function to apply to groups
    :return: The dataframe with the results
    """
    # 0th hierarchy: entire dataframe
    df_all = apply_fn(df)
    results = pd.DataFrame(columns=["lvl"] + df_all.index.to_list())
    results.loc["all"] = df_all

    results.lvl = results.lvl.astype(str)
    results.loc["all", "lvl"] = "0"

    # 1st hierarchy: query type
    for qtype in sorted(df.query_type.unique()):
        df_type = df.query("query_type == @qtype")
        results.loc[qtype] = apply_fn(df_type)
        results.loc[qtype, "lvl"] = "1T"
        results.loc[qtype, "query_type"] = qtype

        # 2nd hierarchy: query label
        for qlabel in ["neutral", "deceptive", "risky"]:
            df_label = df_type.query("query_label == @qlabel")
            results.loc[f"{qtype}/{qlabel}"] = apply_fn(df_label)
            results.loc[f"{qtype}/{qlabel}", "lvl"] = "2"
            results.loc[f"{qtype}/{qlabel}", "query_label"] = qlabel
            results.loc[f"{qtype}/{qlabel}", "query_type"] = qtype

            # 3rd hierarchy: honeywires
            if qlabel == "deceptive":
                df_dcpt = df_label.groupby("applied_honeywire", as_index=True, group_keys=False)
                if (rows := df_dcpt.apply(apply_fn)).size > 0:
                    rows["applied_honeywire"] = rows.index

                    # pylint: disable=cell-var-from-loop
                    rows.index = rows.index.map(lambda x: f"{qtype}/deceptive/{x}")

                    results = pd.concat([results, rows])
                    results.loc[rows.index, "lvl"] = "3D"
                    results.loc[rows.index, "query_label"] = "deceptive"
                    results.loc[rows.index, "query_type"] = qtype

            # 3rd hierarchy: risks
            elif qlabel == "risky":
                df_risk = df_label.groupby("present_risk", as_index=True, group_keys=False)
                if (rows := df_risk.apply(apply_fn)).size > 0:
                    rows["present_risk"] = rows.index

                    # pylint: disable=cell-var-from-loop
                    rows.index = rows.index.map(lambda x: f"{qtype}/risky/{x}")

                    results = pd.concat([results, rows])
                    results.loc[rows.index, "lvl"] = "3R"
                    results.loc[rows.index, "query_label"] = "risky"
                    results.loc[rows.index, "query_type"] = qtype

    # 1st sibling hierarchy: query label (without query type)
    for qlabel in ["neutral", "deceptive", "risky"]:
        df_label_global = df.query("query_label == @qlabel")
        results.loc[qlabel] = apply_fn(df_label_global)
        results.loc[qlabel, "lvl"] = "1L"
        results.loc[qlabel, "query_label"] = qlabel

    assert results.index.is_unique
    return results


def compute_honeywire_and_risk_identifier(
    df: pd.DataFrame,
    score_dcpt_fn: Callable[[pd.Series], pd.Series],
    score_risk_fn: Callable[[pd.Series], pd.Series],
    label_names: Dict[str, str],
    type_names: Dict[str, str],
) -> pd.DataFrame:
    """
    Grabs the rank-based ID for each row in the hierarchical data frame.
    This is done by sorting the hierarchical data frame with the full results table
    and assigning a rank-based ID to each row, grouped by the query type.

    :param df: The "aspect1" results data frame
    :param score_dcpt_fn: The function to compute the deceptive score
    :param score_risk_fn: The function to compute the risky score
    :param label_names: A mapping from query label names to their abbreviation
    :param type_names: A mapping from query type names to their abbreviation
    :return: The same data frame, but with a new "identifier" column
    """
    # compute the metric by which we sort the results table accordingly
    df["score_dcpt"] = df.apply(score_dcpt_fn, axis=1)
    df["score_risk"] = df.apply(score_risk_fn, axis=1)

    def __compute_rank(dfs: pd.DataFrame, col: str) -> pd.Series:
        ranks = dfs.groupby("query_type").apply(
            lambda dfs: list(
                zip(
                    # the indexes within this group, sorted by the score
                    dfs.sort_values(col, ascending=False).index,
                    # the rank, i.e., a running index starting at 1
                    range(1, len(dfs) + 1),
                )
            )
        )

        ranks_list = flatten(ranks.to_list())
        index, values = zip(*ranks_list)
        return pd.Series(values, index=index)

    # compute and set the ranks column
    r = __compute_rank(df.query("lvl == '3R'"), "score_risk")
    d = __compute_rank(df.query("lvl == '3D'"), "score_dcpt")

    df["identifier"] = pd.concat([r, d])
    df["identifier"] = df.identifier.fillna(-1).astype(int).astype(str).replace("-1", "")

    def __compute_id(row: pd.Series) -> str:
        if not row.identifier:
            return ""
        return label_names[row.query_label] + type_names[row.query_type] + row.identifier

    # prepend query label and type abbreviation
    df["identifier"] = df.apply(__compute_id, axis=1)
    df = df.drop(columns=["score_dcpt", "score_risk"])

    return df


def grab_citation_keys(
    query_id: str,
    queries: Dict[str, Query],
    mapping_doi: Optional[Dict[str, str]] = None,
    mapping_url: Optional[Dict[str, str]] = None,
) -> List[str]:
    """
    Helper function to grab the citation key for a query.
    Returns either an empty list or a list with one or more citation keys.

    :param query_id: The query ID
    :param queries: The queries, indexed by ID
    :param mapping_doi: A mapping of `technique/doi` keys to citation keys, if available
    :param mapping_url: A mapping of `technique/url` keys to citation keys, if available
    :return: The citation keys to use in LaTeX
    """

    def __get_refs_list_with_mapping(
        source_key: str, mapping: Optional[Dict[str, str]] = None
    ) -> List[str]:
        refs = queries[query_id].get_reference(source_key, complete=True)
        refs_list = cast(List[str], refs)  # for mypy
        if not refs_list:
            return []

        if mapping is None:
            return refs_list
        return [mapping[ref] for ref in refs_list]

    refs_by_doi = __get_refs_list_with_mapping("technique/doi", mapping_doi)
    refs_by_url = __get_refs_list_with_mapping("technique/url", mapping_url)

    return refs_by_doi + refs_by_url


def get_number_of_honeywires_with_citation_keys(
    honeywires: List[str],
    queries_df: pd.DataFrame,
    queries_dict: Dict[str, Query],
) -> int:
    """
    Helper function to compute the number of honeywires that have at least one citation key.

    :param honeywires: A list of honeywire names to consider
    :param queries_df: Queries frame with "applied_honeywire" column
    :param queries_dict: Queries dictionary, indexed by ID
    :return: The number of honeywires with at least one citation key
    """
    num_cited_honeywires = 0
    for honeywire in honeywires:
        qs = queries_df.query(f"applied_honeywire == '{honeywire}'").index
        if qs.size == 0:
            continue

        # grab and union all keys
        cite_keys = [grab_citation_keys(str(q), queries_dict) for q in qs]
        if sum(map(len, cite_keys)) > 0:
            num_cited_honeywires += 1

    return num_cited_honeywires
