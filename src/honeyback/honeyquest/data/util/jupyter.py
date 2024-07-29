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

from typing import Optional

import ipywidgets as widgets
import pandas as pd
from IPython.display import clear_output, display


def display_sortable_df(
    df: pd.DataFrame,
    by: Optional[str] = None,
    ascending: bool = False,
    max_rows: int = 20,
):
    """
    Displays a DataFrame but with dropdown buttons to order the content by different column names.

    :param df: The dataframe to display
    :param by: The column to sort by initially, defaults to None
    :param ascending: Whether to sort ascending initially, defaults to False
    :param max_rows: Limits the number of rows to show after sorting, defaults to 20
    """
    assert by is None or by in df.columns, f"column {by} not in dataframe"
    by = by if by is not None else str(df.columns[0])
    sort_order = "asc" if ascending else "desc"

    select_col = widgets.Dropdown(options=df.columns, value=by, description="sort by")
    select_ord = widgets.Dropdown(options=["asc", "desc"], value=sort_order, description="order")

    def __display_on_change(change):
        if change["type"] != "change" or change["name"] != "value":
            return

        # we use this hacky re-render because an ipywidget Output
        # would not respect the color theme of the notebooks
        clear_output()
        display(select_col)
        display(select_ord)

        asc = select_ord.value == "asc"
        with pd.option_context("display.max_rows", max_rows):
            display(df.sort_values(select_col.value, ascending=asc).head(n=max_rows))

    select_col.observe(__display_on_change)
    select_ord.observe(__display_on_change)

    # trigger initial display
    __display_on_change({"type": "change", "name": "value"})
