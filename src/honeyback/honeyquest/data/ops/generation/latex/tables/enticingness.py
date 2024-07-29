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
from typing import Dict

import numpy as np
import pandas as pd
from pylatex import escape_latex

from ......common.models.query import Query
from .....util.listutil import map_rounded_numbers_to_probability_distribution
from ....reporting import grab_citation_keys
from ..constants import (
    CITE_MAP_DOI,
    CITE_MAP_URL,
    GROUPER_NAMES,
    HONEYWIRE_NAMES,
    PRESENT_RISK,
    TYPE_NAMES,
)
from ..variables import query_id_to_latex
from .postprocess import (
    EMPTY_CHARACTER,
    make_percentage_column,
    process_and_store_latex,
)

EXTRA_LINES_BEFORE = {
    "All": ["\\addlinespace[0.05cm]"],
    "^[^&]+& \\\\bfseries(?! All)": [
        "\\midrule",
        "\\addlinespace[0.1cm]",
    ],
}

EXTRA_LINES_AFTER = {
    "^\\s&\\s\\\\bfseries(?! All)": ["\\addlinespace[0.05cm]"],
}

EXTRA_LINES_AFTER_A2_AND_NEUTRAL = {
    "\\\\bfseries All": ["\\addlinespace[0.05cm]"],
}


EXTRA_LINES_AFTER_DECEPTIVE = {
    TYPE_NAMES["filesystem"]: [
        "\\addlinespace[0.05cm]",
    ],
    TYPE_NAMES["htaccess"]: [
        "\\addlinespace[0.05cm]",
    ],
    TYPE_NAMES["httpheaders"]: [
        "\\addlinespace[0.05cm]",
    ],
    TYPE_NAMES["networkrequests"]: [
        "\\addlinespace[0.05cm]",
    ],
}


