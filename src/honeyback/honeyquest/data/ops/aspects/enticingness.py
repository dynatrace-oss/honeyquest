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
from typing import Tuple

import pandas as pd

from ...types import ConfusionMatrix
from ..generation.latex.constants import LABEL_NAMES_ABBRV, TYPE_NAMES_ABBRV
from ..reporting import apply_multi_level, compute_honeywire_and_risk_identifier
from ..scoring import detection_scores
from ..testing import binomial_proportion_intervals


def compute_enticingness_table(
    response_ids: pd.DataFrame,
    responses: pd.DataFrame,
    queries: pd.DataFrame,
) -> pd.DataFrame:
    """
    Computes the large tables on aspect A from the paper, for neutral, deceptive, and risky queries.
    Aspect A is about measureing the enticingness of each honeywire and risk.

    The index will contain multiple aggregation levels:
    - "all" for the total counts and scores
    - "neutral" for the totals of only the neutral queries
    - "deceptive" for the totals of only the deceptive queries
    - "risky" for the totals of only the risky queries

    Then, for each query type, label, and concrete honeywire or risk, there will be yet another row:
    - e.g., "filesystem" for the totals of query types "filesystem"
    - e.g., "filesystem/deceptive" for the totals of type "filesystem" and label "deceptive"
    - e.g., "filesystem/deceptive/filesystem-keys" for the scores of the honeywire "filesystem-keys"

    The columns will contain the aggregated counts of all the detection scores,
    as computed by `detection_scores`, and the test statistics (p-values, power, risk reduction).

    Also, the rank-based `identifier` that is used in the paper will be added as a column.

    :param response_ids: The id frame with the "rid" index
    :param responses: The responses frame with all "ans_*" columns
    :param queries: The queries frame
    :return: The resulting table on aspect A
    """
    # merge in the queries already because we need them for the multi-level aggregation
    # and reset-and-set the index again because the merge would drop it otherwise
    df = response_ids.reset_index().merge(queries, on="qid", validate="m:1")
    df = df.set_index("rid")
    assert df.index.is_unique

    def _apply_detection_scores(df: pd.DataFrame) -> pd.Series:
        return detection_scores(df.index, response_ids, responses, queries)

    # compute the detection scores per hierarchy level
    df = apply_multi_level(df, _apply_detection_scores)

    # fix types
    df.k = df.k.astype(int)
    df.n = df.n.astype(int)

    # compute the rank-based identifier
    df = compute_honeywire_and_risk_identifier(
        df,
        score_dcpt_fn=lambda row: row.fell_tp / row.n,
        score_risk_fn=lambda row: row.hack_tp / row.n,
        label_names=LABEL_NAMES_ABBRV,
        type_names=TYPE_NAMES_ABBRV,
    )

    # concat confidence intervals for all confusion-matrix-based scores
    for col in df.columns:
        if "tp" in col or "tn" in col or "fp" in col or "fn" in col:
            apply_fn = partial(binomial_proportion_intervals, kcol=col, alpha=0.05, method="wilson")
            df[f"{col}_cse"] = df.apply(apply_fn, axis=1).cse

    return df


def compute_enticingness_confusion_matrix(
    enticingness_df: pd.DataFrame,
) -> Tuple[ConfusionMatrix, ConfusionMatrix]:
    """
    Derived from the enticingness table, computes the confusion matrix for detection scores.
    This is done once for deceptive and once for risky queries.
    The opposing type are always the neutral queries.

    :param enticingness_df: The enticingness dataframe
    :return: A tuple of the confusion matrices for deceptive and risky queries
    """
    cols_trap = ["ntrl_tn_trap", "ntrl_fp_trap", "trap_fn", "trap_tp"]
    cols_hack = ["ntrl_tn_hack", "ntrl_fp_hack", "hack_fn", "hack_tp"]

    cm_trap = ConfusionMatrix(*enticingness_df.loc["all"].loc[cols_trap].to_list())
    cm_hack = ConfusionMatrix(*enticingness_df.loc["all"].loc[cols_hack].to_list())

    return cm_trap, cm_hack
