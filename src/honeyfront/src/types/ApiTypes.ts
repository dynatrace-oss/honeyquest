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

/* eslint-disable @typescript-eslint/naming-convention */

/**
 * Query format as documented in the QUERY_DATABASE.md document.
 */
export declare interface IQuery {
  /** The ID of the query */
  id: string;
  /** The true label of the query */
  label: "neutral" | "risky" | "deceptive" | null;
  /** The type of the query */
  type: string;
  /** An optional list of key-value pairs referencing metadata */
  references: QueryKVType[];
  /** An optional list of key-value pairs highlighting code fragments */
  annotations: QueryKVType[];
  /** The query payload */
  data: string;
}

export declare interface IQueryWrapper {
  /** The query object */
  query: IQuery;
  /** The number of queries answered by the user */
  answered_queries: number;
  /** The total number of queries in the dataset */
  total_queries: number;
}

export declare interface IQueryBucket {
  /** The internal name of this bucket */
  name: string;
  /** The description of this bucket for the UI */
  description: string;
  /** The internal sampling strategy for this bucket */
  strategy: "sorted" | "random";
  /** The number of queries in that bucket */
  query_size: number;
}

export declare interface IQueryBucketsWrapper {
  /** A list of buckets, or null if no bucket order was specified */
  buckets: IQueryBucket[] | null;
}

export type QueryKVType = Record<string, boolean | number | string | null>;

/**
 * Metadata format as documented in the QUERY_DATABASE.md document.
 */
export declare interface IMetadata {
  /** The ID of the metadata entry */
  id: string;
  /** A descriptive title of the metadata entry */
  title: string;
  /** A list of links to external resources */
  references: string[];
  /** Classification according to security ontologies */
  classification: { cwe?: string[]; capec?: string[]; owasp?: string[] };
  /** A Markdown description of the metadata entry */
  text: string;
}

/**
 * Query response as documented in the models/query.py file.
 */
export declare interface IQueryResponse {
  /** The ID of the original query to answer */
  query_id: string;
  answer: IQueryAnswer;
}

/**
 * Query answer as documented in the models/query.py file.
 */
export declare interface IQueryAnswer {
  /** The timestamp when the answer was submitted, as an ISO 8601 string */
  timestamp: string;
  /** Line numbers (starting at 1) that the user marked in the query, in order */
  lines: ILineAnswerV2[];
  /** The time it took the user to respond as an ISO 8601 time delta */
  response_time: string;
}

export type ILineAnswerV2 = [number, "hack" | "trap"];

/**
 * User feedback as documented in the models/feedback.py file.
 */
export declare interface IFeedback {
  /** The ID of the original query to answer */
  query_id: string | null;
  answer: IFeedbackAnswer;
}

/**
 * Feedback answer as documented in the models/feedback.py file.
 */
export declare interface IFeedbackAnswer {
  /** The message the user provided in the feedback */
  message: string;
  /** The timestamp when the feedback was submitted, as an ISO 8601 string */
  timestamp: string;
}

/**
 * The user profile.
 */
export declare interface IProfile {
  nickname: string | null;
  job: IProfileJob | null;
  years: number | null;
  rank: IProfileRank | null;
  color: string;
}

export type IProfileJob =
  | "student"
  | "dev"
  | "ops"
  | "secops"
  | "biz"
  | "research"
  | "other";
export type IProfileRank = "none" | "little" | "good" | "advanced" | "expert";

export type IDiagnosticsSettings = Record<string, string>;

export declare interface IDiagnosticsSizeItems {
  size: number;
  items: object;
}

export type IApiErrorTypeCode = "OUT_OF_SAMPLES";

export declare interface IApiError {
  status_code: number;
  detail: {
    code: IApiErrorTypeCode;
  };
}
export declare interface IApiErrorOutOfSamples {
  status_code: number;
  detail: {
    code: "OUT_OF_SAMPLES";
    answered_queries: number;
    total_queries: number;
  };
}
