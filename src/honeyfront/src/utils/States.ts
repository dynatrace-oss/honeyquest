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

import { ISession, QAction as QA, QState as QS } from "../types/Common";

/**
 * Computes the next UI state based on the current state,
 * some action, and extra session information.
 */
export function nextState(s: ISession, a: QA): ISession {
  let next = s.state;

  // special case for actions that are
  // not dependent on the current state
  if (a === QA.ClearProfile) {
    next = QS.Init;
  } else {
    // to aid visual clarity, we write state-transitions in full
    // instead of simplifying some conditional expressions
    switch (s.state) {
      case QS.Init:
        if (a === QA.Start && s.profile == null) next = QS.Teaser;
        if (a === QA.Start && s.profile != null) next = QS.Queries;
        break;

      case QS.Teaser:
        // if a user somehow skipped the profile page, ask again after 10 queries
        if (a === QA.NextQuery && (s.endOfTutorial || s.queryCount > 10))
          next = QS.Profile;
        if (a === QA.SubmitProfile && s.profile != null) next = QS.Queries;
        break;

      case QS.Profile:
        if (a === QA.SubmitProfile) next = QS.Queries;
        break;

      case QS.Queries:
        if (a === QA.UpdateProfile) next = QS.ProfileUpdate;
        break;

      case QS.ProfileUpdate:
        if (a === QA.SubmitProfile) next = QS.Queries;
        if (a === QA.AbortProfileUpdate) next = QS.Queries;
        break;

      default:
        next = QS.Init;
    }
  }

  return { ...s, state: next };
}

export function isStartState(state: QS): boolean {
  return [QS.Init].includes(state);
}

export function isQueryState(state: QS): boolean {
  return [QS.Teaser, QS.Queries].includes(state);
}

export function isProfileState(state: QS): boolean {
  return [QS.Profile, QS.ProfileUpdate].includes(state);
}
