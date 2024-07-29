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

import { useCallback, useContext, useEffect, useMemo } from "react";
import { UnsafeTuple as UT } from "tuplerone";

import { userPreferences } from "../context/UserPreferences";
import { useAnimatedCodeLines } from "../hooks/Animation";
import { useToggleList } from "../hooks/SetMagic";
import { SelLine, SelType } from "../types/Common";
import { addSuffixIfMultiple as asim, inLAS, parseLAS } from "../utils/Utils";

import "./CodeView.css";

declare interface ICodeViewProps {
  code: string;
  disabled?: boolean;
  disableHacks?: boolean;
  disableTraps?: boolean;
  animated?: boolean;
  maximizable?: boolean;
  selectable?: boolean;
  selectableLines?: string /* Line Annotation Syntax (LAS) */;
  highlightHack?: string /* Line Annotation Syntax (LAS) */;
  highlightTrap?: string /* Line Annotation Syntax (LAS) */;
  maxHacks?: number;
  maxTraps?: number;
  onSelect?: (lines: SelLine[]) => void;
}

/**
 * A card that shows a query and navigation buttons.
 */
function CodeView(props: Readonly<ICodeViewProps>) {
  const {
    code,
    disabled,
    disableHacks,
    disableTraps,
    animated,
    maximizable,
    selectable,
    selectableLines,
    highlightHack,
    highlightTrap,
    maxHacks,
    maxTraps,
    onSelect,
  } = props;

  const { fullscreen, setFullscreen } = useContext(userPreferences);

  // possibly extract the line ranges that can be selected or must be highlighted
  const lasSelectable = useMemo(
    () => (selectableLines ? parseLAS(selectableLines) : undefined),
    [selectableLines],
  );
  const lasHack = useMemo(
    () => (highlightHack ? parseLAS(highlightHack) : undefined),
    [highlightHack],
  );
  const lasTrap = useMemo(
    () => (highlightTrap ? parseLAS(highlightTrap) : undefined),
    [highlightTrap],
  );

  // stores the selected lines
  const {
    reset: resetSelection,
    toggle: toggleSelection,
    elements: selection,
  } = useToggleList<SelLine>();

  // is hack selection possible, and are we below the max?
  const canHack = !disableHacks && selectable;
  const belowMaxHacks =
    !maxHacks || countSelType(selection, SelType.Hack) < maxHacks;

  // is trap selection possible, and are we below the max?
  const canTrap = !disableTraps && selectable;
  const belowMaxTraps =
    !maxTraps || countSelType(selection, SelType.Trap) < maxTraps;

  // clear the selection when the code changes and propagate to parent
  useEffect(() => resetSelection(), [code, onSelect, resetSelection]);
  useEffect(() => onSelect?.(selection), [onSelect, selection]);

  // toggle line callbacks that may also unselect the other option
  const toggleLine = useCallback(
    (i: number, type: SelType) => {
      const other = type === SelType.Hack ? SelType.Trap : SelType.Hack;
      toggleSelection(UT(i, type));
      toggleSelection(UT(i, other), { onlyUnset: true });
    },
    [toggleSelection],
  );

  // generate the possibly animated code lines
  const lines = useAnimatedCodeLines(code, !!animated);
  const lineFragments = lines.map((line, i) => {
    const canSelectLine = lasSelectable ? inLAS(i + 1, lasSelectable) : true;
    const isHighlightHack = lasHack ? inLAS(i + 1, lasHack) : false;
    const isHighlightTrap = lasTrap ? inLAS(i + 1, lasTrap) : false;

    const hackOrder = selection.indexOf(UT(i + 1, SelType.Hack));
    const trapOrder = selection.indexOf(UT(i + 1, SelType.Trap));
    const toHack = hackOrder !== -1; // is this line selected as a hack?
    const toTrap = trapOrder !== -1; // is this line selected as a trap?

    // build css classes
    const trClazz = asim(undefined, {
      hack: toHack || isHighlightHack,
      trap: toTrap || isHighlightTrap,
    });
    const tdHack = asim("TdHack", {
      selectable: canHack && canSelectLine,
      selected: toHack || isHighlightHack,
    });
    const tdTrap = asim("TdTrap", {
      selectable: canTrap && canSelectLine,
      selected: toTrap || isHighlightTrap,
    });

    // hack and trap callbacks must still be enabled even if
    // we are at the max, but only if the line is already
    // selected, so that the user can deselect it again

    const onHack =
      canHack && canSelectLine && (belowMaxHacks || toHack)
        ? () => toggleLine(i + 1, SelType.Hack)
        : undefined;
    const onTrap =
      canTrap && canSelectLine && (belowMaxTraps || toTrap)
        ? () => toggleLine(i + 1, SelType.Trap)
        : undefined;

    return (
      <tr className={trClazz} key={i}>
        <td className={tdHack} onClick={onHack}>
          <span>{toHack ? hackOrder + 1 : ""}</span>
          <i className="bi bi-lightning-fill"></i>
        </td>
        <td className="TdText">{line}</td>
        <td className={tdTrap} onClick={onTrap}>
          <i className="bi bi-pin-angle-fill"></i>
          <span>{toTrap ? trapOrder + 1 : ""}</span>
        </td>
      </tr>
    );
  });

  const clazz = useMemo(
    () => asim("CodeView", { disabled, selectable, fullscreen }),
    [disabled, selectable, fullscreen],
  );

  const fullscreenIcon = `bi-fullscreen${fullscreen ? "-exit" : ""}`;
  const fullscreenButton = (
    <button
      className="FullscreenButton btn btn-outline-light"
      onClick={() => setFullscreen(!fullscreen)}
    >
      <i className={`bi ${fullscreenIcon}`}></i>
    </button>
  );

  return (
    <div className={clazz}>
      {maximizable && fullscreenButton}
      <table>
        <tbody>{lineFragments}</tbody>
      </table>
    </div>
  );
}

function countSelType(list: SelLine[], selType: SelType) {
  return list.filter((l) => l[1] === selType).length;
}

export default CodeView;
