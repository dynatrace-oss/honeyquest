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

import TeamLogo from "../images/TeamLogo.svg";

import "./Footer.css";

/**
 * Shows the page footer
 */
function Footer() {
  return (
    <footer className="footer bg-light mt-auto py-3">
      <div className="container">
        <span className="text-muted small">
          Honeyquest is free and open-source.{" "}
          <a
            href="https://github.com/dynatrace-oss/honeyquest"
            target="_blank"
            rel="noreferrer"
          >
            <span className="ms-3">
              <i className="bi bi-github"></i> dynatrace-oss/honeyquest
            </span>
          </a>
          <a
            href="https://infosec.exchange/@blu3r4y"
            target="_blank"
            rel="noreferrer"
          >
            <span className="ms-4">
              <i className="bi bi-mastodon"></i> blu3r4y
            </span>
          </a>
          <a href="https://x.com/blu3r4y_at" target="_blank" rel="noreferrer">
            <span className="ms-4">
              <i className="bi bi-twitter-x"></i> blu3r4y_at
            </span>
          </a>
        </span>
        <span className="TeamLabel text-muted small">
          <img
            className="d-inline-block align-text-top"
            src={TeamLogo}
            alt="logo"
            height="24"
          />
        </span>
      </div>
    </footer>
  );
}

export default Footer;
