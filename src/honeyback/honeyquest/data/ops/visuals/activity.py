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

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from ...util import latex


def plot_user_activity(
    marks: pd.DataFrame,
    hue: Optional[str] = "uid",
    path: Optional[str] = None,
    show: bool = True,
    cleanup: bool = True,
):
    """
    Generates a histogram of the user activity, i.e., the number of queries answered by each user.

    :param marks: The marks dataframe
    :param hue: The column to use for coloring, defaults to "uid"
    :param path: The path to save the plot to if it should be, defaults to None
    :param show: Shall the plot be displayed, defaults to True
    :param cleanup: Shall the figure be freed afterwards, defaults to True
    """
    sns.reset_defaults()
    latex.set_latex_style(latex=False, figsize=latex.FigureSize.FLAT)

    fig = plt.figure()
    sns.histplot(
        data=marks,
        x=marks.answer_time.apply(lambda x: x.timestamp()),
        hue=hue,
        multiple="stack",
        cumulative=True,
        stat="count",
        legend=False,
        bins=100,
    )

    ax = plt.gca()
    ax.set_xlabel("Time")
    ax.set_ylabel("Marks")

    formatter = plt.FuncFormatter(lambda x, _: pd.to_datetime(x, unit="s").strftime("%h %d"))
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.set_major_locator(plt.MaxNLocator(10))
    plt.xticks(rotation=45)

    if path is not None:
        plt.savefig(path, dpi=fig.dpi, bbox_inches="tight", pad_inches=0)

    if show:
        plt.show()

    if cleanup:
        fig.clear()
        plt.close(fig)

    plt.show()
