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

from pathlib import Path
from typing import Dict, Optional, cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from IPython.display import display

from ...types import HoneyquestResults
from ...util import latex
from ..counting import get_query_counts


def plot_number_of_queries_answered(
    path: str,
    results: Dict[str, HoneyquestResults],
    display_df=False,
):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    latex.set_latex_style(figsize=latex.FigureSize.SUPERFLATXS2)

    counts_dict = get_query_counts(results)
    counts = np.array(list(counts_dict.values()))

    if display_df:
        series = pd.Series(counts).describe().astype("Float64").astype("Int64")
        display(series.to_frame("num_answers"))

    rng = np.random.default_rng(0)
    xs = counts.astype(float) + rng.random(len(counts)) * 1.0 - 0.5  # jitter
    xs = np.clip(xs, 0, counts.max())
    ys = rng.random(len(xs)) * 0.5 + 0.75  # jitter

    plt.scatter(xs, ys, c="k", s=50, zorder=1, alpha=0.33)
    plt.boxplot(
        counts.astype(float),
        vert=False,
        widths=0.5,
        showfliers=False,
        zorder=10,
        **latex.BOXPLOT_KWARGS
    )

    plt.xlim(0, 180)

    latex.tick_distance("x", 5, "minor")
    latex.tick_distance("x", 20, "major")
    plt.grid(axis="y", which="major")
    plt.grid(axis="y", which="minor")

    ax = plt.gca()
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["top"].set_visible(False)
    if ax.axes is not None:
        ax.axes.yaxis.set_visible(False)

    # plt.xlabel("Number of answered queries per participant")

    plt.axvline(counts.max(), c="r", ls="-", lw=1, zorder=0)

    plt.tight_layout()
    plt.savefig(path)
    plt.show()


def plot_query_response_time(
    path: str,
    marks: pd.DataFrame,
    display_df=False,
):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    latex.set_latex_style(figsize=latex.FigureSize.SUPERFLATXS2)

    # make sure to de-duplicate the data to responses first
    counts = marks.groupby("rid").response_time.first()

    if display_df:
        display(pd.Series(counts).describe().astype(int).to_frame())

    plt.boxplot(
        counts.astype(float),
        vert=False,
        widths=0.5,
        showfliers=False,
        zorder=1,
        **latex.BOXPLOT_KWARGS
    )

    latex.tick_distance("x", 5, "minor")
    latex.tick_distance("x", 10, "major")
    plt.grid(axis="y", which="major")
    plt.grid(axis="y", which="minor")

    ax = plt.gca()
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["top"].set_visible(False)
    if ax.axes is not None:
        ax.axes.yaxis.set_visible(False)

    # plt.xlabel("Query response time in seconds")

    plt.tight_layout()
    plt.savefig(path)
    plt.show()


def plot_query_rating(
    query_rating: pd.DataFrame,
    path: Optional[str] = None,
    show: bool = True,
    cleanup: bool = True,
):
    """
    Generate a heatmap of the query rating.
    The query rating can be generated from `counting.get_query_rating` function.

    :param query_rating: The query rating dataframe
    :param path: The path to save the plot to if it should be, defaults to None
    :param show: Shall the plot be displayed, defaults to True
    :param cleanup: Shall the figure be freed afterwards, defaults to True
    """
    if path is not None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    rc_params = {
        "figure.autolayout": True,
        "font.family": "monospace",
        "ytick.right": True,
        "ytick.labelright": True,
        "ytick.left": False,
        "ytick.labelleft": False,
    }

    plot_df = query_rating[["text", "hack", "trap"]].set_index("text")
    plot_df.rename(columns={"hack": "# Hack", "trap": "# Trap"}, inplace=True)

    sns.reset_defaults()
    fig = plt.figure()
    with plt.rc_context(rc_params):
        cmap = sns.light_palette("black", as_cmap=True)
        sns.heatmap(plot_df, annot=True, cmap=cmap, cbar=False, square=True)

    ax = plt.gca()

    ax.set_yticks(np.arange(0.5, len(plot_df.index)))
    ax.set_yticklabels(plot_df.index)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
    ax.tick_params(axis="both", which="both", length=0)
    ax.set_ylabel("")

    # base figure height on the number of lines
    cast(plt.Figure, ax.figure).set_figheight(0.31 * len(query_rating))

    for i in query_rating[query_rating.deceptive].index:
        ax.yaxis.get_ticklabels()[i - 1].set_backgroundcolor("#ffdead")  # type: ignore
    for i in query_rating[query_rating.risky].index:
        ax.yaxis.get_ticklabels()[i - 1].set_backgroundcolor("#ffe1ff")  # type: ignore

    if path is not None:
        plt.savefig(path, dpi=fig.dpi, bbox_inches="tight", pad_inches=0)

    if show:
        plt.show()

    if cleanup:
        fig.clear()
        plt.close(fig)

    return fig
