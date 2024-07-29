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

import re
from typing import Dict, List, Optional

import pandas as pd

EMPTY_CHARACTER = "\\textminus"


def process_and_store_latex(
    path: str,
    df: pd.DataFrame,
    extra_before: Optional[Dict[str, List[str]]] = None,
    extra_after: Optional[Dict[str, List[str]]] = None,
    before_linespace: float = 0.0,
    round_digits: int = 4,
    bold_first_line: bool = False,
    hide_index: bool = False,
    multicolumn_hack: bool = False,
    skipfirst_extra_before: bool = False,
    multicolumn_width: int = 2,
    makebox_hack: bool = False,
):
    """
    Utility function to process a DataFrame and store it as a LaTeX table.
    Includes various hacky fixes to make it look nice in the paper.
    """
    extra_after = extra_after or {}
    extra_before = extra_before or {}

    def __replace_nan_values(text: str, replacement: Optional[str] = None) -> str:
        """Replace all NaN values with a replacement character."""
        replacement = replacement or EMPTY_CHARACTER.replace("\\", "\\\\")
        text = re.sub(r"nan", replacement, text)  # noqa: keep this line with re.sub
        text = re.sub(r"<NA>", replacement, text)  # noqa: keep this line with re.sub

        return text

    def __round_decimal_values(text: str, old_digits: int = 2, new_digits: int = 3) -> str:
        """Round all digits with at least `old_digits` digits to `digits` digits."""
        pattern = rf"(\d\.\d{{{old_digits},}})"

        def __formatter(m):
            return f"{{:.{new_digits}f}}".format(float(m.group(1)))

        text = re.sub(pattern, __formatter, text)

        # possibly add a smaller sign if we rounded to zero
        all_zero = "0." + "0" * new_digits
        all_zero_one = "0." + "0" * (new_digits - 1) + "1"
        text = text.replace(all_zero, f"\\textless~{all_zero_one}")

        return text

    def __insert_extra_lines(text: str, skipfirst_before: bool = False) -> str:
        """Insert extra vertical alignment or other metdata lines before or after certain lines."""
        source, target, first = text.splitlines(), [], True

        for line in source:
            for pattern, extra in extra_before.items():
                if re.search(pattern, line):
                    if not (skipfirst_before and first):
                        target.extend(extra)
                    else:
                        first = False

            target.append(line)

            for pattern, extra in extra_after.items():
                if re.search(pattern, line):
                    target.extend(extra)

        return "\n".join(target)

    def __multicolumn_title_hack(text: str, num: int) -> str:
        """Make a multicolumn wherever the ID is missing."""
        result = []

        for line in text.splitlines():
            rem = "\\s*&" * (num - 1)
            line = re.sub(
                rf"^ & (.*?){rem}",
                rf"\\multicolumn{{{num}}}{{l}}{{\1}} &",
                line,
            )
            line = re.sub(
                rf"^\\bfseries \\footnotesize \\textminus & (.*?){rem}",
                rf"\\multicolumn{{{num}}}{{l}}{{\1}} &",
                line,
            )

            result.append(line)

        return "\n".join(result)

    def __bold_first_line(df: pd.DataFrame) -> pd.DataFrame:
        """Bold the first line of the table."""
        df = df.copy().astype(str)
        df.iloc[0] = df.iloc[0].apply(lambda x: f"\\bfseries {x}" if x else "")

        return df

    def __add_before_linespace(text: str, linespace: float = 0.0) -> str:
        """Add a linespace before the first line of the table."""
        if linespace <= 0:
            return text
        prefix = f"\\addlinespace[{linespace}cm]\n"
        return prefix + text

    def __scrape_begin_end(text: str) -> str:
        """Hacky scrapping of extra content before and after the table."""
        source = text.splitlines()
        target, skipnext = [], False

        for i, line in enumerate(source):
            if line.startswith("\\begin{tabular}"):
                skipnext = True
                continue
            if line.startswith("\\rhypertarget{row:Design:DcptFilesystem"):
                skipnext = True
                continue
            if line.startswith("\\rhypertarget{row:Design:RiskFilesystem"):
                skipnext = True
                continue

            if i == len(source) - 2 and line.startswith("\\hdashline"):
                continue
            if line.startswith("\\end{tabular}"):
                continue

            if skipnext:
                skipnext = False
                continue

            target.append(line)

        return "\n".join(target)

    if bold_first_line:
        df = __bold_first_line(df)
        df = df.rename(index={df.index[0]: f"\\bfseries {df.index[0]}"})

    if makebox_hack:
        # let the "card3rz_reg.." column overflow by enclosing it in a makebox
        idx = df.index[df["index"].str.contains("card3rz")].tolist()[0]
        df.loc[idx, "index"] = f"\\makebox[0pt][l]{{{df.loc[idx, 'index']}}}"

        # let the "customer_list..." column overflow by enclosing it in a makebox
        idx = df.index[df["index"].str.contains("customer")].tolist()[0]
        df.loc[idx, "index"] = f"\\makebox[0pt][l]{{{df.loc[idx, 'index']}}}"

    style = df.style if not hide_index else df.style.hide(axis="index")
    text = style.to_latex()

    text = __round_decimal_values(text, new_digits=round_digits)
    text = __replace_nan_values(text)
    text = __insert_extra_lines(text, skipfirst_before=skipfirst_extra_before)
    text = __add_before_linespace(text, linespace=before_linespace)
    text = __scrape_begin_end(text)

    if multicolumn_hack:
        text = __multicolumn_title_hack(text, multicolumn_width)

    with open(path, "w") as f:
        f.write(text)
        f.write("\n")


def make_percentage_column(
    series: pd.Series,
    bold: bool = False,
    plus_sign: bool = False,
) -> pd.Series:
    pre = "\\bfseries" if bold else ""
    fmt = "{}{:+.0f}\\%" if plus_sign else "{} {:.0f}\\%"
    return series.apply(lambda x: fmt.format(pre, x * 100) if not pd.isna(x) else EMPTY_CHARACTER)
