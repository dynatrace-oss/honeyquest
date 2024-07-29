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

from typing import Dict, List, Literal, Optional, Set, Tuple

import pandas as pd

from ...common.las import expand_las, in_las
from ...common.models.query import Query

AnswerVariant = Literal["exact", "subset", "overlap", "none", "other"]


def postprocess_marks(
    marks: pd.DataFrame,
    queries: Dict[str, Query],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Post-processes the marks by pre-computing various metrics.

    Returns two dataframes:
    - the original data frame, with some new mark-specific columns
    - a dataframe indexed by response ids, containing response-specific metrics

    :param marks: A dataframe containing the flattened responses
    :param queries: The queries, indexed by query id
    :return: A dataframe containing the post-processed responses
    """
    marks_df = marks.apply(lambda row: process_mark(row, queries), axis=1)
    marks_df = pd.concat([marks, marks_df], axis=1)

    responses_df = marks.groupby("rid").apply(lambda df: process_response(df, queries))

    return marks_df, responses_df


def process_mark(row: pd.Series, queries: Dict[str, Query]) -> pd.Series:
    """
    This function is best used within an apply operation (axis=1).
    Classifies for one mark if it matched a risky or deceptive line.

    We compute the following new values:
    - mrk_query_type: The type of the query
    - mrk_neutral: `True` if the mark is a neutral mark
    - mrk_hack: `True` if the mark is a hack mark
    - mrk_trap: `True` if the mark is a trap mark
    - mrk_on_dcpt: `True` if the mark matched a deceptive line
    - mrk_on_risk: `True` if the mark matched a risky line
    - mrk_hack_on_risk: `True` if the hack mark matched a risky line
    - mrk_hack_on_dcpt: `True` if the hack mark matched a deceptive line
    - mrk_trap_on_risk: `True` if the trap mark matched a risky line
    - mrk_trap_on_dcpt: `True` if the trap mark matched a deceptive line

    Also, we add the following text column:
    - mrk_line: The text of the line that was marked

    The possible column values are:
    - `True` on matches
    - `False` on non-matches
    - `None` if there are no marks, or there are no (risky or deceptive) lines to match

    :param row: Series with "qid" and "answer_*" columns
    :param queries: A dictionary of queries, keyed by their query id
    :return: A single pandas series with the computed columns
    """
    assert "qid" in row.index
    assert "answer_type" in row.index
    assert "answer_line" in row.index

    # query lines
    query = queries[row.qid]
    risky_lines = query.get_risky_lines()
    deceptive_lines = query.get_deceptive_lines()

    # affected query line
    line_text: Optional[str] = None
    if row.answer_line is not None and row.answer_line >= 0:
        line_text = query.data.splitlines()[row.answer_line - 1]

    # answer lines and validity
    aline: int = row.answer_line
    atype: str = row.answer_type
    avalid = aline and aline != -1

    # neutral marks imply invalid lines
    assert not (atype == "neutral" and avalid)

    line_on_risk = in_las(aline, risky_lines) if avalid else None
    line_on_dcpt = in_las(aline, deceptive_lines) if avalid else None

    return pd.Series(
        {
            "mrk_query_type": query.type,
            "mrk_neutral": atype == "neutral",
            "mrk_hack": atype == "hack",
            "mrk_trap": atype == "trap",
            "mrk_line": line_text,
            "mrk_on_dcpt": line_on_dcpt,
            "mrk_on_risk": line_on_risk,
            "mrk_hack_on_risk": line_on_risk if atype == "hack" else None,
            "mrk_hack_on_dcpt": line_on_dcpt if atype == "hack" else None,
            "mrk_trap_on_risk": line_on_risk if atype == "trap" else None,
            "mrk_trap_on_dcpt": line_on_dcpt if atype == "trap" else None,
        }
    )


def process_response(df: pd.DataFrame, queries: Dict[str, Query]) -> pd.Series:
    """
    This function is best used after a groupby operation.
    It merges all answer markers of a user into a single label,
    respecting the different variants that are possible.
    See the paper for details on the set logic.

    We compute the following new columns:
    - ans_all: True if the user marked every single line
    - ans_all_hack: True if the user marked every single line with a hack mark
    - ans_all_trap: True if the user marked every single line with a trap mark
    - ans_any: True if the user placed at least one hack or trap mark anywhere
    - ans_any_hack: True if the user placed at least one hack mark anywhere
    - ans_any_trap: True if the user placed at least one trap mark anywhere
    - ans_hack_on_risk_var: The variant on how the hack mark intersects with the risky lines
    - ans_hack_on_risk: True on exact-, subset- or overlap-matches, False otherwise
    - ans_hack_on_dcpt_var: The variant on how the hack mark intersects with the deceptive lines
    - ans_hack_on_dcpt: True on exact-, subset- or overlap-matches, False otherwise
    - ans_trap_on_risk_var: The variant on how the trap mark intersects with the risky lines
    - ans_trap_on_risk: True on exact-, subset- or overlap-matches, False otherwise
    - ans_trap_on_dcpt_var: The variant on how the trap mark intersects with the deceptive lines
    - ans_trap_on_dcpt: True on exact-, subset- or overlap-matches, False otherwise
    - ans_any_on_risk: True if the user placed at least one mark on a risky line
    - ans_any_on_dcpt: True if the user placed at least one mark on a deceptive line
    - ans_deceived_ranks: The ranks of the hack marks that deceived the user
    - ans_not_deceived_ranks: The ranks of the hack marks that did not deceive the user
    - ans_deceived_first: True if the first hack mark was a trap
    - ans_hacked_ranks: The ranks of the hack marks that were risks
    - ans_not_hacked_ranks: The ranks of the hack marks that were not risks
    - ans_hacked_first: True if the first hack mark was a risk

    Please note:
    - The `_var` columns are of type AnswerVariant, the others are boolean
    - The `ans_deceived_first` column can be None if there are not enough ranks to determine it

    :param df: Answer rows with "rid", "qid" and "answer_*" columns
    :param queries: A dictionary of queries, keyed by their query id
    :return: A single pandas series with the computed columns
    """
    assert "rid" in df.columns
    assert "qid" in df.columns
    assert "answer_rank" in df.columns
    assert "answer_type" in df.columns
    assert "answer_line" in df.columns
    assert df.rid.nunique() == 1, "group contains multiple response ids"
    assert df.qid.nunique() == 1, "group contains multiple query ids"
    qid = df.qid.iloc[0]

    # put all markers of the user into a set
    hack_lines = set(df.query("answer_type == 'hack'").answer_line.values)
    trap_lines = set(df.query("answer_type == 'trap'").answer_line.values)

    any_hack = len(hack_lines) > 0
    any_trap = len(trap_lines) > 0

    # get risky and deceptive lines of the query
    query = queries[qid]
    payload_length = len(query.data.splitlines())
    risky_lines = expand_las(query.get_risky_lines())
    deceptive_lines = expand_las(query.get_deceptive_lines())

    all_hack = len(hack_lines) == payload_length
    all_trap = len(trap_lines) == payload_length
    all_marks = len(hack_lines | trap_lines) == payload_length

    # deducation to a single label that just indicates if there is any overlap, i.e.,
    # indicating if the user detected at least some of the deceptive or risky lines
    hack_on_risk_var = _get_mark_variant(hack_lines, risky_lines)
    hack_on_risk = hack_on_risk_var in ["exact", "subset", "overlap"]
    hack_on_dcpt_var = _get_mark_variant(hack_lines, deceptive_lines)
    hack_on_dcpt = hack_on_dcpt_var in ["exact", "subset", "overlap"]
    trap_on_risk_var = _get_mark_variant(trap_lines, risky_lines)
    trap_on_risk = trap_on_risk_var in ["exact", "subset", "overlap"]
    trap_on_dcpt_var = _get_mark_variant(trap_lines, deceptive_lines)
    trap_on_dcpt = trap_on_dcpt_var in ["exact", "subset", "overlap"]

    # compute the ranks on hack marks that deceived or not deceived the user
    deceived_ranks, not_deceived_ranks = _get_matching_ranks_for_hack_marks(df, deceptive_lines)
    deceived_first = (
        (deceived_ranks[0] < not_deceived_ranks[0])
        if len(deceived_ranks) > 0 and len(not_deceived_ranks) > 0
        else None
    )

    # compute the ranks on hack marks that were risks or not risks
    hacked_ranks, not_hacked_ranks = _get_matching_ranks_for_hack_marks(df, risky_lines)
    hacked_first = (
        (hacked_ranks[0] < not_hacked_ranks[0])
        if len(hacked_ranks) > 0 and len(not_hacked_ranks) > 0
        else None
    )

    return pd.Series(
        {
            "ans_all": all_marks,
            "ans_all_hack": all_hack,
            "ans_all_trap": all_trap,
            "ans_any": any_hack or any_trap,
            "ans_any_hack": any_hack,
            "ans_any_trap": any_trap,
            "ans_hack_on_risk_var": hack_on_risk_var,
            "ans_hack_on_risk": hack_on_risk,
            "ans_hack_on_dcpt_var": hack_on_dcpt_var,
            "ans_hack_on_dcpt": hack_on_dcpt,
            "ans_trap_on_risk_var": trap_on_risk_var,
            "ans_trap_on_risk": trap_on_risk,
            "ans_trap_on_dcpt_var": trap_on_dcpt_var,
            "ans_trap_on_dcpt": trap_on_dcpt,
            "ans_any_on_risk": hack_on_risk or trap_on_risk,
            "ans_any_on_dcpt": hack_on_dcpt or trap_on_dcpt,
            "ans_deceived_ranks": tuple(deceived_ranks),
            "ans_not_deceived_ranks": tuple(not_deceived_ranks),
            "ans_deceived_first": deceived_first,
            "ans_hacked_ranks": tuple(hacked_ranks),
            "ans_not_hacked_ranks": tuple(not_hacked_ranks),
            "ans_hacked_first": hacked_first,
        }
    )


def _get_matching_ranks_for_hack_marks(
    df: pd.DataFrame, other_lines: Set[int]
) -> Tuple[List[int], List[int]]:
    """
    Looking only at hack marks, computes the ranks on whether the user was deceived or not.

    For example, we can use this to get the "fallen-for-trap ranks", i.e.,
    when there a three hack marks, where the first is placed on a trap,
    and the others on (arbitrary) other lines, the result would be `([1], [2, 3])`.

    Alternatively, we can use this to get the "hacked-risk ranks", i.e.,
    when there a three hack marks, where the second is placed on a risky line,
    and the others on (arbitrary) other lines, the result would be `([2], [1, 3])`.

    :param df: A frame with at least the "answer_*" columns
    :param other_lines: The "other" lines of the associated query,
        which are probably the deceptive (for a fallen-for-trap rank)
        or risky lines (for a hacked-risk rank)
    """
    hack_mrk_ranks, not_hack_mrk_ranks = [], []
    df = df.query("answer_type == 'hack'").sort_values("answer_rank")
    for rnk, (_, row) in enumerate(df.iterrows(), 1):
        if row.answer_line in other_lines:
            hack_mrk_ranks.append(rnk)
        else:
            not_hack_mrk_ranks.append(rnk)

    return hack_mrk_ranks, not_hack_mrk_ranks


def _get_mark_variant(user_lines: Set[int], true_lines: Set[int]) -> AnswerVariant:
    """
    Computes the respective variant of a mark, i.e., how the mark intersects with the true lines.
    See the paper for details on the set logic.

    :param answer_lines: The lines that were marked by the user
    :param true_lines: The true lines of the query
    :rtype: AnswerVariant
    """
    # the following cases must be mutually exclusive and exhaustive, thus,
    # we check all cases and assert that only one is true
    variant: Optional[AnswerVariant] = None

    # A1. `a = L`
    # exact match: marked lines exactly (`{} == {}` is also exact)
    if user_lines == true_lines:
        variant = "exact"

    # A2. `a != ∅ ∧ a ⊂ L`
    # strict subset:  marked only some true lines (and no non-true lines)
    if user_lines < true_lines and user_lines:
        assert variant is None, "set logic is not mutually exclusive (on subset)"
        variant = "subset"

    # A3. `a !⊆ L ∧ L ∩ a != ∅`
    # strict overlap: marked some true lines (but also non-true lines)
    if user_lines.intersection(true_lines) and not user_lines.issubset(true_lines):
        assert variant is None, "set logic is not mutually exclusive (on overlap)"
        variant = "overlap"

    # A4. `a != ∅ ∧ L ∩ a = ∅`
    # no overlap: marked only non-true lines
    if not user_lines.intersection(true_lines) and user_lines:
        assert variant is None, "set logic is not mutually exclusive (on none)"
        variant = "none"

    # A5. `a = ∅`
    # nothing: marked nothing (but there would be true lines)
    if not user_lines and true_lines:
        assert variant is None, "set logic is not mutually exclusive (on other)"
        variant = "other"

    assert variant is not None, "set logic is not exhaustive"
    return variant
