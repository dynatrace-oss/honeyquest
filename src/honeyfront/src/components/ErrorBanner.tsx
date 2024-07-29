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

import { ApiError } from "../utils/Api";

declare interface IErrorBannerProps {
  /** The error message to display */
  error: ApiError;
}

/**
 * Shows an error message along with a cat image.
 */
function ErrorBanner(props: Readonly<IErrorBannerProps>) {
  const { error } = props;

  const message = error.isJson
    ? JSON.stringify(error.data, null, 2)
    : error.message;

  return (
    <div className="row alert alert-danger m-1" role="alert">
      <div className="col-lg-6">
        <p>
          <strong>Sorry, something went wrong.</strong> Please refresh the page
          or try again later.
          <br />
        </p>
        <code>
          <pre style={{ whiteSpace: "pre-wrap" }}>{message}</pre>
        </code>
      </div>
      <div className="col-lg-6">
        <img
          src="https://cataas.com/cat/cute"
          alt="A cute cat"
          className="img-fluid"
          style={{ maxHeight: "20em" }}
        />
      </div>
    </div>
  );
}

export default ErrorBanner;
