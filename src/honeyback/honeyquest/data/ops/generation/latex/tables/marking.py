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
from typing import List

import pandas as pd
from pylatex import escape_latex

from ..constants import TYPE_NAMES_ABBRV
from ..variables import query_id_to_latex
from .postprocess import process_and_store_latex

EXTRA_LINES_AFTER_A4 = {
    "texttt": ["\\hdashline"],
}


def generate_mark_ranking_latex_table(
    path: str,
    aspect4_lines: pd.DataFrame,
    id_dcpt: pd.DataFrame,
    id_risk: pd.DataFrame,
    sort_by: List[str],
    limit: int,
):
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    cols = [
        "mrk_query_type",
        "mrk_on_dcpt",
        "mrk_on_risk",
        "mrk_hack",
        "mrk_trap",
        "applied_honeywire",
        "present_risk",
    ]

    df = aspect4_lines.loc[:, cols].copy()
    df = df.merge(
        id_dcpt.add_suffix("_dcpt"),
        left_on="applied_honeywire",
        right_index=True,
        how="left",
        validate="m:1",
    )
    df = df.merge(
        id_risk.add_suffix("_risk"),
        left_on="present_risk",
        right_index=True,
        how="left",
        validate="m:1",
    )

    # imply the icons and identifiers
    icons, identifiers = zip(
        *df.apply(
            lambda r: (
                ("\\riski", r.identifier_risk)
                if r.mrk_on_risk > 0
                else ("\\dcpti", r.identifier_dcpt) if r.mrk_on_dcpt > 0 else ("", "")
            ),
            axis=1,
        ).tolist()
    )

    df.insert(0, "icon", icons)
    df.insert(1, "identifier", identifiers)

    def __map_to_hyperlink(r):
        if r.mrk_on_risk > 0 and r.present_risk:
            return query_id_to_latex(r.present_risk, prefix="Risk")
        elif r.mrk_on_dcpt > 0 and r.applied_honeywire:
            return query_id_to_latex(r.applied_honeywire, prefix="Dcpt")
        else:
            return ""

    # rows that have neither, get an empty string
    df["identifier"] = df.apply(
        lambda r: (
            f"\\footnotesize \\RowRefSingle{{Results}}{{{__map_to_hyperlink(r)}}}"
            if r.identifier
            else ""
        ),
        axis=1,
    )

    # abbreviate the query type
    df["mrk_query_type"] = df["mrk_query_type"].map(TYPE_NAMES_ABBRV)
    df["mrk_query_type"] = df["mrk_query_type"].map(lambda x: f"\\texttt{{{x}}}" if x else "")

    df.drop(
        columns=[
            "mrk_on_dcpt",
            "mrk_on_risk",
            "identifier_risk",
            "identifier_dcpt",
            "applied_honeywire",
            "present_risk",
        ],
        inplace=True,
    )

    # escape latex chars, explicitly encode spaces,
    # and add a hyphen for slashes and dots
    df.index = df.index.map(
        lambda e: "\\raggedright\\arraybackslash\\texttt{{{}}}".format(
            escape_latex(str(e).lstrip())
            .replace("  ", "~~")
            .replace(" ", " {\\allowbreak}")
            .replace("/", "/{\\allowbreak}")
            .replace(".", ".{\\allowbreak}")
            .replace("-", "-{\\allowbreak}")
        )
    )

    # move icon column to the front
    df.reset_index(inplace=True)
    col_front = ["icon", "identifier", "mrk_query_type"]
    df = df[col_front + [col for col in df.columns if col not in col_front]]

    df = df.sort_values(by=sort_by, ascending=[False, True])
    df = df.iloc[:limit, :]

    process_and_store_latex(path, df, extra_after=EXTRA_LINES_AFTER_A4, hide_index=True)
