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

import HoneyquestLogo from "../images/HoneyquestLogo.svg";

import "./HoneyquestLead.css";

declare interface IHoneyquestLeadProps {
  /** The callback to invoke when the start button is clicked */
  onStart: () => void;
  /** The callback to invoke when the admin panel button is clicked */
  onAdmin: () => void;
  /** Possibly shows the intro text along with the logo */
  showIntro: boolean;
  /** Shows a summary text for people that already played the tutorial */
  showSummary: boolean;
  /** Possibly show a button for the admin panel */
  showAdmin: boolean;
  /** Possibly show the data privacy statement */
  showDataPrivacy: boolean;
}

/**
 * Holds the lead text, used to kick-off the questionnaire.
 */
function HoneyquestLead(props: Readonly<IHoneyquestLeadProps>) {
  const {
    onStart,
    onAdmin,
    showIntro,
    showSummary,
    showAdmin,
    showDataPrivacy,
  } = props;

  const introFragment = (
    <div>
      <p className="lead">
        Honeyquest is a game where you have to identify security vulnerabilities
        in web applications. Be careful, some of the vulnerabilities are traps
        trying to trick you into thinking something is vulnerable.
      </p>
    </div>
  );

  const summaryFragment = (
    <div>
      <h4 className="mt-4 mb-4">Game Summary</h4>
      <div>
        <p className="lead">
          Honeyquest shows you{" "}
          <strong>
            <mark>neutral</mark> or <mark>risky</mark> or <mark>deceptive</mark>
          </strong>{" "}
          queries.
        </p>
        <p className="lead">
          Think like a hacker and tell us your <strong>next&nbsp;move</strong>.
        </p>
        <ul className="mb-3 text-muted">
          <li>
            You can{" "}
            <strong>
              <i className="bi bi-caret-right-fill"></i>&nbsp;continue
            </strong>{" "}
            without marking anything
          </li>
          <li>
            You can mark lines to{" "}
            <strong>
              <i className="bi bi-lightning-fill"></i>&nbsp;exploit
            </strong>{" "}
            or mark them as a{" "}
            <strong>
              <i className="bi bi-pin-angle-fill"></i>&nbsp;trap
            </strong>{" "}
            to avoid
          </li>
          <li>
            You can indicate the order in which you would like to exploit
            something
          </li>
        </ul>
        <p className="lead">
          You can answer as many questions as you like and come back later.
          Honeyquest saves your progress automatically.
        </p>
      </div>
    </div>
  );

  const dataPrivacyFragment = (
    <div>
      <h4 className="mt-4 mb-4">Data Privacy Consent for Research Purposes</h4>
      <div>
        <p>
          During the game, we will collect some data to help us advance research
          on cyber deception. This includes:
        </p>
        <ul>
          <li className="mb-3">
            We store <mark>a cookie</mark> on your computer to identify you.
            <br />
            <i className="text-muted">
              Why? So that we know which answers belong to the same person and
              we change the difficulty level individually, even when you
              continue the game later.
            </i>
          </li>
          <li className="mb-3">
            We store <mark>your profile information</mark>, like your job, years
            of experience, and skill level.
            <br />
            <i className="text-muted">
              Why? So that we can research, if there are differences among
              different professions and skill levels.
            </i>
          </li>
          <li className="mb-3">
            We store <mark>your answers</mark> and the time of your answers.
            <br />
            <i className="text-muted">
              Why? So that we can research what kinds of questions humans are
              good at answering and what kinds of questions are hard for humans,
              or even impossible to get right.
            </i>
          </li>
          <li className="mb-3">
            We do not store your IP address, location, name, email address, or
            any other PII.
            <br />
            <i className="text-muted">
              Why? Because we don't need it and think data privacy is important.
            </i>
          </li>
        </ul>
      </div>
    </div>
  );

  const adminFragment = (
    <button
      type="button"
      className="btn btn-sm btn-outline-secondary ms-3 mb-1"
      style={{ border: "none" }}
      onClick={onAdmin}
    >
      Admin Panel
    </button>
  );

  return (
    <div>
      <h1>
        <img className="honeyquest-logo" src={HoneyquestLogo} alt="Logo" />
        Honeyquest {showAdmin && adminFragment}
      </h1>
      {showIntro && introFragment}
      {showSummary && summaryFragment}
      {showDataPrivacy && dataPrivacyFragment}
      {(showIntro || showDataPrivacy) && (
        <button
          type="button"
          className="btn btn-primary mt-4"
          onClick={onStart}
        >
          {showDataPrivacy
            ? "Agree, please bring me to the game"
            : "Continue the game"}
        </button>
      )}
    </div>
  );
}

export default HoneyquestLead;
