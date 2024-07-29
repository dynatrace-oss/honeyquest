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

import Cookies from "js-cookie";
import { useCallback, useEffect, useState } from "react";
import { useQueryClient } from "react-query";
import { useToggle } from "usehooks-ts";

import AdminCard from "./AdminCard";
import HoneyquestLead from "./HoneyquestLead";
import ProfileCard from "./ProfileCard";
import ProfileInfo from "./ProfileInfo";
import ProgressBar from "./ProgressBar";
import QueryCardGroup, { IProgress } from "./QueryCardGroup";

import { IProfile, IQueryResponse } from "../types/ApiTypes";
import { ISession, QAction, QState } from "../types/Common";
import { getProfile, postAdminAuth } from "../utils/Api";
import {
  isProfileState,
  isQueryState,
  isStartState,
  nextState,
} from "../utils/States";
import { xor } from "../utils/Utils";

/**
 * Main React component.
 */
function Main() {
  const queryClient = useQueryClient();
  const initState: ISession = {
    state: QState.Init,
    profile: null,
    queryCount: 0,
    endOfTutorial: false,
    showAdminView: false,
  };
  const [session, setSession] = useState<ISession>(initState);
  const [showAdmin, toggleShowAdmin] = useToggle(false);

  // progress bar state
  const emptyProgress: IProgress = { active: false, answered: 0, total: 0 };
  const [progress, setProgress] = useState<IProgress>(emptyProgress);
  const progressVisibility = progress.active ? "visible" : "hidden";

  const isStartPage = isStartState(session.state);
  const isQueriesPage = isQueryState(session.state);
  const isProfilePage = isProfileState(session.state);
  console.assert(xor(xor(isStartPage, isQueriesPage), isProfilePage));

  /* lead controllers */

  const onLeadSubmit = useCallback(() => {
    // submitting the lead must mean that the user has accepted the data privacy statement
    Cookies.set("COOKIE_CONSENT", "true", { expires: 365 });
    setSession((s) => nextState(s, QAction.Start));
  }, []);

  /* query card controllers */

  const onQuerySubmit = useCallback(
    (_response: IQueryResponse, endOfTutorial: boolean): boolean => {
      // console.log(_response);
      const mutatedSession = {
        ...session,
        endOfTutorial,
        queryCount: session.queryCount + 1,
      };
      const pendingState = nextState(mutatedSession, QAction.NextQuery);
      setSession(pendingState);

      // we only continue fetching queries if
      // the next state is still a queries state
      return isQueryState(pendingState.state);
    },
    [session],
  );

  /* profile card controllers */

  const onProfileSubmit = useCallback((profile: IProfile) => {
    setSession((s) => nextState({ ...s, profile }, QAction.SubmitProfile));
  }, []);

  const onProfileUpdate = useCallback(
    () => setSession((s) => nextState(s, QAction.UpdateProfile)),
    [],
  );

  const onProfileClear = useCallback(() => {
    // make sure to also remove the cookie consent on profile clear
    Cookies.remove("COOKIE_CONSENT");
    // invalidate queries, do not use cached ones
    void queryClient.invalidateQueries("query");
    setSession((s) =>
      nextState({ ...s, profile: null, queryCount: 0 }, QAction.ClearProfile),
    );
  }, [queryClient]);

  const onProfileAbort = useCallback(
    () => setSession((s) => nextState(s, QAction.AbortProfileUpdate)),
    [],
  );

  /* admin panel "backdoor" */

  const onHashChange = useCallback(() => {
    const hashStr = window.location.hash.substring(1);
    if (hashStr === "admin") {
      const token = prompt("Please enter the admin token") ?? "";
      postAdminAuth(token)
        .then(() => setSession((s) => ({ ...s, showAdminView: true })))
        .catch(console.error)
        .finally(() => {
          // always clean the hash from url again, without refreshing
          window.history.pushState(
            "",
            document.title,
            window.location.pathname + window.location.search,
          );
        });
    }
  }, []);

  useEffect(() => {
    window.addEventListener("hashchange", onHashChange, false);
    return () => window.removeEventListener("hashchange", onHashChange, false);
  }, [onHashChange]);

  /* every time we mount, check if a user profile became available */

  useEffect(() => {
    // avoid fetching profile if user has not accepted the data privacy statement first
    if (!Cookies.get("COOKIE_CONSENT")) return;
    getProfile()
      .then((res) => {
        if (res == null) return;
        setSession((s) =>
          nextState({ ...s, profile: res }, QAction.SubmitProfile),
        );
      })
      .catch(console.error);
  }, []);

  return (
    <main role="main">
      <div className="container py-5">
        <div className="row g-4">
          <div className="col-lg-6">
            <HoneyquestLead
              showAdmin={session.showAdminView}
              showIntro={isStartPage}
              showSummary={isStartPage && !!session.profile}
              showDataPrivacy={Cookies.get("COOKIE_CONSENT") === undefined}
              onStart={onLeadSubmit}
              onAdmin={toggleShowAdmin}
            />
          </div>
          <div className="col-lg-6" style={{ paddingRight: "28px" }}>
            {!isStartPage && (
              <ProfileInfo
                profile={session.profile}
                onUpdate={onProfileUpdate}
                onClear={onProfileClear}
              />
            )}
          </div>
        </div>

        {isQueriesPage && (
          <>
            <div className="row mt-5">
              <div className="col" style={{ visibility: progressVisibility }}>
                <ProgressBar
                  progress={progress}
                  color={session.profile?.color}
                />
              </div>
            </div>
            <div className="row">
              <div className="col">
                <QueryCardGroup
                  showDetails={session.showAdminView}
                  onSubmit={onQuerySubmit}
                  onProgressChange={setProgress}
                  fetchMetadata={false}
                />
              </div>
            </div>
          </>
        )}

        {isProfilePage && (
          <div className="row mt-5">
            <div className="col">
              <ProfileCard
                initState={session.profile}
                onSubmit={onProfileSubmit}
                onAbort={onProfileAbort}
                showAbort={session.state === QState.ProfileUpdate}
              />
            </div>
          </div>
        )}

        {showAdmin && (
          <div className="row mt-5">
            <div className="col">
              <AdminCard />
            </div>
          </div>
        )}
      </div>
    </main>
  );
}

export default Main;