def generate_enticingness_latex_table(
    path: str,
    queries_dict: Dict[str, Query],
    queries_df: pd.DataFrame,
    aspect1: pd.DataFrame,
    aspect2: pd.DataFrame,
    aspect3: pd.DataFrame,
    label: str,
    min_test_samples: int,
):
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    def __collect_citation_keys(honeywire: str) -> str:
        qs = queries_df.query(f"applied_honeywire == '{honeywire}'").index
        if qs.size == 0:
            return ""

        # grab and union all keys
        all_keys = [grab_citation_keys(q, queries_dict, CITE_MAP_DOI, CITE_MAP_URL) for q in qs]
        all_keys = set.union(*(set(k) for k in all_keys))
        all_keys = ",".join(sorted(all_keys))

        return f"\\cite{{{all_keys}}}" if all_keys else ""

    label_specific_fields = {
        "deceptive": ["fell_tp", "trap_tp", "dcpt_fn_rest", "dcpt_fn_skip"],
        "risky": ["hack_tp", "new_tp", "risk_fn_rest", "risk_fn_skip"],
        "neutral": ["ntrl_fp_hack", "ntrl_fp_trap", "ntrl_fp_mark", "ntrl_tn"],
    }

    label_specific_cse = {
        "deceptive": ["fell_tp_cse", "trap_tp_cse"],
        "risky": ["hack_tp_cse", "new_tp_cse"],
        "neutral": ["ntrl_fp_hack_cse", "ntrl_fp_trap_cse"],
    }

    # sub-select only the specified label
    df = aspect1.query("query_label == @label").copy()

    # make the honeywire or risk the index
    df.reset_index(inplace=True)
    if label == "deceptive":
        df.loc[df.lvl == "3D", "index"] = df.loc[df.lvl == "3D", :].applied_honeywire
    elif label == "risky":
        df.loc[df.lvl == "3R", "index"] = df.loc[df.lvl == "3R", :].present_risk
    df.set_index("index", inplace=True)

    assert df.index.is_unique

    # move the label row to the top and sort each group
    sort_by = "fell_tp" if label == "deceptive" else "hack_tp"
    new_index = [label]

    for k in df.query_type.unique():
        if pd.isna(k):
            continue

        group_label = f"{k}/{label}"

        # add the sorted sub-groups (but without the group label)
        sorted_group = df.query(f"query_type == '{k}'").copy()
        sorted_group["_sort_by"] = sorted_group.apply(lambda row: row[sort_by] / row.n, axis=1)
        sorted_group = sorted_group.sort_values("_sort_by", ascending=False)

        # if there is only the group header, skip it
        # unless this is the neutral label
        if label != "neutral" and sorted_group.shape[0] <= 1:
            continue

        sorted_index = sorted_group.index.to_list()
        sorted_index.remove(group_label)

        new_index.append(group_label)
        new_index.extend(sorted_index)

    df = df.reindex(new_index)

    # subselect only what we need
    cols = ["identifier", "k", "n"] + label_specific_fields[label] + label_specific_cse[label]
    df = df.loc[:, cols]

    # compute percentages
    for field in label_specific_fields[label]:
        ratio = make_percentage_column(df[field] / df.n, bold=False)
        df.insert(df.columns.get_loc(field) + 1, field + "%", ratio)

    def _make_detectionbar_column(row: pd.Series):
        vals = [(row[lbl] / row.n) * 100 for lbl in label_specific_fields[label]]
        vals = map_rounded_numbers_to_probability_distribution(vals, nplaces=0)
        vals_opt = [row[lbl] for lbl in label_specific_cse[label]]
        args = "".join([f"{{{val}}}" for val in vals])
        args_opt = "".join([f"[{val}]" for val in vals_opt])
        return f"\\detectionbar{args}{args_opt}"

    # add the detection score bar
    detectbars = df.apply(_make_detectionbar_column, axis=1)
    df.insert(len(df.columns), "detectbar", detectbars)

    df = df.add_prefix("a1.")

    # possibly merge in extra columns
    if label == "deceptive":
        df = df.merge(
            aspect3.loc[:, ["k", "n", "pvalue", "power"]]
            .copy()
            .rename(index={k: f"{k}/deceptive" for k in TYPE_NAMES.keys()} | {"all": "deceptive"})
            .add_prefix("a3."),
            left_index=True,
            right_index=True,
            how="left",
            validate="1:1",
        )

        # [aspect 2] we only need to know if it exists
        df = df.merge(
            aspect2.loc[:, ["pvalue"]].copy().add_prefix("a2."),
            left_index=True,
            right_index=True,
            how="left",
            validate="1:1",
        )

        # [aspect 2] add a hack mark when the aspect exists
        a2_exists = df["a2.pvalue"].apply(lambda x: "\\riski" if not pd.isna(x) else "")
        df.insert(0, "a2.exists", a2_exists)
        df.loc[label, "a2.exists"] = ""
        df.drop(columns=["a2.pvalue"], inplace=True)

        # [aspect 3] only show the test if we have more than "n" samples
        n = min_test_samples
        df["a3.pvalue"] = df.apply(lambda r: r["a3.pvalue"] if r["a3.n"] >= n else np.nan, axis=1)
        df["a3.power"] = df.apply(lambda r: r["a3.power"] if r["a3.n"] >= n else np.nan, axis=1)

        # [aspect 3] compute k over n ratio
        kn_ratio = make_percentage_column(df["a3.k"] / df["a3.n"], bold=False)
        df.insert(df.columns.get_loc("a3.n") + 1, "a3.kn%", kn_ratio)
        # only show the ratio if we have more than "n" samples
        df["a3.kn%"] = df.apply(lambda r: r["a3.kn%"] if r["a3.n"] >= n else np.nan, axis=1)

        # [aspect 3] add backslash character to n column
        df["a3.k"] = df["a3.k"].apply(lambda x: f"{x}~/" if not pd.isna(x) else EMPTY_CHARACTER)

        # insert empty literature references column as the first column
        refs = df.index.map(__collect_citation_keys) if label == "deceptive" else ""
        df.insert(0, "ref", refs)

        # insert an empty column between aspects as padding
        df.insert(df.columns.get_loc("a3.k"), "e1", "")

    labeldict = {"neutral": "Ntrl", "deceptive": "Dcpt", "risky": "Risk"}

    def _build_row_link_prefix(label: str, mode: str):
        return f"row:{mode}:{labeldict[label]}"

    def _get_index_row_command(name: str):
        prefix = f"Row{label.capitalize()}"
        name = query_id_to_latex(name, prefix=prefix)
        return f"\\{name}{{}}"

    def _get_index_row_link(name: str, prefix: str, nolink: bool = False):
        target = query_id_to_latex(name, prefix=prefix)
        other = query_id_to_latex(name, prefix=labeldict[label])
        grp = "Results" if "Design" in prefix else "Design"

        # filesystem queries can not be linked explicitly
        if nolink or "Filesystem" in other:
            return f"\\rhypertarget{{{target}}}\\scriptsize\\VarId{other}"
        else:
            return f"\\rhypertarget{{{target}}}\\scriptsize\\RowRefSingle{{{grp}}}{{{other}}}"

    # copy the index to a new column
    df["altindex"] = df.index

    # rename index to honeywire, risk, and grouper names
    df.rename(
        index=HONEYWIRE_NAMES | PRESENT_RISK | TYPE_NAMES | GROUPER_NAMES,
        inplace=True,
    )

    # prefix grouper names with bold font
    # unless this is the neutral table
    if label == "neutral":
        df.index = df.index.map(
            lambda x: (
                f"\\bfseries {x}"
                if x in GROUPER_NAMES.values() and x not in TYPE_NAMES.values()
                else x
            )
        )
    else:
        df.index = df.index.map(lambda x: f"\\bfseries {x}" if x in TYPE_NAMES.values() else x)
        df.index = df.index.map(lambda x: f"\\bfseries {x}" if x in GROUPER_NAMES.values() else x)

    rowlinkpre = _build_row_link_prefix(label, "Results")
    df["rowlink"] = df["altindex"].apply(lambda n: _get_index_row_link(n, rowlinkpre, nolink=True))
    df["rowlink"] = df.apply(lambda r: "" if not r["a1.identifier"] else r["rowlink"], axis=1)
    df["linked_identifier"] = df["rowlink"]

    if label == "deceptive":
        # append the ref column text to the index AFTER the naming step
        df.index = df.index + "~" + df.ref
        df.index = df.index.str.rstrip("~")

    if label == "risky":
        # for the risky column, replac the index directly by the commandix
        # since we don't have a representative description there due to space constraints
        df.index = df.apply(
            lambda row: (
                _get_index_row_command(row.altindex) if "bfseries" not in row.name else row.name
            ),
            axis=1,
        )

    # move identifier column to the front
    df.reset_index(inplace=True)
    df = df[["linked_identifier"] + [col for col in df.columns if col != "linked_identifier"]]

    df.columns = df.columns.map(escape_latex)

    extra_before = EXTRA_LINES_BEFORE if label != "neutral" else None
    extra_after_dict = {
        "neutral": EXTRA_LINES_AFTER_A2_AND_NEUTRAL,
        "deceptive": EXTRA_LINES_AFTER_DECEPTIVE,
        "risky": EXTRA_LINES_AFTER,
    }

    dropcols = ["a1.identifier", "altindex", "rowlink"]
    if label == "neutral":
        dropcols.append("linked_identifier")

    # store table with full results
    # process_and_store_latex(
    #     path,
    #     df.drop(columns=map(escape_latex, dropcols)),
    #     extra_before,
    #     extra_after_dict[label],
    #     hide_index=True,
    #     multicolumn_hack=label != "neutral",
    #     makebox_hack=label == "deceptive",
    # )

    # store description-only table with just the names
    # and transform the altindex to a command
    df["commandidx"] = df["altindex"].apply(_get_index_row_command)

    # store a overview-only table with a subset of the columns
    overview_ntrl_cols = [
        "index",
        "a1.k",
        "a1.n",
        # "a1.ntrl_fp_mark%",
        # "a1.ntrl_fp_hack%",
        # "a1.ntrl_fp_trap%",
        # "a1.ntrl_tn%",
        "a1.detectbar",
    ]

    overview_dcpt_cols = [
        "linked_identifier",
        "index",
        "a2.exists",
        "commandidx",
        "a1.k",
        "a1.n",
        # "a1.fell_tp%",
        # "a1.trap_tp%",
        # "a1.dcpt_fn_skip%",
        # "a1.dcpt_fn_rest%",
        "a1.detectbar",
        "e1",
        "a3.n",
        "a3.kn%",
    ]

    overview_risky_cols = [
        "linked_identifier",
        "index",
        # "commandidx",
        "a1.n",
        # "a1.hack_tp%",
        # "a1.new_tp%",
        # "a1.risk_fn_skip%",
        # "a1.risk_fn_rest%",
        "a1.detectbar",
    ]

    overview_cols_dict = {
        "neutral": list(map(escape_latex, overview_ntrl_cols)),
        "deceptive": list(map(escape_latex, overview_dcpt_cols)),
        "risky": list(map(escape_latex, overview_risky_cols)),
    }

    # bold the first column
    if label != "neutral":
        bold_overview_col = escape_latex("a1.fell_tp%" if label == "deceptive" else "a1.hack_tp%")
        df[bold_overview_col] = df[bold_overview_col].map(lambda x: f"\\bfseries {x}")

    process_and_store_latex(
        path.replace(".tex", "-overview.tex"),
        df[overview_cols_dict[label]],
        extra_before,
        extra_after_dict[label],
        hide_index=True,
        multicolumn_hack=label != "neutral",
        makebox_hack=label == "deceptive",
    )

    # neutral label does not need more tables
    if label == "neutral":
        return

    # get the risk names that are of type attack
    # and just put a mark when its an attack
    if label == "risky":
        attacks = set(queries_df[["present_risk", "present_attack"]].dropna().present_risk)
        attack_exists = df.altindex.apply(lambda x: "\\attack" if x in attacks else "")
        df.insert(1, "is_attack", attack_exists)

    rowlinkpre = _build_row_link_prefix(label, "Design")
    df["rowlink"] = df["altindex"].apply(lambda n: _get_index_row_link(n, rowlinkpre))
    df["rowlink"] = df.apply(lambda r: "" if not r["a1.identifier"] else r["rowlink"], axis=1)

    # select a few columns for the light-weight table
    # desc_cols = ["rowlink", "index", "commandidx"]
    # if label == "risky":
    #     desc_cols = ["rowlink", "index", "is_attack", "commandidx"]
    # df_desc = df.loc[1:, desc_cols] if label != "neutral" else df.loc[:, desc_cols]
    # desc_multicol_width = 3 if label == "risky" else 2

    # process_and_store_latex(
    #     path.replace(".tex", "-descriptions.tex"),
    #     df_desc,
    #     EXTRA_LINES_BEFORE,
    #     EXTRA_LINES_AFTER,
    #     before_linespace=0.1,
    #     skipfirst_extra_before=True,
    #     hide_index=True,
    #     multicolumn_hack=True,
    #     multicolumn_width=desc_multicol_width,
    # )
