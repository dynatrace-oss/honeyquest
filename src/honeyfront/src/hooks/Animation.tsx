// Copyright 2024 Dynatrace LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// Portions of this code, as identified in remarks, are provided under the
// Creative Commons BY-SA or the MIT license, and are provided without
// any warranty. In each of the remarks, we have provided attribution to the
// original creators and other attribution parties, along with the title of
// the code (if known) a copyright notice and a link to the license, and a
// statement indicating whether or not we have modified the code.

import { useMemo, useState, useEffect } from "react";
import { useInterval } from "usehooks-ts";

// total effect duration in millseconds
const EFFECT_DURATION = 1500;
// at each time step, we show 1 / LINE_DIVISOR of a line
const LINE_DIVISOR = 10;

/**
 * Just a nice animation that slowly unravels the code lines
 * @param code The code lines, as a text blob with line breaks
 * @param enabled Whether to enable the animation
 * @returns An array of string, with the individual lines
 */
export function useAnimatedCodeLines(code: string, enabled = true) {
  const lines = useMemo(() => code.split("\n"), [code]);

  const effectSpeed = EFFECT_DURATION / LINE_DIVISOR / lines.length;

  // if disabled, we just skip to the end of the animation
  // so that we won't conditionally call the useInterval hook
  const effectInit = enabled ? 0 : lines.length * LINE_DIVISOR;
  const [effectIndex, setEffectIndex] = useState<number>(effectInit);

  useInterval(
    () => setEffectIndex((i) => i + 1),
    effectIndex / LINE_DIVISOR < lines.length ? effectSpeed : null,
  );

  // ensure to reset the effect index when the lines change
  useEffect(() => setEffectIndex(effectInit), [effectInit, lines]);

  return lines
    .slice(0, Math.ceil((effectIndex + 1) / LINE_DIVISOR))
    .map((line, i) => {
      if (i > effectIndex / LINE_DIVISOR - 1) {
        const end =
          (((effectIndex % LINE_DIVISOR) + 1) / LINE_DIVISOR) * line.length;
        return line.slice(0, Math.ceil(end));
      }
      return line;
    });
}
