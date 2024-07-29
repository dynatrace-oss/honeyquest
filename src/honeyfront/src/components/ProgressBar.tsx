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

import { useMemo } from "react";
import { useQuery } from "react-query";

import { IProgress } from "./QueryCardGroup";
import Tooltip from "./Tooltip";
import { ApiError, getQueryBuckets } from "../utils/Api";

import "./ProgressBar.css";
import { IQueryBucketsWrapper } from "../types/ApiTypes";

declare interface IProgressBarProps {
  progress: IProgress;
  color?: string;
}

/**
 * Tells the user that he there are no more queries to show.
 */
function ProgressBar(props: Readonly<IProgressBarProps>) {
  const { progress, color } = props;
  const bgColor = color ?? "#212529";
  const bgColorInactive = "#e9ecef";

  // fetch and cache the bucket order from the backend
  const { data } = useQuery<IQueryBucketsWrapper, ApiError>(
    "buckets",
    getQueryBuckets,
    {
      staleTime: 60 * 60 * 1000 /* 60 minutes */,
      refetchOnMount: true,
      refetchOnWindowFocus: false,
      refetchOnReconnect: false,
    },
  );

  const tooltips: JSX.Element[] = useMemo(() => {
    if (!data?.buckets) return [];

    const fragments: JSX.Element[] = [];
    let cumSize = 0;
    let prevDescription = null;

    for (const bucket of data.buckets) {
      cumSize += bucket.query_size;
      const leftPercent = (cumSize / progress.total) * 100;
      const color = progress.answered < cumSize ? bgColorInactive : bgColor;

      // auto-merge descriptions that are equal
      if (!prevDescription || prevDescription !== bucket.description) {
        const tooltipText =
          `${bucket.description} (+ ${bucket.query_size} queries) is done` +
          ` after answering ${cumSize} queries`;
        fragments.push(
          <Tooltip text={tooltipText} key={bucket.name} placement="top">
            <i
              className="TargetIcon bi bi-geo-alt-fill"
              style={{ color, left: `${leftPercent}%` }}
            ></i>
          </Tooltip>,
        );
      }

      prevDescription = bucket.description;
    }
    return fragments;
  }, [data, bgColor, progress]);

  return (
    <div className="ProgressBar d-flex align-items-center">
      <div className="ms-auto pe-3 text-muted small">
        {`${progress.answered} / ${progress.total}`}
      </div>
      <div className="progress flex-fill">
        <progress
          className="progress-bar"
          aria-label="Example with label"
          aria-valuenow={progress.answered}
          aria-valuemin={0}
          aria-valuemax={progress.total}
          style={{
            width: `${(progress.answered / progress.total) * 100}%`,
            background: bgColor,
          }}
        ></progress>
        {tooltips}
      </div>
    </div>
  );
}

export default ProgressBar;
