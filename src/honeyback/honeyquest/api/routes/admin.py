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

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse

from ...common.diagnostics import create_results_archive, enrich_settings
from ...common.models.admin import AuthToken, SizeItemsDict
from ...common.models.query import Query
from ..config import Settings, get_settings
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
# /admin ROUTES
###############################################################################


@router.post("/auth", status_code=status.HTTP_204_NO_CONTENT)
async def auth_admin(
    request: Request,
    token: AuthToken,
    sessions: UserSessionService = Depends(get_user_session_svc),
):
    """Authorizes the current user as an admin."""
    uid = request.session["uid"]
    if not sessions.auth_admin(uid, token.token):
        raise HTTPException(status_code=403, detail="invalid token")


@router.get("/results", response_class=FileResponse)
async def get_results(
    request: Request,
    sessions: UserSessionService = Depends(get_user_session_svc),
    settings: Settings = Depends(get_settings),
):
    """Returns the results directory as a zip archive."""
    _guard_admin_session(request, sessions)
    path = create_results_archive(settings)
    return FileResponse(path, media_type="application/zip", filename="results.zip")


@router.delete("/results", status_code=status.HTTP_204_NO_CONTENT)
async def clear_results(
    request: Request,
    sessions: UserSessionService = Depends(get_user_session_svc),
    persistence: PersistenceService = Depends(get_persistence_svc),
):
    """Clears the results directory."""
    _guard_admin_session(request, sessions)
    persistence.clear_results()


@router.post("/sync", status_code=status.HTTP_204_NO_CONTENT)
async def sync_response_cache(
    request: Request,
    sessions: UserSessionService = Depends(get_user_session_svc),
    persistence: PersistenceService = Depends(get_persistence_svc),
):
    """Re-hydrates the response cache from disk."""
    _guard_admin_session(request, sessions)
    persistence.sync_cache()


@router.get("/diagnostics/settings")
async def get_diagnostics_settings(
    request: Request,
    sessions: UserSessionService = Depends(get_user_session_svc),
    settings: Settings = Depends(get_settings),
) -> dict:
    _guard_admin_session(request, sessions)
    return enrich_settings(settings)


@router.get("/diagnostics/queries")
async def get_diagnostics_queries(
    request: Request,
    sessions: UserSessionService = Depends(get_user_session_svc),
    query_sampler: QuerySamplerService = Depends(get_query_sampler_svc),
) -> SizeItemsDict:
    _guard_admin_session(request, sessions)
    return query_sampler.get_diagnostics()


@router.get("/diagnostics/queries/{query_id}")
async def get_diagnostics_single_query(
    query_id: str,
    request: Request,
    sessions: UserSessionService = Depends(get_user_session_svc),
    query_sampler: QuerySamplerService = Depends(get_query_sampler_svc),
) -> Query:
    _guard_admin_session(request, sessions)
    if not query_sampler.exists_query(query_id):
        raise HTTPException(status_code=404, detail="query not found")
    return query_sampler._parse_query(query_id)


@router.get("/diagnostics/sessions")
async def get_diagnostics_sessions(
    request: Request,
    sessions: UserSessionService = Depends(get_user_session_svc),
) -> SizeItemsDict:
    _guard_admin_session(request, sessions)
    return sessions.get_diagnostics()


@router.get("/diagnostics/users")
async def get_diagnostics_users(
    request: Request,
    sessions: UserSessionService = Depends(get_user_session_svc),
    persistence: PersistenceService = Depends(get_persistence_svc),
) -> SizeItemsDict:
    _guard_admin_session(request, sessions)
    return persistence.get_diagnostics("users")


@router.get("/diagnostics/feedback")
async def get_diagnostics_feedback(
    request: Request,
    sessions: UserSessionService = Depends(get_user_session_svc),
    persistence: PersistenceService = Depends(get_persistence_svc),
) -> SizeItemsDict:
    _guard_admin_session(request, sessions)
    return persistence.get_diagnostics("feedback")


@router.get("/diagnostics/responses")
async def get_diagnostics_responses(
    request: Request,
    sessions: UserSessionService = Depends(get_user_session_svc),
    persistence: PersistenceService = Depends(get_persistence_svc),
) -> SizeItemsDict:
    _guard_admin_session(request, sessions)
    return persistence.get_diagnostics("responses")


###############################################################################
# helpers
###############################################################################


def _guard_admin_session(request: Request, sessions: UserSessionService):
    """Raises an HTTPException if the current session is not authorized as an admin."""
    uid = request.session["uid"]
    if not sessions.is_admin(uid):
        raise HTTPException(status_code=403, detail="not authorized")
