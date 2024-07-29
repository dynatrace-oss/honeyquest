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
from typing import Dict, List

import matplotlib.pyplot as plt
import pandas as pd
from IPython.display import display
from matplotlib import colormaps
from matplotlib.patches import Patch

from ....common.models.query import Query
from ...util import latex, listutil
from ..generation.latex.constants import LABEL_NAMES, TYPE_NAMES


def plot_query_label_distribution_per_bucket(
    path: str,
    queries: Dict[str, Query],
    buckets: Dict[str, List[str]],
    display_df=False,
):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    latex.set_latex_style(figsize=latex.FigureSize.DOUBLEFLATXS2)

    cmap_pastel = colormaps["Pastel1"]
    cmap = (cmap_pastel(2), cmap_pastel(3), cmap_pastel(0)).__getitem__

    # flatten the query index
    query_index = set(listutil.flatten(buckets.values()))

    # grab all queries and filter by the index
    queries_flat = pd.DataFrame(
        [
            dict(label=q.label, type=q.type)
            for q in queries.values()
            if q.type != "tutorial" and q.id in query_index
        ]
    )

    order = ["neutral", "deceptive", "risky"]
    query_groups = queries_flat.groupby(["label", "type"]).size().unstack(fill_value=0)
    query_groups = query_groups.reindex(index=order, fill_value=0)
    query_groups.rename(columns=TYPE_NAMES, index=LABEL_NAMES, inplace=True)

    if display_df:
        display(query_groups)

    counts = query_groups.to_numpy().tolist()
    typs = query_groups.columns.tolist()
    lbls = query_groups.index.tolist()
    ntyps, nlbls = len(typs), len(lbls)

    ax = plt.gca()
    width = 0.2
    for j in range(nlbls):
        bars = [e + j * width for e in range(ntyps)]
        ax.bar(bars, height=counts[j], width=width, color=cmap(j))

    latex.show_barplot_counts()

    plt.ylim(0, 40)

    ax.set_xticks([e + (len(lbls) - 1) * width / 2 for e in range(ntyps)])
    ax.set_xticklabels(typs)

    # plt.xlabel("Query type")
    plt.ylabel("Count")

    patches = [Patch(facecolor=cmap(i), label=label) for i, label in enumerate(lbls)]
    ax.legend(handles=patches, fontsize=14, loc="upper left", ncol=2, fancybox=False)

    # latex.tick_distance("y", 5, "minor")
    latex.tick_distance("y", 10, "major")
    plt.grid(axis="y", which="major")

    plt.tight_layout()
    plt.savefig(path)
    plt.show()
