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

from colorsys import rgb_to_yiq, yiq_to_rgb
from itertools import product
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython.display import display
from matplotlib import colormaps
from matplotlib.patches import Patch

from ...util import latex
from ..generation.latex.constants import EXPERIMENT_NAMES, JOB_NAMES, RANK_NAMES


def plot_job_roles(
    path: str,
    profiles: pd.DataFrame,
    display_df: bool = False,
):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    latex.set_latex_style(figsize=latex.FigureSize.DOUBLEFLATXS2)

    cmap = colormaps["Pastel1"]

    order = ["biz", "dev", "research", "student", "ops", "secops", "other"]
    job_summary = profiles.groupby(["job", "eid"]).size().unstack(fill_value=0)
    job_summary = job_summary.reindex(index=order, fill_value=0)
    job_summary.rename(columns=EXPERIMENT_NAMES, index=JOB_NAMES, inplace=True)

    if display_df:
        display(job_summary)

    counts = job_summary.values.tolist()
    exps = job_summary.columns.tolist()
    jobs = job_summary.index.tolist()
    nexps, njobs = len(exps), len(jobs)

    ax = plt.gca()
    width, gap = 0.2, 0.5
    for j in range(njobs):
        bars = [e + gap * e + j * width for e in range(nexps)]
        ax.bar(bars, height=counts[j], width=width, color=cmap(j))

    latex.show_barplot_counts()

    plt.ylim(0, 25)

    ax.set_xticks([e + gap * e + (len(jobs) - 1) * width / 2 for e in range(nexps)])
    ax.set_xticklabels(exps)

    # plt.xlabel("Participant Group")
    plt.ylabel("Count")

    patches = [Patch(facecolor=cmap(i), label=label) for i, label in enumerate(jobs)]
    ax.legend(handles=patches, fontsize=13, loc="upper left", ncol=2, fancybox=False)

    latex.tick_distance("y", 1, "minor")
    latex.tick_distance("y", 5, "major")
    plt.grid(axis="y", which="major")

    plt.tight_layout()
    plt.savefig(path)
    plt.show()


def plot_skill_levels(
    path: str,
    profiles: pd.DataFrame,
    display_df: bool = False,
):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    latex.set_latex_style(figsize=latex.FigureSize.DOUBLEFLATXS2)

    cmap = colormaps["Pastel1"]
    order = ["none", "little", "good", "advanced", "expert"]

    rank_summary = profiles.groupby(["rank", "eid"]).size().unstack(fill_value=0)
    rank_summary = rank_summary.reindex(index=order, fill_value=0)
    rank_summary.rename(columns=EXPERIMENT_NAMES, index=RANK_NAMES, inplace=True)

    if display_df:
        display(rank_summary)

    counts = rank_summary.values.tolist()
    exps = rank_summary.columns.tolist()
    rnks = rank_summary.index.tolist()
    nexps, nrnks = len(exps), len(rnks)

    ax = plt.gca()
    width, gap = 0.2, 0.2
    for j in range(nrnks):
        bars = [e + gap * e + j * width for e in range(nexps)]
        ax.bar(bars, height=counts[j], width=width, color=cmap(j))

    latex.show_barplot_counts()

    plt.ylim(0, 25)

    ax.set_xticks([e + gap * e + (len(rnks) - 1) * width / 2 for e in range(nexps)])
    ax.set_xticklabels(exps)

    # plt.xlabel("Participant Group")
    plt.ylabel("Count")

    patches = [Patch(facecolor=cmap(i), label=label) for i, label in enumerate(rnks)]
    ax.legend(handles=patches, fontsize=13, loc="upper left", ncol=3, fancybox=False)

    latex.tick_distance("y", 1, "minor")
    latex.tick_distance("y", 5, "major")
    plt.grid(axis="y", which="major")

    plt.tight_layout()
    plt.savefig(path)
    plt.show()


def plot_years_of_experience(
    path: str,
    profiles: pd.DataFrame,
):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    latex.set_latex_style(figsize=latex.FigureSize.DOUBLEFLATXS2)
    rng = np.random.default_rng(0)

    years = profiles.groupby("eid").years.apply(np.array).to_dict()
    # example: {'ctf1': array([2, 0, 0]), 'ex1': array([10, 0, 1, 3])}

    experiment_names = []
    for i, (experiment, values) in enumerate(years.items(), start=1):
        exp_name = EXPERIMENT_NAMES[experiment].removeprefix("Security ")  # make shorter
        experiment_names.append(exp_name)
        xs = values.astype(float) + rng.random(len(values)) * 0.25 - 0.125  # jitter
        xs = np.clip(xs, 0, values.max())
        ys = rng.random(len(xs)) * 0.5 + 0.75 + (i - 1)  # jitter

        plt.scatter(xs, ys, c="k", s=50, zorder=1, alpha=0.33)
        plt.boxplot(
            values.astype(float),
            positions=[i],
            vert=False,
            widths=0.5,
            showfliers=False,
            zorder=10,
            **latex.BOXPLOT_KWARGS,
        )

    latex.tick_distance("x", 2, "major")
    plt.grid(axis="x", which="major")

    plt.gca().spines["right"].set_visible(False)
    plt.gca().spines["left"].set_visible(False)
    plt.gca().spines["top"].set_visible(False)

    ax = plt.gca()
    ax.set_yticklabels(experiment_names)
    plt.xlabel("Years of professional experience")

    plt.tight_layout()
    plt.savefig(path)
    plt.show()


def plot_favorite_colors(
    path: str,
    profiles: pd.DataFrame,
):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    latex.set_latex_style(figsize=latex.FigureSize.SQUAREXS4)

    def _yiq_color_space(y0=0.5, n=20):
        df = list(product(np.linspace(-1, 1, n), np.linspace(-1, 1, n)))
        df = pd.DataFrame(df, columns=["i", "q"])
        df["color"] = df.apply(lambda r: yiq_to_rgb(y0, r.i, r.q), axis=1)
        return df

    def _profile_color_space():
        def __hex_to_rgb(hexcode):
            hexcode = hexcode.lstrip("#")
            assert len(hexcode) == 6, "hex code must be 6 characters long"
            return tuple(int(hexcode[i : i + 2], 16) for i in range(0, 6, 2))

        df = profiles.loc[:, ["color"]].copy()
        df["r"], df["g"], df["b"] = zip(*df.color.apply(__hex_to_rgb))
        df["r"], df["g"], df["b"] = df.r / 255, df.g / 255, df.b / 255
        df["y"], df["i"], df["q"] = zip(*df.apply(lambda r: rgb_to_yiq(r.r, r.g, r.b), axis=1))
        return df

    # plot colors on a 2D plane
    cs_yiq = _yiq_color_space()
    cs_prf = _profile_color_space()

    ax = plt.gca()
    ax.scatter(cs_yiq.i, cs_yiq.q, s=5, marker="D", c=cs_yiq.color, alpha=0.5)
    ax.scatter(cs_prf.i, cs_prf.q, s=500, marker="o", c=cs_prf.color, zorder=1, edgecolors="w")
    ax.set_xlim(-0.66, 0.66)
    ax.set_ylim(-0.66, 0.66)
    ax.set_axis_off()

    plt.tight_layout()
    plt.savefig(path)
    plt.show()
