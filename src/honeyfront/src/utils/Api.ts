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

/* eslint-disable @typescript-eslint/no-explicit-any */

import {
  IApiError,
  IApiErrorTypeCode,
  IDiagnosticsSettings,
  IDiagnosticsSizeItems,
  IFeedback,
  ILineAnswerV2,
  IMetadata,
  IProfile,
  IQuery,
  IQueryBucketsWrapper,
  IQueryResponse,
  IQueryWrapper,
} from "../types/ApiTypes";
import { SelLine, SelType } from "../types/Common";

/**
 * The API can often give us additional error
 * details in a JSON object. This class can be
 * used to access that object, but it also will
 * allows offer a string representation as well.
 */
export class ApiError extends Error {
  isJson: boolean;
  data: any;

  constructor(data: string | object | undefined) {
    const isJson = typeof data === "object";
    const message = isJson ? JSON.stringify(data) : data;
    super(message);

    this.isJson = isJson;
    this.data = isJson ? data : undefined;
    this.name = this.constructor.name;
  }

  /**
   * Tests if the error type matches.
   *
   * @param type The type to check for
   * @returns True if the type is present
   */
  isOfType(type: IApiErrorTypeCode): boolean {
    try {
      const typedData = this.data as IApiError;
      if (!this.isJson || !typedData) return false;
      return (
        Object.keys(typedData).includes("detail") &&
        Object.keys(typedData.detail).includes("code") &&
        typedData.detail.code === type
      );
    } catch (e) {
      return false;
    }
  }
}

export async function getQuery(): Promise<IQueryWrapper> {
  return getJson("/api/query") as Promise<IQueryWrapper>;
}

export async function getQueryBuckets(): Promise<IQueryBucketsWrapper> {
  return getJson("/api/query/buckets") as Promise<IQueryBucketsWrapper>;
}

export async function getQueryMetadata(metadataId: string): Promise<IMetadata> {
  return getJson(`/api/metadata/${metadataId}`, {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    text_format: "markdown",
  }) as Promise<IMetadata>;
}

export async function getProfile(): Promise<IProfile> {
  return getJson("/api/profile") as Promise<IProfile>;
}

export async function putProfile(profile: IProfile): Promise<boolean> {
  return postJson("/api/profile", profile, "PUT");
}

export async function deleteProfile(): Promise<boolean> {
  return postJson("/api/profile", null, "DELETE");
}

export async function deleteAdminResults(): Promise<boolean> {
  return postJson("/api/admin/results", null, "DELETE");
}

export async function postAdminSync(): Promise<boolean> {
  return postJson("/api/admin/sync", null);
}

export async function getAdminDiagnosticsSettings(): Promise<IDiagnosticsSettings> {
  return getJson(
    "/api/admin/diagnostics/settings",
  ) as Promise<IDiagnosticsSettings>;
}

export async function getAdminDiagnosticsQueries(): Promise<IDiagnosticsSizeItems> {
  return getJson(
    "/api/admin/diagnostics/queries",
  ) as Promise<IDiagnosticsSizeItems>;
}

export async function getAdminDiagnosticsQuery(
  queryId: string,
): Promise<IQuery> {
  return getJson(
    `/api/admin/diagnostics/queries/${queryId}`,
  ) as Promise<IQuery>;
}

export async function getAdminDiagnosticsSessions(): Promise<IDiagnosticsSizeItems> {
  return getJson(
    "/api/admin/diagnostics/sessions",
  ) as Promise<IDiagnosticsSizeItems>;
}

export async function getAdminDiagnosticsUsers(): Promise<IDiagnosticsSizeItems> {
  return getJson(
    "/api/admin/diagnostics/users",
  ) as Promise<IDiagnosticsSizeItems>;
}

export async function getAdminDiagnosticsFeedback(): Promise<IDiagnosticsSizeItems> {
  return getJson(
    "/api/admin/diagnostics/feedback",
  ) as Promise<IDiagnosticsSizeItems>;
}

export async function getAdminDiagnosticsResponses(): Promise<IDiagnosticsSizeItems> {
  return getJson(
    "/api/admin/diagnostics/responses",
  ) as Promise<IDiagnosticsSizeItems>;
}

export async function postAnswer(params: IQueryResponse): Promise<boolean> {
  return postJson("/api/response", params);
}

export async function postFeedback(params: IFeedback): Promise<boolean> {
  return postJson("/api/feedback", params);
}

export async function postAdminAuth(token: string): Promise<boolean> {
  return postJson("/api/admin/auth", { token });
}

/**
 * Returns a Promise that parses the result from `fetch()` to JSON.
 * Rejects the Promise on error and returns the text-based error message.
 */
export async function getJson(url: string, params?: any): Promise<any> {
  let fullUrl = url;
  if (params) {
    // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
    fullUrl = `${url}?${new URLSearchParams(params).toString()}`;
  }

  return fetch(fullUrl).then(async (res) => {
    if (res.ok) return res.json();
    throw new ApiError(await tryParseJsonResponse(res));
  });
}

/**
 * Posts data as JSON to some URL with `fetch()`. Returns true if the request was successful.
 * Rejects the Promise on error with the text-based error message.
 */
export async function postJson(
  url: string,
  data?: any,
  method = "POST",
): Promise<boolean> {
  return fetch(url, {
    method,
    cache: "no-cache",
    // eslint-disable-next-line @typescript-eslint/naming-convention
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  }).then(async (res) => {
    if (res.ok) return true;
    throw new ApiError(await tryParseJsonResponse(res));
  });
}

/**
 * Trys to parse a response as JSON, otherwise returns the text.
 *
 * @param res The response object
 * @returns The parsed JSON object or the text
 */
async function tryParseJsonResponse(res: Response): Promise<string | object> {
  const text = await res.text();
  try {
    return JSON.parse(text) as object;
  } catch (e) {
    return text;
  }
}

export function mapSelectionType(lines: SelLine[]): ILineAnswerV2[] {
  return lines.map((line) => {
    const num = line[0];
    const type = line[1] === SelType.Hack ? "hack" : "trap";
    return [num, type];
  });
}
