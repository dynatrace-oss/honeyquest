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

import { useCallback, useState } from "react";
import { drop } from "../utils/Utils";

/**
 * A toggle list is a list with some elements in it that
 * you can easily add or remove with one "toggle" operation.
 * We use it to easily toggle the selection of lines in the CodeView.
 * @returns An array of string, with the individual lines
 */
export function useToggleList<E>() {
  const [elements, setElements] = useState<E[]>([]);
  const reset = useCallback(() => setElements([]), []);
  const toggle = useCallback(
    (ele: E, opts?: { onlySet?: boolean; onlyUnset?: boolean }) => {
      const { onlySet = false, onlyUnset = false } = opts ?? {};
      setElements((elements) => {
        const nxt = [...elements];
        if (nxt.includes(ele) && !onlySet) drop(nxt, ele);
        else if (!onlyUnset) nxt.push(ele);
        return nxt;
      });
    },
    [],
  );

  return { reset, toggle, elements };
}
