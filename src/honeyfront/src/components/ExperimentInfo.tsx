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

import "./ExperimentInfo.css";

declare interface IExperimentInfoProps {
  disabled?: boolean;
}

/**
 * Shows a notification bar about the current experiment.
 * Experiments can be identified by an alternative host name.
 */
function ExperimentInfo(props: Readonly<IExperimentInfoProps>) {
  const { disabled } = props;
  if (disabled) {
    return null;
  }

  const canonicalHost = "honeyquest.yourdomain.test";
  if (window.location.host === canonicalHost) {
    return null;
  }

  return (
    <div
      className="ExperimentInfo alert alert-primary d-flex align-items-center"
      role="alert"
    >
      <div>
        <i className="bi bi-info-circle"></i>&nbsp;&nbsp;You are participating
        in a controlled research experiment. If you want to revisit or share
        this app later, please go to{" "}
        <a href={`https://${canonicalHost}`}>
          <strong>{canonicalHost}</strong>
        </a>{" "}
        instead.
      </div>
    </div>
  );
}

export default ExperimentInfo;
