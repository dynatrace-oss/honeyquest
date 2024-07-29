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

import { Tooltip as BsTooltip } from "bootstrap";
import React, { useEffect, useRef } from "react";

// Code Snippet: Bootstrap 5 tooltip component for React
//
// (c) 2020 Monsignor https://stackoverflow.com/a/70392725/927377
// Dynatrace has made changes to this code.
// This code snippet is supplied without warranty.
// This code snippet is licensed under CC BY-SA 4.0.

function Tooltip(p: {
  children: JSX.Element;
  text: string;
  placement?: BsTooltip.PopoverPlacement;
  customClass?: string;
  hidden?: boolean;
}) {
  const childRef = useRef(undefined as unknown as Element);
  const isHidden = p.hidden ?? false;

  useEffect(() => {
    const t = new BsTooltip(childRef.current, {
      title: p.text,
      placement: p.placement ?? "auto",
      customClass: p.customClass ?? "",
      offset: "0, 12px",
      trigger: "hover",
    });
    if (isHidden) t.disable();
    return () => t.dispose();
  }, [p.text, p.placement, p.customClass, isHidden]);

  return React.cloneElement(p.children, { ref: childRef });
}

export default Tooltip;
