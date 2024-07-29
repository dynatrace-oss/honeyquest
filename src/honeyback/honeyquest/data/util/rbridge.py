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

from typing import Literal, Optional

try:
    from rpy2.rinterface import NULL
    from rpy2.robjects import conversion, default_converter, pandas2ri
    from rpy2.robjects.packages import importr

    # some of our tests require an R installation,
    # but we don't want to make it a hard dependency
    RPY2_BINOM = importr("binom")
except ImportError:
    RPY2_BINOM = None


def binom_power(
    p_alt: float,
    n: int = 100,
    p: float = 0.5,
    alpha: float = 0.05,
    phi: float = 1,
    alternative: Optional[Literal["two.sided", "greater", "less"]] = None,
    method: Optional[Literal["cloglog", "logit", "probit", "asymp", "lrt", "exact"]] = None,
) -> Optional[float]:
    """Tries calling `binom.power` from R or returns `None` if R is not available."""
    if RPY2_BINOM is None:
        return None

    # ensure native types
    p_alt = float(p_alt)
    n = int(n)
    p = float(p)
    alpha = float(alpha)
    phi = float(phi)
    alternative = alternative if alternative is not None else NULL
    method = method if method is not None else NULL

    result = RPY2_BINOM.binom_power(
        p_alt=p_alt,
        n=n,
        p=p,
        alpha=alpha,
        phi=phi,
        alternative=alternative,
        method=method,
    )

    return result[0]


def cloglog_sample_size(
    p_alt: float,
    n: Optional[int] = None,
    p: float = 0.5,
    power: float = 0.8,
    alpha: float = 0.05,
    alternative: Optional[Literal["two.sided", "greater", "less"]] = None,
    exact_n: bool = False,
    recompute_power: bool = False,
    phi: float = 1,
):
    """Tries calling `binom.power` from R or returns `None` if R is not available."""
    if RPY2_BINOM is None:
        return None

    # ensure native types
    p_alt = float(p_alt)
    n = int(n) if n is not None else NULL
    p = float(p)
    power = float(power)
    alpha = float(alpha)
    alternative = alternative if alternative is not None else NULL
    exact_n = bool(exact_n)
    recompute_power = bool(recompute_power)
    phi = float(phi)

    result = RPY2_BINOM.cloglog_sample_size(
        p_alt=p_alt,
        n=n,
        p=p,
        power=power,
        alpha=alpha,
        alternative=alternative,
        exact_n=exact_n,
        recompute_power=recompute_power,
        phi=phi,
    )

    with (default_converter + pandas2ri.converter).context():
        df = conversion.get_conversion().rpy2py(result)
        return int(df.iloc[0].n)
