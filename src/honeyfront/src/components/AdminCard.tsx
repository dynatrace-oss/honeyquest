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

import { useCallback, useMemo, useState } from "react";
import { useQuery } from "react-query";
import Select, { OnChangeValue } from "react-select";
import { useToggle } from "usehooks-ts";

import { QAnnotation } from "../types/Common";

import CodeView from "./CodeView";
import ErrorBanner from "./ErrorBanner";
import LoadingSpinner from "./LoadingSpinner";

import {
  IDiagnosticsSettings,
  IDiagnosticsSizeItems,
  IQuery,
} from "../types/ApiTypes";
import {
  ApiError,
  deleteAdminResults,
  getAdminDiagnosticsFeedback,
  getAdminDiagnosticsQueries,
  getAdminDiagnosticsQuery,
  getAdminDiagnosticsResponses,
  getAdminDiagnosticsSessions,
  getAdminDiagnosticsSettings,
  getAdminDiagnosticsUsers,
  postAdminSync,
} from "../utils/Api";
import { grabKey } from "../utils/Utils";

import "./AdminCard.css";

interface ISelectType {
  label: string;
  value: string;
}

/**
 * A card that asks for the user's profile.
 */
function AdminCard() {
  // state for fetching diagnostic data selectively
  const [seeSett, toggleSeeSett] = useToggle(false);
  const [seeQuer, toggleSeeQuer] = useToggle(false);
  const [seeSess, toggleSeeSess] = useToggle(false);
  const [seeUser, toggleSeeUser] = useToggle(false);
  const [seeFeed, toggleSeeFeed] = useToggle(false);
  const [seeResp, toggleSeeResp] = useToggle(false);
  const [queryId, setQueryId] = useState<string | null>(null);

  // fetch the next query from the backend
  const {
    data: query,
    error: queryError,
    isSuccess: queryIsSuccess,
  } = useQuery<IQuery, ApiError>(
    ["query", queryId],
    () => getAdminDiagnosticsQuery(String(queryId)),
    { enabled: !!queryId },
  );

  // all the (possibly enabled) fetchers of diagnostic data
  const {
    data: sett,
    error: settErr,
    isSuccess: settSucc,
  } = useQuery<IDiagnosticsSettings, ApiError>(
    ["diagnostics", "settings"],
    getAdminDiagnosticsSettings,
    { enabled: seeSett },
  );

  const {
    data: quer,
    error: querErr,
    isSuccess: querSucc,
  } = useQuery<IDiagnosticsSizeItems, ApiError>(
    ["diagnostics", "queries"],
    getAdminDiagnosticsQueries /* always enabled for the dropdown */,
  );

  const {
    data: sess,
    error: sessErr,
    isSuccess: sessSucc,
  } = useQuery<IDiagnosticsSizeItems, ApiError>(
    ["diagnostics", "sessions"],
    getAdminDiagnosticsSessions,
    { enabled: seeSess },
  );

  const {
    data: user,
    error: userErr,
    isSuccess: userSucc,
  } = useQuery<IDiagnosticsSizeItems, ApiError>(
    ["diagnostics", "profiles"],
    getAdminDiagnosticsUsers,
    { enabled: seeUser },
  );

  const {
    data: feed,
    error: feedErr,
    isSuccess: feedSucc,
  } = useQuery<IDiagnosticsSizeItems, ApiError>(
    ["diagnostics", "feedback"],
    getAdminDiagnosticsFeedback,
    { enabled: seeFeed },
  );

  const {
    data: resp,
    error: respErr,
    isSuccess: respSucc,
  } = useQuery<IDiagnosticsSizeItems, ApiError>(
    ["diagnostics", "responses"],
    getAdminDiagnosticsResponses,
    { enabled: seeResp },
  );

  const fragments = [];

  if (seeSett) {
    if (settErr)
      fragments.push(<ErrorBanner key="settings-error" error={settErr} />);
    else if (!settSucc)
      fragments.push(<LoadingSpinner key="settings-spinner" margin />);
    else
      fragments.push(
        <div key="settings-view">
          <h5 className="card-title pt-4 pb-2">Server configuration</h5>
          <CodeView maximizable code={JSON.stringify(sett, null, 2)} />
        </div>,
      );
  }

  if (seeQuer) {
    if (querErr)
      fragments.push(<ErrorBanner key="queries-error" error={querErr} />);
    else if (!querSucc)
      fragments.push(<LoadingSpinner key="queries-spinner" margin />);
    else
      fragments.push(
        <div key="queries-view">
          <h5 className="card-title pt-4 pb-2">Query diagnostics</h5>
          <CodeView maximizable code={JSON.stringify(quer, null, 2)} />
        </div>,
      );
  }

  if (seeSess) {
    if (sessErr)
      fragments.push(<ErrorBanner key="sessions-error" error={sessErr} />);
    else if (!sessSucc)
      fragments.push(<LoadingSpinner key="sessions-spinner" margin />);
    else
      fragments.push(
        <div key="sessions-view">
          <h5 className="card-title pt-4 pb-2">Session diagnostics</h5>
          <CodeView maximizable code={JSON.stringify(sess, null, 2)} />
        </div>,
      );
  }

  if (seeUser) {
    if (userErr)
      fragments.push(<ErrorBanner key="users-error" error={userErr} />);
    else if (!userSucc)
      fragments.push(<LoadingSpinner key="users-spinner" margin />);
    else
      fragments.push(
        <div key="users-view">
          <h5 className="card-title pt-4 pb-2">Users diagnostics</h5>
          <CodeView maximizable code={JSON.stringify(user, null, 2)} />
        </div>,
      );
  }

  if (seeFeed) {
    if (feedErr)
      fragments.push(<ErrorBanner key="feedback-error" error={feedErr} />);
    else if (!feedSucc)
      fragments.push(<LoadingSpinner key="feedback-spinner" margin />);
    else
      fragments.push(
        <div key="feedback-view">
          <h5 className="card-title pt-4 pb-2">Feedback diagnostics</h5>
          <CodeView maximizable code={JSON.stringify(feed, null, 2)} />
        </div>,
      );
  }

  if (seeResp) {
    if (respErr)
      fragments.push(<ErrorBanner key="responses-error" error={respErr} />);
    else if (!respSucc)
      fragments.push(<LoadingSpinner key="responses-spinner" margin />);
    else
      fragments.push(
        <div key="responses-view">
          <h5 className="card-title pt-4 pb-2">Responses diagnostics</h5>
          <CodeView maximizable code={JSON.stringify(resp, null, 2)} />
        </div>,
      );
  }

  if (queryId) {
    if (queryError)
      fragments.push(<ErrorBanner key="query-error" error={queryError} />);
    else if (!queryIsSuccess)
      fragments.push(<LoadingSpinner key="query-spinner" margin />);
    else {
      const deceptiveLines = grabKey(
        QAnnotation.DeceptiveLines,
        query.annotations,
        String,
        undefined,
      );

      const riskyLines = grabKey(
        QAnnotation.RiskyLines,
        query.annotations,
        String,
        undefined,
      );

      const queryDetails = (
        <div className="card-footer">
          <div className="container">
            <div className="row row-cols-auto gx-3 gy-2 text-muted small">
              <div className="col">id: {query.id}</div>
              <div className="col">type: {query.type}</div>
              <div className="col">label: {query.label}</div>
              <div className="col">
                annotations: {JSON.stringify(query.annotations, null, 1)}
              </div>
              <div className="col">
                references: {JSON.stringify(query.references, null, 1)}
              </div>
            </div>
          </div>
        </div>
      );

      fragments.push(
        <div key="query-view">
          <h5 className="card-title pt-4 pb-2">Invidual query analysis</h5>
          <CodeView
            code={query.data}
            maximizable
            highlightHack={riskyLines}
            highlightTrap={deceptiveLines}
          />
          {queryDetails}
        </div>,
      );
    }
  }

  // options and handler for the select dropdown
  const options: ISelectType[] = useMemo(() => {
    if (!quer || !Object.keys(quer).includes("items")) return [];
    const queryIds = quer.items as string[];
    return queryIds.map((item) => ({ value: item, label: item }));
  }, [quer]);

  const onSelectChange = useCallback(
    (newValue: OnChangeValue<ISelectType, false>) =>
      setQueryId(newValue?.value ?? null),
    [],
  );

  return (
    <div className="AdminCard card">
      <div className="card-header">
        <span className="text-muted">Admin Panel</span>
      </div>
      <div className="card-body">
        <div className="d-flex align-items-top mb-2">
          <button
            type="button"
            className={`AdminButton btn btn${
              seeSett ? "" : "-outline"
            }-secondary me-2`}
            onClick={toggleSeeSett}
          >
            Settings
          </button>
          <button
            type="button"
            className={`AdminButton btn btn${
              seeQuer ? "" : "-outline"
            }-secondary me-2`}
            onClick={toggleSeeQuer}
          >
            Queries
          </button>
          <button
            type="button"
            className={`AdminButton btn btn${
              seeSess ? "" : "-outline"
            }-secondary me-2`}
            onClick={toggleSeeSess}
          >
            Sessions
          </button>
          <button
            type="button"
            className={`AdminButton btn btn${
              seeUser ? "" : "-outline"
            }-secondary me-2`}
            onClick={toggleSeeUser}
          >
            Users
          </button>
          <button
            type="button"
            className={`AdminButton btn btn${
              seeFeed ? "" : "-outline"
            }-secondary me-2`}
            onClick={toggleSeeFeed}
          >
            Feedback
          </button>
          <button
            type="button"
            className={`AdminButton btn btn${
              seeResp ? "" : "-outline"
            }-secondary me-2`}
            onClick={toggleSeeResp}
          >
            Responses
          </button>
          <a
            href="/api/admin/results"
            role="button"
            className="AdminButton btn btn-primary me-2"
          >
            <i className="bi bi-download"></i>Download results
          </a>
          <button
            type="button"
            className="AdminButton btn btn-info me-2"
            onClick={() => postAdminSync()}
          >
            <i className="bi bi-arrow-repeat"></i>Sync cache
          </button>
          <button
            type="button"
            className="AdminButton btn btn-danger me-2"
            onClick={() => deleteAdminResults()}
          >
            <i className="bi bi-trash-fill"></i>Clear results
          </button>
        </div>
        <div className="d-flex align-items-top">
          <Select
            options={options}
            isClearable={true}
            className="QueryInput"
            onChange={onSelectChange}
            placeholder="Analyze query .."
          />
        </div>
        {fragments}
      </div>
    </div>
  );
}

export default AdminCard;
