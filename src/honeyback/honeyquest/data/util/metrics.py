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

import math
from math import sqrt
from typing import TypedDict

from scipy.stats import binomtest

from ..types import ConfusionMatrix


class ClassificationMetrics(TypedDict):
    """A dictionary type for classification metrics."""

    acc: float  # accuracy
    ppv: float  # precision, positive predictive value (PPV)
    tpr: float  # recall, sensitivity, true positive rate (TPR)
    fpr: float  # fall-out, false positive rate (FPR)
    f1: float  # f1 score
    mcc: float  # matthews correlation coefficient

    acc_cse: float  # confidence interval for accuracy
    ppv_cse: float  # confidence interval for precision
    tpr_cse: float  # confidence interval for recall
    fpr_cse: float  # confidence interval for fall-out


def classification_metrics(cm: ConfusionMatrix) -> ClassificationMetrics:
    """
    Computes binary classification metrics from confusion matrix.
    Illustration where y are the true label and x the predicted labels:

    ```
    |       | y = F | y = T |
    |-------|-------|-------|
    | x = F |    TN |    FP |
    | x = T |    FN |    TP |
    ```

    :param cm: A `ConfusionMatrix` object to keep the four values.
    :return: A `ClassificationMetrics` object with the computed metrics.
    """
    tn, fp, fn, tp = cm.tn, cm.fp, cm.fn, cm.tp

    acc = div(tp + tn, tp + tn + fp + fn)
    ppv = div(tp, tp + fp)
    tpr = div(tp, tp + fn)
    fpr = div(fp, fp + tn)
    f1 = 2 * div(ppv * tpr, ppv + tpr)
    mcc = div(tp * tn - fp * fn, sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)))

    # confidence intervals
    acc_cse = cse(tp + tn, tp + tn + fp + fn)
    ppv_cse = cse(tp, tp + fp)
    tpr_cse = cse(tp, tp + fn)
    fpr_cse = cse(fp, fp + tn)

    return ClassificationMetrics(
        acc=acc,
        ppv=ppv,
        tpr=tpr,
        fpr=fpr,
        f1=f1,
        mcc=mcc,
        acc_cse=acc_cse,
        ppv_cse=ppv_cse,
        tpr_cse=tpr_cse,
        fpr_cse=fpr_cse,
    )


def div(a: float, b: float) -> float:
    if a == 0 and b == 0:
        return float("nan")
    if b == 0:
        return float("inf")
    return a / b


def cse(k: int, n: int) -> float:
    if math.isnan(k) or math.isnan(n):
        return float("nan")
    if n == 0:
        return float("nan")
    ci = binomtest(k, n).proportion_ci(confidence_level=1 - 0.05, method="wilson")
    return (ci.high - ci.low) / 2
