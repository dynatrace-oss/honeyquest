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

import { useCallback } from "react";

import { IProfile } from "../types/ApiTypes";
import { deleteProfile } from "../utils/Api";

import "./ProfileInfo.css";

declare interface IProfileInfoProps {
  profile: IProfile | null;
  onUpdate: () => void;
  onClear: () => void;
}

declare interface IClearSessionModalProps {
  id: string;
  onSubmit: () => void;
}

/**
 * Shows a banner indicating the current profile information.
 */
function ProfileInfo(props: Readonly<IProfileInfoProps>) {
  const { profile, onUpdate, onClear } = props;

  // calls the clear endpoint on the backend and fires the callback on success
  // (define this before the early return to avoid creating a conditional hook)
  const handleOnClear = useCallback(() => {
    deleteProfile()
      .then(() => onClear())
      .catch(console.error);
  }, [onClear]);

  // destructure profile data, if given
  const emptyProfile: IProfile = {
    nickname: null,
    job: null,
    years: null,
    rank: null,
    color: "#fff",
  };
  const displayProfile = profile ?? emptyProfile;

  const modalId = "clearSessionModal";

  const profileButtons = (
    <>
      <button
        type="button"
        className="ProfileButton btn btn-sm btn-outline-secondary me-2"
        onClick={onUpdate}
      >
        Update profile
      </button>
      <button
        type="button"
        className="ProfileButton btn btn-sm btn-outline-danger"
        data-bs-toggle="modal"
        data-bs-target={`#${modalId}`}
      >
        Clear profile
      </button>
    </>
  );

  const sessionButton = (
    <button
      type="button"
      className="ProfileButton btn btn-sm btn-secondary"
      data-bs-toggle="modal"
      data-bs-target={`#${modalId}`}
    >
      Clear session
    </button>
  );

  return (
    <div>
      <div className="d-flex flex-row justify-content-end">
        <div
          className="me-2"
          style={{ width: "0.5em", background: displayProfile.color }}
        >
          &nbsp;
        </div>
        <div>{getProfileAbbrevFragment(displayProfile)}</div>
      </div>
      <div className="d-flex flex-row justify-content-end mt-3">
        {profile ? profileButtons : sessionButton}
      </div>
      <ClearSessionModal id={modalId} onSubmit={handleOnClear} />
    </div>
  );
}

/**
 * A model that is shown before the user tries to clear the session.
 */
function ClearSessionModal(props: Readonly<IClearSessionModalProps>) {
  const { id, onSubmit } = props;
  return (
    <div
      className="modal fade"
      id={id}
      tabIndex={-1}
      aria-labelledby="clearSessionModalLabel"
      aria-hidden="true"
    >
      <div className="modal-dialog">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title" id="clearSessionModalLabel">
              Are you sure?
            </h5>
            <button
              type="button"
              className="btn-close"
              data-bs-dismiss="modal"
              aria-label="Close"
            ></button>
          </div>
          <div className="modal-body">
            <p>
              <strong>
                This action clears your profile and resets your progress.
              </strong>
            </p>
            <p>
              You will be brought back to the tutorial and have to start all
              over again. We will not be able to recover your profile.
            </p>
          </div>
          <div className="modal-footer">
            <button
              type="button"
              className="btn btn-secondary-outline"
              data-bs-dismiss="modal"
            >
              Abort
            </button>
            <button
              type="button"
              className="btn btn-danger"
              data-bs-dismiss="modal"
              onClick={onSubmit}
            >
              Yes, clear my profile and reset my progress
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

const JOB_NAMES = {
  student: "Campus Crusader",
  dev: "Code Wizard",
  ops: "Infrastructure Hero",
  secops: "Security Ninja",
  biz: "Business Mastermind",
  research: "Research Rockstar",
  other: "Mysterious Internet Person",
};

const RANK_NAMES = {
  none: "Baby",
  little: "Novice",
  good: "Competent",
  advanced: "Skilled",
  expert: "Expert",
};

function getProfileAbbrevFragment(profile: IProfile) {
  if (profile.nickname) {
    return (
      <>
        <i
          className="bi bi-person-fill pe-2"
          style={{ color: profile.color }}
        ></i>
        <span>
          <strong>{profile.nickname}</strong>
        </span>
      </>
    );
  }

  const fragments: JSX.Element[] = [];
  if (profile.job) {
    let name = JOB_NAMES[profile.job];
    if (profile.rank) {
      name = `${RANK_NAMES[profile.rank]} ${name}`;
    }

    fragments.push(
      <i
        key="profile-icon"
        className="bi bi-person-lock pe-2"
        style={{ color: profile.color }}
      ></i>,
    );
    fragments.push(<span key="profile-name">{name}</span>);
  }

  if (profile.years) {
    fragments.push(
      <span key="profile-years" className="text-muted">
        , since {profile.years} years
      </span>,
    );
  }

  return fragments;
}

export default ProfileInfo;
