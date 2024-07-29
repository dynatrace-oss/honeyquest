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
from collections import defaultdict
from datetime import datetime, timedelta
from functools import cache
from typing import Dict, Set, Tuple, TypedDict
from uuid import uuid4

from fastapi import Request

from ...common.models.admin import SizeItemsDict
from ...common.ratelimit import LeakyBucket
from ...common.timestamps import epoch_time
from ..config import get_settings

# reuse the uvicorn logger
log = logging.getLogger("uvicorn.error")


class SessionDict(TypedDict):
    """Stores the activity timestamps of a user session."""

    start_time: datetime
    last_seen: datetime


SessionType = Dict[str, Dict[int, SessionDict]]  # uid -> qid -> SessionDict
BucketType = Dict[str, LeakyBucket]  # uid -> LeakyBucket


class UserSessionService:
    """
    Ensures that all requests have a user (uid) and quest (qid) session identifier attached to them.

    A `SessionMiddleware` is needed to store this data in the client browser.

    - A user identifier (uid) identifies the browser.
    - A quest identifier (qid) identifies a run (or, session) through the questionnaire.

    UIDs are only cleared when the browser cookies are deleted or the user
    decides to clear his profile in the UI (which happens via an API call).

    QIDs will be reset when there was no interaction with the backend within
    the specified questionnaire session timeout. This is just a heuristic
    to cluster individual user sessions.
    """

    def __init__(
        self,
        session_timeout_mins: int,
        admin_token: str,
        api_burst_limit: int,
        api_rate_limit: float,
    ):
        self._session_timeout_mins = session_timeout_mins
        self._admin_token = admin_token
        self._api_burst_limit = api_burst_limit
        self._api_rate_limit = api_rate_limit
        self._admin_sessions: Set[str] = set()
        self._sessions: SessionType = defaultdict(dict)
        self._leaky_buckets: BucketType = defaultdict(
            lambda: LeakyBucket(self._api_burst_limit, self._api_rate_limit)
        )

    async def __call__(self, request: Request):
        """Sets and possibly refreshes the session cookie."""
        if not request.session:
            # no cookies yet, create new user session
            uid, qid = self._get_new_uid()
            request.session.update({"uid": uid, "qid": qid})
        else:
            # returning user, possibly update (or timeout) their session
            uid, qid = request.session["uid"], int(request.session["qid"])
            new_qid = self._keep_session_alive(uid)
            if qid != new_qid:
                request.session.update({"uid": uid, "qid": new_qid})

    def is_rate_limited(self, uid: str) -> bool:
        """
        Attempts to consume a rate-limited request for the given user id (uid).
        Returns `True` if the request was rate-limited and must be rejected.
        """
        return not self._leaky_buckets[uid].consume()

    def auth_admin(self, uid: str, token: str) -> bool:
        """If the supplied token matches, give the current user id (uid) admin privileges."""
        if token != self._admin_token:
            return False

        self._admin_sessions.add(uid)
        return True

    def is_admin(self, uid: str) -> bool:
        """Checks if this user id (uid) has admin privileges."""
        return uid in self._admin_sessions

    def get_diagnostics(self) -> SizeItemsDict:
        items = {k: SizeItemsDict(v) for k, v in self._sessions.items()}
        return SizeItemsDict(items)

    def _get_new_uid(self) -> Tuple[str, int]:
        """Creates a new random user id (uid) along with a quest id."""
        uid = str(uuid4())
        qid = self._get_new_qid(uid)
        return uid, qid

    def _get_new_qid(self, uid: str) -> int:
        """
        Creates a quest id (qid) by taking the current epoch time (in seconds).

        :param uid: The user identifier (uid) for which to create a new qid
        """
        now = datetime.utcnow()
        qid = epoch_time(now)
        self._sessions[uid][qid] = SessionDict(start_time=now, last_seen=now)
        return qid

    def _keep_session_alive(self, uid: str) -> int:
        """
        Updates the timestamp of the most recent quest id (qid) for this user id (uid).
        Sets the "last_seen" timestamp on the most recent quest id (qid) for
        this user id (uid) to the current time. Moreover, if the previously stored
        "last_seen" timestamp was too long ago, we time it out and create a new one.

        If this user has never been seen before, we assign it a quest id.

        This function will always return a valid quest id.

        :param uid: The user identifier (uid)
        :return: The current quest id, or a new one if it timed-out recently
        """
        if uid not in self._sessions or len(self._sessions[uid]) == 0:
            # a returning user that we do not have in the session store
            # let's keep their uid and only give them a new qid
            qid = self._get_new_qid(uid)
            return qid

        # grab the most recent qid of this user
        qid = max(self._sessions[uid].keys())

        # how long has it been since the last interaction?
        now = datetime.utcnow()
        delta = now - self._sessions[uid][qid]["last_seen"]
        delta_minutes = delta / timedelta(minutes=1)

        # possibly refresh qid on session timeouts
        if delta_minutes >= self._session_timeout_mins:
            qid = self._get_new_qid(uid)

        self._sessions[uid][qid]["last_seen"] = now
        return qid


@cache
def get_user_session_svc() -> UserSessionService:
    """Provides a singleton (cached instance) of `UserSessionService`."""
    settings = get_settings()
    assert settings.admin_token is not None
    return UserSessionService(
        settings.session_timeout_mins,
        settings.admin_token,
        settings.api_burst_limit,
        settings.api_rate_limit,
    )


async def call_user_session_svc(request: Request):
    # invokes the callable of the cached service singleton
    return await get_user_session_svc()(request)
