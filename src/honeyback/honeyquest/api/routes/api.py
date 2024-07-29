# Copyright 2024 Dynatrace LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Portions of this code, as identified in remarks, are provided under the
# Creative Commons BY-SA or the MIT license, and are provided without
# any warranty. In each of the remarks, we have provided attribution to the
# original creators and other attribution parties, along with the title of
# the code (if known) a copyright notice and a link to the license, and a
# statement indicating whether or not we have modified the code.

import logging
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ...common.models.feedback import FeedbackForApi, FeedbackForStorage
from ...common.models.metadata import Metadata
from ...common.models.query import (
    QueryBucketsWrapper,
    QueryResponseForApi,
    QueryResponseForStorage,
    QueryWrapper,
)
from ...common.models.user import User, UserProfile
from ..services.metadata import MetadataService, get_metadata_svc
from ..services.query import QuerySamplerService, get_query_sampler_svc
from ..services.sessions import (
    UserSessionService,
    call_user_session_svc,
    get_user_session_svc,
)
from ..services.storage import PersistenceService, get_persistence_svc

# reuse the uvicorn logger
log = logging.getLogger("uvicorn.error")

router = APIRouter(dependencies=[Depends(call_user_session_svc)])

###############################################################################
# /query + /metadata ROUTES
###############################################################################

# indicates that the user has exhausted all queries
ERR_OUT_OF_SAMPLES = "OUT_OF_SAMPLES"


@router.get("/query")
async def get_query(
    request: Request,
    query_sampler: QuerySamplerService = Depends(get_query_sampler_svc),
    persistence: PersistenceService = Depends(get_persistence_svc),
) -> QueryWrapper:
    """Serves queries to the frontend. Read QUERY_DATABASE.md for more."""
    uid = request.session["uid"]
    query = query_sampler.sample(uid)

    nanswered = persistence.get_number_of_answered_queries(uid)
    ntotal = query_sampler.get_number_of_queries()

    if not query:
        # no more queries left to sample
        raise HTTPException(
            status_code=404,
            detail=dict(
                code=ERR_OUT_OF_SAMPLES,
                answered_queries=nanswered,
                total_queries=ntotal,
            ),
        )

    return QueryWrapper(
        query=query,
        answered_queries=nanswered,
        total_queries=ntotal,
    )


@router.get("/query/buckets")
async def get_query_buckets(
    query_sampler: QuerySamplerService = Depends(get_query_sampler_svc),
) -> QueryBucketsWrapper:
    buckets = query_sampler.get_buckets()
    return QueryBucketsWrapper(buckets=buckets)


@router.get("/metadata/{metadata_id}")
async def get_metadata(
    metadata_id: str,
    text_format: Literal["html", "markdown"] = "html",
    metadata: MetadataService = Depends(get_metadata_svc),
) -> Metadata:
    """Serves metadata on queries to the frontend. Read QUERY_DATABASE.md for more."""
    payload = None
    if text_format == "markdown":
        payload = metadata.get_markdown(metadata_id)
    elif text_format == "html":
        payload = metadata.get_html(metadata_id)

    if not payload:
        raise HTTPException(status_code=404, detail=f"metadata id '{metadata_id}' not found")

    return payload


###############################################################################
# /response + /feedback ROUTES
###############################################################################


@router.post("/response", status_code=status.HTTP_204_NO_CONTENT)
async def receive_query_response(
    request: Request,
    response: QueryResponseForApi,
    query_sampler: QuerySamplerService = Depends(get_query_sampler_svc),
    persistence: PersistenceService = Depends(get_persistence_svc),
    sessions: UserSessionService = Depends(get_user_session_svc),
):
    """Stores query responses for the active user."""
    uid, qid = request.session["uid"], int(request.session["qid"])
    if sessions.is_rate_limited(uid):
        raise HTTPException(status_code=429)

    if not query_sampler.exists_query(response.query_id):
        raise HTTPException(status_code=404, detail=f"query id '{response.query_id}' not found")

    # reconstruct a self-contained query object and store that
    query = query_sampler.get_query(response.query_id)
    full_response = QueryResponseForStorage(uid=uid, qid=qid, query=query, answer=response.answer)
    persistence.store_response(uid, qid, full_response)


@router.post("/feedback", status_code=status.HTTP_204_NO_CONTENT)
async def receive_feedback(
    request: Request,
    feedback: FeedbackForApi,
    query_sampler: QuerySamplerService = Depends(get_query_sampler_svc),
    persistence: PersistenceService = Depends(get_persistence_svc),
    sessions: UserSessionService = Depends(get_user_session_svc),
):
    """Stores query responses for the active user."""
    uid, qid = request.session["uid"], int(request.session["qid"])
    if sessions.is_rate_limited(uid):
        raise HTTPException(status_code=429)

    # possibly attach the query object to the feedback, if available
    query = None
    if feedback.query_id:
        if query_sampler.exists_query(feedback.query_id):
            query = query_sampler.get_query(feedback.query_id)
        else:
            log.warning(f"got feedback for unknown query id {feedback.query_id}")

    # reconstruct a self-contained query object and store that
    full_feedback = FeedbackForStorage(uid=uid, qid=qid, answer=feedback.answer, query=query)
    persistence.store_feedback(uid, full_feedback)


###############################################################################
# /profile ROUTES
###############################################################################


@router.get("/profile")
async def get_profile(
    request: Request, persistence: PersistenceService = Depends(get_persistence_svc)
) -> Optional[UserProfile]:
    """Reads profile information on a user, if available."""
    uid = request.session["uid"]
    if not persistence.exists_user(uid):
        return None  # empty response, no error

    user = persistence.read_user(request.session["uid"])
    return user.profile


@router.put("/profile", status_code=status.HTTP_204_NO_CONTENT)
async def update_profile(
    request: Request,
    profile: UserProfile,
    persistence: PersistenceService = Depends(get_persistence_svc),
    sessions: UserSessionService = Depends(get_user_session_svc),
):
    """Creates or updates (idempotent) profile information for a user."""
    uid = request.session["uid"]
    if sessions.is_rate_limited(uid):
        raise HTTPException(status_code=429)

    user = User(uid=uid, profile=profile)
    persistence.store_user(user)


@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
async def clear_profile(request: Request):
    """Clears the profile information by removing the session cookie."""
    request.session.clear()
