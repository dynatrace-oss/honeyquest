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

from typing import Literal

import numpy as np
import pandas as pd
from scipy.stats import binomtest

from ..util.metrics import div
from ..util.rbridge import binom_power


def deception_effect(row: pd.Series) -> pd.Series:
    """
    Computes test statistics and results for a single row.
    The result is a full before / after contingency table.

    This function is best used within an apply operation (axis=1).

    :param row: A row with a binary before / after multi-index
    :return: Various test statistics and results for this row
    """
    assert row.size == 4, "expected a flattened 2x2 contingency table row with 4 cells"

    # index is (before, after)
    a = int(row[(False, False)])
    b = int(row[(False, True)])
    c = int(row[(True, False)])
    d = int(row[(True, True)])

    # check the rule of thumb that the rounded expected cell values are larger than 5
    tab = np.array([[a, b], [c, d]], dtype=int)
    exp = np.outer(tab.sum(axis=1), tab.sum(axis=0)) / tab.sum().sum()
    rule_of_thumb_5 = np.all(np.floor(exp) >= 5)

    # one-sided binomial test
    n = b + c
    pvalue = binomtest(c, n, p=0.5, alternative="greater").pvalue if n > 0 else np.nan
    power = binom_power(p_alt=div(c, n), n=n, alternative="two.sided") if n > 0 else np.nan

    # relative risk
    rr = (b + d) / (c + d) if (c + d) > 0 else np.nan
    rr_percent = round(((b + d) / (c + d) - 1) * 100, 2) if (c + d) > 0 else np.nan

    return pd.Series(
        {
            # p-value of the binomial test for the after condition
            "pvalue": pvalue,
            # power of the binomial test on the c / (b+c) proportion, i.e. where `1 - power`
            # is the probability of rejecting the null while it is false (type II error)
            "power": power,
            # relative risk of hacking a risky line in the after condition
            "rr": rr if rr > 0 else None,
            # by what percentage does the risk of hacing a risky line change?
            "rr%": rr_percent if rr > 0 else None,
            # does the rule of thumb for the test hold?
            "rof5": rule_of_thumb_5,
            "exp": exp.round(1).ravel().tolist(),
        }
    )


def mark_preference(df: pd.DataFrame, base_type: str) -> pd.Series:
    """
    Computes if participants prefer to mark deceptive / risky lines over non-deceptive / non-risky.
    Metric is only computed when participants are shown both types of lines.

    :param df: A frame with at least the columns "ans_deceived_first" / "ans_hacked_first"
    :param base_type: Either "deceived" or "hacked", depending on what property to test
    :return: Various test statistics and results for this dataframe
    """
    ans_first_col = f"ans_{base_type}_first"
    assert base_type in ("deceived", "hacked")
    assert ans_first_col in df.columns

    counts = df[ans_first_col].dropna().value_counts()
    k, n = counts.to_dict().get(True, 0), counts.sum()

    # one-sided binomial test
    pvalue = binomtest(k, n, p=0.5, alternative="greater").pvalue if n > 0 else np.nan
    power = binom_power(p_alt=div(k, n), n=n, alternative="two.sided") if n > 0 else np.nan

    return pd.Series(
        {
            # the number of times a deceptive line was marked first
            "k": k,
            # the total number of times when deceptive and non-deceptive lines were marked
            "n": n,
            # p-value of the binomial test on the k / n proportion
            "pvalue": pvalue,
            # power of the binomial test on the k / n proportion, i.e. where `1 - power`
            # is the probability of rejecting the null while it is false (type II error)
            "power": power,
        }
    )


def binomial_proportion_intervals(
    row: pd.Series,
    kcol: str = "k",
    ncol: str = "n",
    alpha: float = 0.05,
    method: Literal["exact", "wilson"] = "exact",
) -> pd.Series:
    """
    Computes the confidence interval of the proportion of successes in a Binomial test.

    This function is best used within an apply operation (axis=1).

    :param row: A row with the the `kcol` for `ncol` columns
    :param kcol: The column name for the number of successes
    :param ncol: The column name for the number of trials
    :param alpha: The confidence interval, defaults to 0.05
    :param method: The method to compute the interval, defaults to "exact"
    :return: The lower and upper bounds and the scaled standard error (interval width / 2)
    """
    if not isinstance(row[kcol], int) or not isinstance(row[ncol], int):
        return pd.Series({"lo": None, "hi": None, "cse": None}, dtype="Int64")

    ci = binomtest(row[kcol], row[ncol]).proportion_ci(confidence_level=1 - alpha, method=method)
    cse = (ci.high - ci.low) / 2  # scaled standard error

    return pd.Series(
        {
            "lo": ci.low,
            "hi": ci.high,
            "cse": cse,
        },
        dtype="Float64",
    )
