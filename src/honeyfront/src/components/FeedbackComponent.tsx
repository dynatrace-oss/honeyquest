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

import { Modal, Toast } from "bootstrap";
import dayjs from "dayjs";
import { FormEvent, useCallback, useState } from "react";
import { useMutation, UseMutationResult } from "react-query";

import ErrorBanner from "./ErrorBanner";
import LoadingSpinner from "./LoadingSpinner";

import { IFeedback } from "../types/ApiTypes";
import { ApiError, postFeedback } from "../utils/Api";

declare interface IFeedbackComponentProps {
  modalId: string;
}

declare interface IFeedbackModalProps {
  modalId: string;
  mutation: UseMutationResult<boolean, unknown, IFeedback, unknown>;
  onSubmit: (message: string) => Promise<boolean>;
}

declare interface IFeedbackToastProps {
  toastId: string;
}

/**
 * Holds the feedback modal and handles feedback submission
 */
function FeedbackComponent(props: Readonly<IFeedbackComponentProps>) {
  const { modalId } = props;

  const mutation = useMutation(postFeedback, { retry: 6 });
  const handleSubmit = useCallback(
    (message: string) => {
      // the query id is stored in the modal's HTML data attribute
      const queryId = document.getElementById(modalId)?.dataset?.queryId;
      const feedback: IFeedback = {
        // eslint-disable-next-line @typescript-eslint/naming-convention
        query_id: queryId ?? null,
        answer: {
          timestamp: dayjs().toISOString(),
          message,
        },
      };
      return mutation.mutateAsync(feedback);
    },
    [mutation, modalId],
  );

  return (
    <FeedbackModal
      modalId={modalId}
      mutation={mutation}
      onSubmit={handleSubmit}
    />
  );
}

function FeedbackModal(props: Readonly<IFeedbackModalProps>) {
  const { modalId, mutation, onSubmit } = props;
  const successToastId = `${modalId}-toast`;

  const [message, setMessage] = useState("");
  const onFormSubmit = useCallback(
    async (event: FormEvent) => {
      event.preventDefault();
      try {
        if (await onSubmit(message)) {
          // dismiss modal
          const modal = document.getElementById(modalId);
          if (modal) Modal.getInstance(modal)?.hide();

          // show success toast
          const toast = document.getElementById(successToastId);
          if (toast) Toast.getOrCreateInstance(toast)?.show();

          // reset message
          setMessage("");
        }
      } catch (e) {
        console.error(e);
      }
    },
    [message, modalId, successToastId, onSubmit],
  );

  // prepare loading and error fragments
  const errorMessage =
    "Okay, that is super frustrating now. We are very sorry, please try again later.";
  const errorCard = <ErrorBanner error={new ApiError(errorMessage)} />;
  const loadingSpinner = <LoadingSpinner />;

  const modalBody = (
    <div className="mb-3">
      <label htmlFor="feedbackMessage" className="form-label">
        What is on your mind?
      </label>
      <textarea
        required
        rows={3}
        name="message"
        id="feedbackMessage"
        defaultValue={message}
        className="form-control"
        onChange={(e) => setMessage(e.target.value)}
      ></textarea>
    </div>
  );

  return (
    <>
      <div
        className="modal fade"
        id={modalId}
        tabIndex={-1}
        aria-labelledby="sendFeedbackModalLabel"
        aria-hidden="true"
      >
        <div className="modal-dialog">
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title" id="sendFeedbackModalLabel">
                Feedback
              </h5>
              <button
                type="button"
                className="btn-close"
                data-bs-dismiss="modal"
                aria-label="Close"
              ></button>
            </div>
            <form onSubmit={onFormSubmit}>
              <div className="modal-body">
                {mutation.isLoading ? loadingSpinner : null}
                {mutation.isError ? errorCard : null}
                {!mutation.isLoading && !mutation.isError ? modalBody : null}
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary-outline"
                  onClick={() => mutation.reset()}
                  data-bs-dismiss="modal"
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={mutation.isLoading || mutation.isError}
                  className="btn btn-primary"
                >
                  Submit feedback
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
      <FeedbackToast toastId={successToastId} />
    </>
  );
}

function FeedbackToast(props: Readonly<IFeedbackToastProps>) {
  const { toastId } = props;

  return (
    <div className="toast-container position-fixed top-0 start-50 translate-middle-x py-5">
      <div
        className="toast align-items-center text-bg-success border-0"
        id={toastId}
        role="alert"
        aria-live="assertive"
        aria-atomic="true"
      >
        <div className="d-flex">
          <div className="toast-body">
            <i className="bi bi-emoji-smile"></i>&nbsp;&nbsp;Thanks! We received
            your feedback.
          </div>
          <button
            type="button"
            className="btn-close btn-close-white me-2 m-auto"
            data-bs-dismiss="toast"
            aria-label="Close"
          ></button>
        </div>
      </div>
    </div>
  );
}

export default FeedbackComponent;
