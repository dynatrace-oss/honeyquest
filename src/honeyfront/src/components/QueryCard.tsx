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

import CodeView from "./CodeView";
import LoadingSpinner from "./LoadingSpinner";
import Tooltip from "./Tooltip";

import { IQuery } from "../types/ApiTypes";
import { FEEDBACK_MODAL_ID, QAnnotation as QA, SelLine } from "../types/Common";
import {
  getExploitDescription,
  getNiceQueryTypeName,
  getTrapDescription,
  getTypeDescription,
} from "../utils/References";
import { grabKey } from "../utils/Utils";

import "./QueryCard.css";

declare interface IQueryCardProps {
  query: IQuery | null;
  invalid: boolean;
  showDetails: boolean;
  animateCode: boolean;
  onClick: (lines: SelLine[]) => void;
}

/**
 * A card that shows a query and navigation buttons.
 */
function QueryCard(props: Readonly<IQueryCardProps>) {
  const { query, invalid, showDetails, animateCode, onClick } = props;

  // selection state from CodeView child
  const [selection, setSelection] = useState<SelLine[]>([]);
  const areLinesSelected = selection.length > 0;
  const handleSelect = useCallback(
    (lines: SelLine[]) => setSelection(lines),
    [],
  );

  const handleAnswer = useCallback(
    () => onClick(selection),
    [onClick, selection],
  );

  // unpack query or use empty values
  const emptyQuery: IQuery = {
    id: "",
    label: null,
    type: "",
    references: [],
    annotations: [],
    data: "",
  };
  const { id, label, type, references, annotations, data } =
    query ?? emptyQuery;
  const isTutorial = type === "tutorial";

  // grab some ui-specific annotations
  const buttonText = grabKey(QA.ButtonText, annotations, String, undefined);
  const canSelect = grabKey(QA.Select, annotations, Boolean, true);
  const canHack = grabKey(QA.SelectHacks, annotations, Boolean, true);
  const canTrap = grabKey(QA.SelectTraps, annotations, Boolean, true);
  const maxHacks = grabKey(QA.MaxHacks, annotations, Number, undefined);
  const maxTraps = grabKey(QA.MaxTraps, annotations, Number, undefined);
  const allowLines = grabKey(QA.AllowLines, annotations, String, undefined);

  const codeFragment = (
    <CodeView
      code={data}
      disabled={false} /* do not use `invalid` here to avoid a flashing card */
      disableHacks={!canHack}
      disableTraps={!canTrap}
      animated={animateCode}
      maximizable
      selectable={!invalid && canSelect}
      selectableLines={allowLines}
      maxHacks={maxHacks}
      maxTraps={maxTraps}
      onSelect={handleSelect}
    />
  );

  const queryDetails = (
    <div className="card-footer">
      <div className="container">
        <div className="row row-cols-auto gx-3 gy-2 text-muted small">
          <div className="col">id: {id}</div>
          <div className="col">type: {type}</div>
          <div className="col">label: {label}</div>
          <div className="col">
            annotations: {JSON.stringify(annotations, null, 1)}
          </div>
          <div className="col">
            references: {JSON.stringify(references, null, 1)}
          </div>
        </div>
      </div>
    </div>
  );

  const introParagraph = (
    <p className="mb-0">
      Assume you are a hacker seeing the following&nbsp;
      <mark>{getNiceQueryTypeName(type)}</mark>&nbsp;&nbsp;
      <Tooltip
        text={getTypeDescription(type)}
        placement="top"
        customClass="TooltipType"
      >
        <span>
          <i className="bi bi-info-circle HelpIcon"></i>
        </span>
      </Tooltip>
      <br />
      <span className="small text-muted">
        <i className="bi bi-lightning"></i> {getExploitDescription(type)}
      </span>
      <br />
      <span className="small text-muted">
        <i className="bi bi-pin-angle"></i> {getTrapDescription(type)}
      </span>
    </p>
  );

  const buttonFeedback = (
    <Tooltip
      text="Send feedback or report a mistake in this query"
      placement="left"
    >
      <button
        type="button"
        className="FeedbackButton btn btn-outline-secondary"
        data-bs-toggle="modal"
        data-bs-target={`#${FEEDBACK_MODAL_ID}`}
      >
        <i className="bi bi-chat-text"></i>
      </button>
    </Tooltip>
  );

  const buttonSubmit = (
    <button
      type="button"
      className="AnswerButton btn btn-primary"
      disabled={!query || invalid}
      onClick={handleAnswer}
    >
      <i className="bi bi-caret-right-fill"></i>
      <span>{buttonText ?? "Submit selection"}</span>
    </button>
  );

  const buttonSkip = (
    <button
      type="button"
      className="AnswerButton btn btn-light"
      disabled={!query || invalid}
      onClick={handleAnswer}
    >
      <i className="bi bi-caret-right-fill"></i>
      <span>{buttonText ?? "This query is neither risky nor deceptive"}</span>
    </button>
  );

  const spinnerFragment = <LoadingSpinner margin />;

  return (
    <div className="QueryCard card">
      <div className="card-body">
        <div className="QueryCardHeader gap-3 d-flex flex-wrap align-items-start">
          <div className="flex-fill pe-2">
            {isTutorial || !query ? null : introParagraph}
          </div>
          <div className="ms-auto">
            {areLinesSelected ? buttonSubmit : buttonSkip}
          </div>
        </div>
        {query ? codeFragment : spinnerFragment}
        <div className="mt-2 d-flex justify-content-end">{buttonFeedback}</div>
      </div>
      {query && showDetails ? queryDetails : null}
    </div>
  );
}

export default QueryCard;
