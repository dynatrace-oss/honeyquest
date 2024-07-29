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

# pylint: disable-all
# mypy: ignore-errors

from pathlib import Path

import pandas as pd
from pylatex import escape_latex

from ..constants import HONEYWIRE_NAMES
from ..variables import query_id_to_latex
from .enticingness import EXTRA_LINES_AFTER_A2_AND_NEUTRAL
from .postprocess import make_percentage_column, process_and_store_latex


def generate_defensive_distraction_latex_table(
    path: str,
    aspect2: pd.DataFrame,
    id_dcpt: pd.DataFrame,
):
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    cols = [
        (False, False),
        (False, True),
        (True, False),
        (True, True),
        "pvalue",
        "power",
        "rr%",
        "rof5",
    ]

    df = aspect2.loc[:, cols].copy()
    df = df.merge(id_dcpt, left_index=True, right_index=True, how="left")

    df.rename(columns={"rof5": "rof"}, inplace=True)

    df["rr%"] = make_percentage_column(df["rr%"] / 100, plus_sign=True)

    # strike-out test values if rof is violated
    df["pvalue"] = df.apply(
        lambda r: r.pvalue if r.rof or pd.isna(r.pvalue) else f"\\st{{{r.pvalue}}}",
        axis=1,
    )
    df["power"] = df.apply(
        lambda r: r.power if r.rof or pd.isna(r.power) else f"\\st{{{r.power}}}",
        axis=1,
    )

    # take the index column and wrap it in RowRefSingle command
    df["identifier"] = df.index.map(
        lambda x: (
            f"\\scriptsize \\RowRefSingle{{Results}}{{{query_id_to_latex(x, prefix='Dcpt')}}}"
            if x != "all"
            else ""
        )
    )

    df.drop(columns="rof", inplace=True)
    df.rename(
        index=HONEYWIRE_NAMES
        | {
            # special fixes just for this table
            "httpheaders-devtoken": "Dev. Token",
            "networkrequests-sessid-parameter": "SESSID Param.",
        },
        inplace=True,
    )
    df.columns = df.columns.map(escape_latex)

    # move identifier column to the front
    df.reset_index(inplace=True)
    df = df[["identifier"] + [col for col in df.columns if col != "identifier"]]

    process_and_store_latex(
        path,
        df,
        extra_after=EXTRA_LINES_AFTER_A2_AND_NEUTRAL,
        bold_first_line=True,
        hide_index=True,
        multicolumn_hack=True,
    )
