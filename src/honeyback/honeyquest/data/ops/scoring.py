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

from typing import Iterable, Optional

import pandas as pd


def detection_scores(
    rids: pd.Series | Iterable,
    response_ids: pd.DataFrame,
    responses: pd.DataFrame,
    queries: pd.DataFrame,
) -> pd.Series:
    """
    Computes how well participants detected traps and risks.
    Computes various classification metrics and performing some statistical tests on them.

    This function is best used after a groupby operation
    on a series or iterable of just the response ids,
    which we expect to be unique.

    We compute the following new values:
    - k: The number of unique queries
    - n: The number of responses to all those queries
    - trap_tp: The number of deceptive queries with trap marks on deceptive lines
    - trap_fn: The number of deceptive queries without trap marks on deceptive lines
    - fell_tp: The number of deceptive queries with exploit marks on deceptive lines
    - dcpt_fn_skip: The number of deceptive queries without any marks at all
    - dcpt_fn_rest: The number of deceptive queries with all marks on other lines
    - hack_tp: The number of risky queries with exploit marks on risky lines
    - hack_fn: The number of risky queries without exploit marks on risky lines
    - new_tp: The number of risky queries with trap marks on risky lines
    - risk_fn_skip: The number of risky queries without any marks at all
    - risk_fn_rest: The number of risky queries with all marks on other lines
    - ntrl_fp_mark: The number of neutral queries with exploit AND trap marks
    - ntrl_fp_hack: The number of neutral queries with ONLY exploit marks
    - ntrl_tn_hack: The number of neutral queries without exploit marks
    - ntrl_fp_trap: The number of neutral queries with ONLY trap marks
    - ntrl_tn_trap: The number of neutral queries without trap marks
    - ntrl_tn: The number of neutral queries without any marks

    :param rids: A series or iterable with just the response ids
    :param response_ids: The id frame with the "rid" index
    :param responses: The responses frame with all "ans_*" columns
    :param queries: The queries frame with the "query_label" column
    :return: A series of metrics describing this dataframe as a whole
    """
    rids = pd.Series(rids)
    assert rids.is_unique, "response ids are not unique"

    # select rids and merge in the variants and annotations
    df = response_ids.loc[rids, :]
    df = df.merge(responses, on="rid", how="left", validate="1:1")
    df = df.reset_index().merge(queries, on="qid", how="left", validate="m:1")
    df = df.set_index("rid")
    assert df.index.is_unique, "response ids are not unique after merge"

    df_dcpt = df.query("query_label == 'deceptive'")
    df_risk = df.query("query_label == 'risky'")
    df_ntrl = df.query("query_label == 'neutral'")

    unique_query_labels = df.query_label.unique()

    def _iif_label(value: int, label: str) -> Optional[int]:
        # only return value if the label even exists in this dataframe
        return value if label in unique_query_labels else None

    # number of unique queries
    k = df.qid.nunique()

    # number of responses (total, and per label)
    n = df.shape[0]
    n_label = df.query_label.value_counts()

    # --- deceptive queries ---

    # for queries with multiple deceptive lines, it can happen that the participant marks
    # one of them as exploit and the other as trap. to keep the numbers in the confusion
    # matrix consistent, we count these as 0.5 for each class instead
    num_double_mark_on_dcpt = df_dcpt.query("ans_hack_on_dcpt & ans_trap_on_dcpt").shape[0]

    # `LD ∩ aTr != ∅`
    # number of deceptive queries with trap marks on deceptive lines
    trap_tp: float = df_dcpt.query("ans_trap_on_dcpt").shape[0]
    trap_tp -= 0.5 * num_double_mark_on_dcpt
    trap_tp = int(trap_tp)

    # `LD ∩ aEx != ∅`
    # number of deceptive queries with exploit marks on deceptive lines
    fell_tp: float = df_dcpt.query("ans_hack_on_dcpt").shape[0]
    fell_tp -= 0.5 * num_double_mark_on_dcpt
    fell_tp = int(fell_tp)

    # to avoid floating number counts, even-out odd duplicates with a bias towards trap marks
    if num_double_mark_on_dcpt % 2 != 0:
        fell_tp += 1

    # `aTr = ∅ ∧ aEx = ∅`
    # number of deceptive queries without any marks at all
    dcpt_fn_skip = df_dcpt.query("~ans_any").shape[0]

    # `LD ∩ (aTr ∪ aEx) = ∅ ∧ (aTr ∪ aEx) != ∅`
    # number of deceptive queries with all marks on other (mostly neutral, maybe risky) lines
    dcpt_fn_rest = df_dcpt.query("ans_any & ~ans_any_on_dcpt").shape[0]

    # (extra metric, just for confusion matrix) `LD ∩ aTr = ∅`
    # number of deceptive queries without trap marks on deceptive lines
    trap_fn = df_dcpt.query("~ans_trap_on_dcpt").shape[0]

    if "deceptive" in unique_query_labels:
        cm_dcpt_check = trap_tp + fell_tp + dcpt_fn_skip + dcpt_fn_rest - n_label["deceptive"]
        assert cm_dcpt_check == 0, f"checksum off by {cm_dcpt_check} for deceptive answers"

    # --- risky queries ---

    # for queries with multiple risky lines, it can happen that the participant marks
    # one of them as exploit and the other as trap. to keep the numbers in the confusion
    # matrix consistent, we count these as 0.5 for each class instead
    num_double_mark_on_risk = df_risk.query("ans_hack_on_risk & ans_trap_on_risk").shape[0]

    # `LR ∩ aEx != ∅`
    # number of risky queries with exploit marks on risky lines
    hack_tp: float = df_risk.query("ans_hack_on_risk").shape[0]
    hack_tp -= 0.5 * num_double_mark_on_risk
    hack_tp = int(hack_tp)

    # `LR ∩ aTr != ∅`
    # number of risky queries with trap marks on risky lines
    new_tp: float = df_risk.query("ans_trap_on_risk").shape[0]
    new_tp -= 0.5 * num_double_mark_on_risk
    new_tp = int(new_tp)

    # to avoid floating number counts, even-out odd duplicates with a bias towards trap marks
    if num_double_mark_on_risk % 2 != 0:
        new_tp += 1

    # `aTr = ∅ ∧ aEx = ∅`
    # number of risky queries without any marks at all
    risk_fn_skip = df_risk.query("~ans_any").shape[0]

    # `LR ∩ (aTr ∪ aEx) = ∅ ∧ (aTr ∪ aEx) != ∅`
    # number of risky queries with all marks on other (mostly neutral, maybe deceptive) lines
    risk_fn_rest = df_risk.query("ans_any & ~ans_any_on_risk").shape[0]

    # (extra metric, just for confusion matrix) `LR ∩ aEx = ∅`
    # number of risky queries without exploit marks on risky lines
    hack_fn = df_risk.query("~ans_hack_on_risk").shape[0]

    if "risky" in unique_query_labels:
        cm_risk_check = hack_tp + new_tp + risk_fn_skip + risk_fn_rest - n_label["risky"]
        assert cm_risk_check == 0, f"checksum off by {cm_risk_check} for deceptive answers"

    # --- neutral queries ---

    # `aEx != ∅ ∧ aTr != ∅`
    # number of neutral queries with exploit AND trap marks
    ntrl_fp_mark = df_ntrl.query("ans_any_hack & ans_any_trap").shape[0]

    # `aEx != ∅ ∧ aTr = ∅`
    # number of neutral queries with ONLY exploit marks
    ntrl_fp_hack = df_ntrl.query("ans_any_hack & ~ans_any_trap").shape[0]

    # `aTr != ∅ ∧ aEx = ∅`
    # number of neutral queries with ONLY trap marks
    ntrl_fp_trap = df_ntrl.query("ans_any_trap & ~ans_any_hack").shape[0]

    # `aTr = ∅ ∧ aEx = ∅`
    # number of neutral queries without any marks
    ntrl_tn = df_ntrl.query("~ans_any").shape[0]

    # (extra metric, just for confusion matrix) `aEx = ∅`
    # number of neutral queries without exploit marks
    ntrl_tn_hack = df_ntrl.query("~ans_any_hack").shape[0]

    # (extra metric, just for confusion matrix) `aTr = ∅`
    # number of neutral queries without trap marks
    ntrl_tn_trap = df_ntrl.query("~ans_any_trap").shape[0]

    if "neutral" in unique_query_labels:
        cm_ntrl_check = ntrl_fp_mark + ntrl_fp_hack + ntrl_fp_trap + ntrl_tn - n_label["neutral"]
        assert cm_ntrl_check == 0, f"checksum off by {cm_ntrl_check} for neutral answers"

    return pd.Series(
        {
            "k": k,
            "n": n,
            "trap_tp": _iif_label(trap_tp, "deceptive"),
            "trap_fn": _iif_label(trap_fn, "deceptive"),
            "fell_tp": _iif_label(fell_tp, "deceptive"),
            "dcpt_fn_skip": _iif_label(dcpt_fn_skip, "deceptive"),
            "dcpt_fn_rest": _iif_label(dcpt_fn_rest, "deceptive"),
            "hack_tp": _iif_label(hack_tp, "risky"),
            "hack_fn": _iif_label(hack_fn, "risky"),
            "new_tp": _iif_label(new_tp, "risky"),
            "risk_fn_skip": _iif_label(risk_fn_skip, "risky"),
            "risk_fn_rest": _iif_label(risk_fn_rest, "risky"),
            "ntrl_fp_mark": _iif_label(ntrl_fp_mark, "neutral"),
            "ntrl_fp_hack": _iif_label(ntrl_fp_hack, "neutral"),
            "ntrl_tn_hack": _iif_label(ntrl_tn_hack, "neutral"),
            "ntrl_fp_trap": _iif_label(ntrl_fp_trap, "neutral"),
            "ntrl_tn_trap": _iif_label(ntrl_tn_trap, "neutral"),
            "ntrl_tn": _iif_label(ntrl_tn, "neutral"),
        },
        dtype="Int64",
    )


