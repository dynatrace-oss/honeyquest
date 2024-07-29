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

import { Tuple2 } from "tuplerone";

import { IProfile } from "./ApiTypes";

export const FEEDBACK_MODAL_ID = "honeyquest-feedback-modal";

/**
 * The full session object, containing the current state, the user profile, and metrics.
 */
export declare interface ISession {
  /** UI State of Honeyquest */
  state: QState;
  /** The current user profile, if available */
  profile: IProfile | null;
  /** The number of queries already submitted */
  queryCount: number;
  /** If the last query indicated the end of the tutorial */
  endOfTutorial: boolean;
  /** Enable the admin button */
  showAdminView: boolean;
}

/**
 * States of the Honeyquest UI.
 */
export enum QState {
  /** Landing page for new users */
  Init,
  /** New users without profile information get introduced with a teaser */
  Teaser,
  /** Let's ask user to tell us more about them */
  Profile,
  /** The normal program flow, with a profiled user */
  Queries,
  /** Update profile information */
  ProfileUpdate,
}

/**
 * User actions that can be taken in the Honeyquest UI.
 */
export enum QAction {
  /** Start the game */
  Start,
  /** Continue to the next query */
  NextQuery,
  /** Submit the profile information */
  SubmitProfile,
  /** Request to update profile information */
  UpdateProfile,
  /** Abort the profile information update */
  AbortProfileUpdate,
  /** Clear the entire session */
  ClearProfile,
}

/** The type of a code selection */
export enum SelType {
  Hack,
  Trap,
}

/** The selection of a code line */
export type SelLine = Tuple2<number, SelType>;

/**
 * Query annotations used by honeyquest
 */
export enum QAnnotation {
  /** Overrides the text of the continue button */
  ButtonText = "honeyquest/button-text",
  /** Enables or disables that lines can be selected */
  Select = "honeyquest/select",
  /** Enables or disables that lines can be selected as hacks */
  SelectHacks = "honeyquest/select-hacks",
  /** Enables or disables that lines can be selected as traps */
  SelectTraps = "honeyquest/select-traps",
  /** Sets the maximum number of hacks that can be selected */
  MaxHacks = "honeyquest/max-hacks",
  /** Sets the maximum number of traps that can be selected */
  MaxTraps = "honeyquest/max-traps",
  /** Restricts the lines that can be selected (using LAS) */
  AllowLines = "honeyquest/allow-lines",
  /** Indicates that this is the last query of the tutorial */
  TutorialEnd = "honeyquest/tutorial-end",
  /** Marks risky code fragments (using LAS)  */
  RiskyLines = "risk/risky-lines",
  /** Marks deceptive code fragments (using LAS)  */
  DeceptiveLines = "honeypatch/deceptive-lines",
}
