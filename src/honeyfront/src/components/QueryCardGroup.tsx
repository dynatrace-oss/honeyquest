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

import dayjs from "dayjs";
import duration from "dayjs/plugin/duration";
import { useCallback } from "react";
import { useMutation, useQuery, useQueryClient } from "react-query";

import ErrorBanner from "./ErrorBanner";
import MetadataCard from "./MetadataCard";
import QueryCard from "./QueryCard";

import {
  IApiErrorOutOfSamples,
  IMetadata,
  IQueryResponse,
  IQueryWrapper,
} from "../types/ApiTypes";
import { FEEDBACK_MODAL_ID, QAnnotation, SelLine } from "../types/Common";
import {
  ApiError,
  getQuery,
  getQueryMetadata,
  mapSelectionType,
  postAnswer,
} from "../utils/Api";
import { grabKey } from "../utils/Utils";
import EndCard from "./EndCard";

dayjs.extend(duration);

export declare interface IProgress {
  active: boolean;
  answered: number;
  total: number;
}

declare interface IQueryCardGroupProps {
  showDetails: boolean;
  fetchMetadata: boolean;
  onSubmit: (response: IQueryResponse, endOfTutorial: boolean) => boolean;
  onProgressChange: (progress: IProgress) => void;
}

/**
 * Groups query and metadata cards and holds the
 * logic to fetch queries and associated metadata.
 *
 * The `onSubmit` callback returns you a `{query, answer}` in its parameters
 * and expects you to return `true` to indicate that the next query shall be fetched.
 */
function QueryCardGroup(props: Readonly<IQueryCardGroupProps>) {
  const queryClient = useQueryClient();
  const { showDetails, fetchMetadata, onSubmit, onProgressChange } = props;

  // callback handler that updates an upstream progress bar
  const propagateProgress = useCallback(
    (data: IQueryWrapper | undefined, error: ApiError | null) => {
      if (error !== null || (data && data.query.type === "tutorial"))
        onProgressChange({ active: false, answered: 0, total: 0 });
      else if (data)
        onProgressChange({
          active: true,
          answered: data.answered_queries,
          total: data.total_queries,
        });
    },
    [onProgressChange],
  );

  // fetch the next query from the backend
  const {
    data: qData,
    error: qError,
    isSuccess: qIsSuccess,
    dataUpdatedAt: qTimestamp,
  } = useQuery<IQueryWrapper, ApiError>("query", getQuery, {
    staleTime: 10 * 60 * 1000 /* 10 minutes */,
    refetchOnMount: true,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    onSettled: propagateProgress,
  });

  // (optional) fetch the metadata for the current query if the annotation is present
  const metaRef =
    qData?.query.references.filter((e) => "metaref" in e)[0]?.metaref ?? "";
  const {
    data: mData,
    error: mError,
    isSuccess: mIsSuccess,
  } = useQuery<IMetadata, ApiError>(
    ["metadata", metaRef],
    () => getQueryMetadata(String(metaRef)),
    {
      enabled: fetchMetadata && Boolean(metaRef),
      staleTime: 10 * 60 * 1000 /* 10 minutes */,
      refetchOnMount: true,
      refetchOnWindowFocus: false,
      refetchOnReconnect: false,
    },
  );

  // check if this is the last query of a tutorial
  // because that needs special navigation
  const endOfTutorial = qData
    ? grabKey(QAnnotation.TutorialEnd, qData.query.annotations, Boolean, false)
    : false;

  // send the answer to the backend
  const { mutate, isLoading: rIsLoading } = useMutation(postAnswer, {
    retry: 6,
    onMutate: () =>
      queryClient.invalidateQueries("query", { refetchActive: false }),
    onSuccess: (_, variables) => {
      if (onSubmit(variables, endOfTutorial)) {
        void queryClient.invalidateQueries("query", { refetchActive: true });
      }
    },
  });

  // TODO: TR-547 is this useCallback correct here?
  const onClickCallback = useCallback(
    (lines: SelLine[]) => {
      const responseTimeMs =
        qTimestamp > 0 ? dayjs().diff(dayjs(qTimestamp)) : 0;
      /* eslint-disable @typescript-eslint/naming-convention */
      const response: IQueryResponse = {
        query_id: qData!.query.id,
        answer: {
          lines: mapSelectionType(lines),
          timestamp: dayjs().toISOString(),
          response_time: dayjs.duration(responseTimeMs).toISOString(),
        },
      };
      mutate(response);
    },
    [mutate, qData, qTimestamp],
  );

  // TR-547: use proper state management
  // very hacky way to pass the query id to the feedback modal
  const feedbackModal = document.getElementById(FEEDBACK_MODAL_ID);
  if (feedbackModal) feedbackModal.dataset.queryId = qData?.query.id ?? "";

  if (qError?.isOfType("OUT_OF_SAMPLES")) {
    const qErrorData = qError.data as IApiErrorOutOfSamples;
    const numQueries = qErrorData.detail.answered_queries ?? 0;
    return <EndCard numQueries={numQueries} />;
  }

  if (qError) return <ErrorBanner error={qError} />;
  if (mError) return <ErrorBanner error={mError} />;

  return (
    <div className="card-group">
      <QueryCard
        query={qData?.query ?? null}
        invalid={!qIsSuccess || rIsLoading}
        showDetails={showDetails}
        animateCode={!showDetails}
        onClick={onClickCallback}
      />
      {mIsSuccess && <MetadataCard {...mData} />}
    </div>
  );
}

export default QueryCardGroup;
