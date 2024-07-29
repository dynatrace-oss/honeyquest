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

import enum
from typing import Dict, TypedDict

import matplotlib.axes
import matplotlib.dates
import matplotlib.font_manager
import matplotlib.pyplot as plt
import matplotlib.ticker
from cycler import Cycler, cycler
from pandas.plotting import register_matplotlib_converters

# explicitly register datetime converters
register_matplotlib_converters()

FOREGROUND_COLOR = "#424242"
BACKGROUND_COLOR = "#6d6d6d"

# a rectangle for .tight_layout(rect=), that does not cut off the title
TIGHT_LAYOUT_RECT = [0, 0.03, 1, 0.95]


class BoxplotArgs(TypedDict):
    """Keyword arguments for boxplots."""

    boxprops: Dict[str, str]


BOXPLOT_KWARGS: BoxplotArgs = {
    "boxprops": {
        "facecolor": "None",
    },
}

ANNOTATE_KWARGS = {
    "fontsize": 15,
    "color": FOREGROUND_COLOR,
    "arrowprops": {
        "color": "#6d6d6d",
        "arrowstyle": "-",
        "connectionstyle": "arc3,rad=-0.1",
        "linestyle": ":",
    },
}


class FigureSize(enum.Enum):
    """Enumeration of common figure sizes."""

    HORIZONTAL = (16, 8)
    FLAT = (16, 4)
    SUPERFLAT = (16, 2.5)
    DOUBLEFLAT = (16, 6)
    VERTICAL = (8, 16)
    SQUARE = (16, 16)
    HORIZONTALX2 = (32, 16)
    FLATX2 = (32, 8)
    SUPERFLATX2 = (32, 5)
    DOUBLEFLATX2 = (32, 12)
    VERTICALX2 = (16, 32)
    SQUAREX2 = (32, 32)
    HORIZONTALXS2 = (8, 4)
    FLATXS2 = (8, 2)
    SUPERFLATXS2 = (8, 1.5)
    DOUBLEFLATXS2 = (8, 3)
    VERTICALXS2 = (4, 8)
    SQUAREXS2 = (8, 8)
    HORIZONTALXS4 = (4, 2)
    FLATXS4 = (4, 1)
    SUPERFLATXS4 = (4, 0.625)
    DOUBLEFLATXS4 = (4, 1.5)
    VERTICALXS4 = (2, 4)
    SQUAREXS4 = (4, 4)


def set_latex_style(latex: bool = True, figsize: FigureSize = FigureSize.HORIZONTAL):
    """
    Sets the plot parameters for your LaTeX documents.

    :param latex: use the LaTeX font faces
    :param figsize: default figure size
    """
    plt.rcParams["figure.figsize"] = figsize.value if isinstance(figsize, FigureSize) else figsize

    plt.rcParams["axes.labelpad"] = 20
    plt.rcParams["axes.axisbelow"] = True
    plt.rcParams["axes.titlesize"] = 18
    plt.rcParams["axes.titlepad"] = 15
    plt.rcParams["axes.prop_cycle"] = Cycler.concat(
        cycler(color=[FOREGROUND_COLOR]),
        plt.rcParams["axes.prop_cycle"],
    )

    plt.rcParams["text.usetex"] = latex
    plt.rcParams["font.family"] = "serif" if latex else "sans-serif"
    plt.rcParams["font.serif"] = "Palatino"
    plt.rcParams["font.size"] = 20

    plt.rcParams["xtick.labelsize"] = 15
    plt.rcParams["ytick.labelsize"] = 15

    plt.rcParams["grid.color"] = BACKGROUND_COLOR
    plt.rcParams["grid.linestyle"] = ":"

    plt.rcParams["boxplot.meanline"] = True
    plt.rcParams["boxplot.showmeans"] = True
    plt.rcParams["boxplot.showfliers"] = False
    plt.rcParams["boxplot.patchartist"] = True

    plt.rcParams["savefig.bbox"] = "tight"
    plt.rcParams["savefig.pad_inches"] = 0.0


def thousands_separator(axis: str):
    """
    Set a tick formatter that uses thousand separators on an axis.

    :param axis: Either 'x', 'y' or 'both'
    """
    formatter = matplotlib.ticker.FuncFormatter(lambda x, _: format(int(x), ","))
    for ax in _axis_selector(axis):
        ax.set_major_formatter(formatter)


def format_numeric_labels(fmt: str, axis: str):
    """
    Set a tick formatter with a custom format string on an axis.

    :param fmt: The format string, e.g. "{:.2f}"
    :param axis: Either 'x', 'y' or 'both'
    """
    formatter = matplotlib.ticker.FuncFormatter(lambda x, _: fmt.format(x))
    for ax in _axis_selector(axis):
        ax.set_major_formatter(formatter)


def tick_distance(axis: str, base: float, which: str = "major"):
    """
    Set the tick distance on an axis.

    :param axis: Either 'x', 'y' or 'both'
    :param base: The distance between ticks
    :param which: Either 'major' or 'minor'
    """
    assert which in ("minor", "major")

    ticker = matplotlib.ticker.MultipleLocator(base=base)
    for ax in _axis_selector(axis):
        if which == "major":
            ax.set_major_locator(ticker)
        elif which == "minor":
            ax.set_minor_locator(ticker)


def show_barplot_counts(
    orientation: str = "v",
    extend: bool = False,
    show_zero: bool = False,
):
    """
    Draw labels next to the barplots, showing the count.

    :param orientation: Either 'h' or 'v'
    :param extend: Extend the axis to make room for the labels
    :param show_zero: Show the label for zero values
    """
    assert orientation == "v", "only vertical orientation is supported"

    ax = plt.gca()

    rectangles = [p for p in ax.patches if isinstance(p, matplotlib.patches.Rectangle)]

    # get the maximum height of the bars and possibly extend the axis
    max_height = max(p.get_height() for p in rectangles)
    height_offset = max_height * 0.05
    if extend:
        plt.ylim(top=max_height * 1.2)

    # add text patch for each bar
    for i in rectangles:
        h = int(i.get_height())
        if not show_zero and h == 0:
            continue

        width_offset = i.get_width() / 2
        digit_offset_heur = (len(str(h)) * 0.06) / 2

        x = i.get_x() + width_offset - digit_offset_heur
        y = h + height_offset

        text = f"{h:,d}"
        ax.text(x, y, text, fontsize=15, color="dimgrey")


def _axis_selector(axis: str):
    assert axis in ("x", "y", "both")

    gca = plt.gca()
    if axis in ("x", "both"):
        yield gca.get_xaxis()
    if axis in ("y", "both"):
        yield gca.get_yaxis()
