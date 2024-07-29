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

import { ChangeEvent, FormEvent, useCallback, useReducer } from "react";

import { IProfile } from "../types/ApiTypes";
import { putProfile } from "../utils/Api";
import { randomColor } from "../utils/Utils";

declare interface IProfileCardProps {
  initState: IProfile | null;
  onSubmit: (profile: IProfile) => void;
  onAbort: () => void;
  showAbort: boolean;
}

/**
 * A card that asks for the user's profile.
 */
function ProfileCard(props: Readonly<IProfileCardProps>) {
  const { initState, onSubmit, onAbort, showAbort } = props;

  const emptyProfile: IProfile = {
    nickname: null,
    job: null,
    years: null,
    rank: null,
    color: randomColor(),
  };

  // use a reducer that allows us to update some state fields partially
  // and take the state from the props, if available
  const [formState, setFormatState] = useReducer(
    (curr: IProfile, next: Partial<IProfile>): IProfile => ({
      ...curr,
      ...next,
    }),
    initState ?? emptyProfile,
  );

  // sends form to the backend and fires the callback on success
  // TODO: TR-547 replace with useMutation and retry in case of 429 errors
  const handleSubmit = useCallback(
    (event: FormEvent) => {
      event.preventDefault();
      putProfile(formState)
        .then(() => onSubmit(formState))
        .catch(console.error);
    },
    [formState, onSubmit],
  );

  // updates component state on input changes
  const handleInputChange = useCallback(
    (event: ChangeEvent<HTMLSelectElement | HTMLInputElement>) => {
      setFormatState({ [event.target.name]: event.target.value });
    },
    [],
  );

  return (
    <div className="card">
      <div className="card-body">
        <h5 className="card-title">
          <i className="bi bi-file-person-fill"></i> Wait, please tell us more
          about yourself first
        </h5>
        <form className="mt-5" onSubmit={handleSubmit}>
          <div className="mb-3">
            <label htmlFor="profileJob" className="form-label col-form-label">
              What describes <strong>your current profession</strong> best?
            </label>
            <select
              required
              name="job"
              id="profileJob"
              defaultValue={formState.job ?? ""}
              className="form-select"
              onChange={handleInputChange}
            >
              <option value=""></option>
              <option value="student">Student</option>
              <option value="dev">
                Development (Developer, Engineer, Architect)
              </option>
              <option value="ops">
                Operations (System Administrator, SRE)
              </option>
              <option value="secops">
                Security Operations (Penetration Tester, Incident Detection and
                Response)
              </option>
              <option value="biz">
                Business (Manager, Leader, Sales, Marketing)
              </option>
              <option value="research">
                Research (Researcher, Scientist, Innovator)
              </option>
              <option value="other">None of the above</option>
            </select>
          </div>
          <div className="mb-3">
            <label htmlFor="profileYears" className="form-label">
              Roughly, <strong>how many years</strong> have you been
              professionally involved in cyber security?
            </label>
            <input
              required
              name="years"
              id="profileYears"
              defaultValue={formState.years ?? ""}
              type="number"
              min="0"
              max="100"
              className="form-control"
              onChange={handleInputChange}
            />
          </div>
          <div className="mb-3">
            <label htmlFor="profileRank" className="form-label">
              How would you describe{" "}
              <strong>your secure coding skill level</strong> at the moment?
            </label>
            <select
              required
              name="rank"
              id="profileRank"
              defaultValue={formState.rank ?? ""}
              className="form-select"
              onChange={handleInputChange}
            >
              <option value=""></option>
              <option value="none">
                None: What do you mean by secure coding?
              </option>
              <option value="little">
                Little: I only heard about a few concepts.
              </option>
              <option value="good">
                Good: I understand the essentials, but still need guidance
                sometimes.
              </option>
              <option value="advanced">
                Advanced: I apply secure coding concepts regularly and know
                where to go to learn more.
              </option>
              <option value="expert">
                Expert: I educate others about secure coding.
              </option>
            </select>
          </div>
          <div className="mb-3">
            <label htmlFor="profileNickname" className="form-label">
              Do you have a <strong>nickname</strong> that we should put on the
              leaderboard?
              <small className="ms-2 text-muted">
                You can also leave it empty or change it anytime.
              </small>
            </label>
            <input
              name="nickname"
              id="profileNickname"
              defaultValue={formState.nickname ?? ""}
              maxLength={100}
              className="form-control"
              onChange={handleInputChange}
            />
          </div>
          <div className="mb-5">
            <label htmlFor="profileColor" className="form-label">
              What's your <strong>favorite color?</strong>
            </label>
            <input
              type="color"
              name="color"
              id="profileColor"
              title="Choose your favorite color"
              defaultValue={formState.color}
              className="form-control form-control-color"
              onChange={handleInputChange}
            />
          </div>
          <div>
            <button type="submit" className="btn btn-primary me-2">
              Continue
            </button>
            {showAbort && (
              <button
                type="button"
                className="btn btn-secondary-outline"
                onClick={onAbort}
              >
                Abort profile changes
              </button>
            )}
          </div>
        </form>
      </div>
      <div className="card-footer text-muted">
        We will use your data to research differences in the response behavior
        between different professions and skill levels.
      </div>
    </div>
  );
}

export default ProfileCard;