def before_after_contingency_table(
    qids: pd.Series | Iterable,
    response_ids: pd.DataFrame,
    responses: pd.DataFrame,
    queries: pd.DataFrame,
):
    """
    Computes a contingency table over the following two factors.
    - Whether the risky lines where hacked in the risky query (before)
    - Whether the risky lines where hacked in the deceptive query (after)

    Only participants who answered both query pairs are included.
    Query pairs are then matched per "uid", and based on the
    "original_query" id, iif the "original_risky" column is set.

    This function is best used after a groupby operation
    on a series or iterable of just the query ids,
    which we expect to be unique.

    :param qids: A series or iterable with just the query ids
    :param response_ids: The id frame with the "rid" index
    :param responses: The responses frame with all "ans_*" columns
    :param queries: The queries frame with the "query_label" column
    :return: A 2x2 contingency table with before and after condition counts
    """
    qids = pd.Series(qids)
    assert qids.is_unique, "query ids are not unique"

    # select query ids and merge in the answers and its metadata
    df = response_ids[response_ids.qid.isin(qids)]
    df = df.merge(responses, on="rid", how="left", validate="1:1")
    df = df.reset_index().merge(queries, on="qid", how="left", validate="m:1")
    df = df.set_index("rid")
    assert df.index.is_unique, "response ids are not unique after merge"

    # set the qid to itself wherever it is missing right now
    original_qids = df.loc[df.original_query.isna(), "qid"]
    df.loc[df.original_query.isna(), "original_query"] = original_qids

    def __pair_and_count(grp: pd.DataFrame):
        assert grp.qid.nunique() == grp.shape[0], "query ids are not unique"
        if grp.shape[0] < 2:
            return None  # there must be a matching pair of queries
        assert grp.shape[0] == 2, f"expected exactly two queries per uid, got {grp.shape[0]}"

        # `LR ∩ aEx != ∅` on `q_R` (before) / `q_D` (after)
        before = grp.query("query_label == 'risky' & ans_hack_on_risk").shape[0] > 0
        after = grp.query("query_label == 'deceptive' & ans_hack_on_risk").shape[0] > 0

        return pd.Series({"before": before, "after": after})

    counts = df.groupby(["uid", "original_query"]).apply(__pair_and_count).dropna()
    counts.after = pd.Categorical(counts.after, [False, True])
    counts.before = pd.Categorical(counts.before, [False, True])

    # cross-tabulate the counts that we made categorial before to respect all combinations
    crosstab = pd.crosstab(counts.after, counts.before, dropna=False).unstack()
    return crosstab
