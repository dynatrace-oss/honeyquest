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

# pylint: disable=missing-class-docstring

from textwrap import dedent
from typing import List

import pytest
from honeypatch.filters.httpheader import HttpHeaderFilter
from honeypatch.models.httpheader import HeaderOp, HttpHeaderHoney
from loguru import logger as log


class TestHttpHeaderBase:
    @pytest.fixture
    def caplog(self, caplog):
        # suppress default loggers and override caplog to capture loguru logs
        # https://github.com/Delgan/loguru/issues/59#issuecomment-1016516449
        log.remove()
        handler_id = log.add(caplog.handler, format="{message}")
        yield caplog
        log.remove(handler_id)

    @pytest.fixture
    def empty_filter(self):
        # a httpheader filter without any operations
        return self._build_filter([])

    @staticmethod
    def _build_filter(operations: List[HeaderOp]):
        return HttpHeaderFilter(
            HttpHeaderHoney(
                name="test-httpheader",
                description="This honeywire is only used for unit tests",
                kind="httpheader",
                operations=operations,
            )
        )


class TestHttpHeaderValidate(TestHttpHeaderBase):
    def test_http_response(self, empty_filter):
        # note the lstrip so that we keep trailing whitespace
        data = dedent(
            """
            HTTP/1.1 200 OK
            Date: Mon, 23 May 2005 22:38:34 GMT
            Content-Type: text/html; charset=UTF-8
            Content-Length: 155
            Last-Modified: Wed, 08 Jan 2003 23:11:55 GMT
            Server: Apache/1.3.3.7 (Unix) (Red-Hat/Linux)
            ETag: "3f80f-1b6-3e1cb03b"
            Accept-Ranges: bytes
            Connection: close
            """
        ).lstrip()

        assert empty_filter.validate(data).result

    def test_http_request(self, empty_filter):
        # note the lstrip so that we keep trailing whitespace
        data = dedent(
            """
            GET / HTTP/1.1
            Host: www.example.com
            User-Agent: Mozilla/5.0
            """
        ).lstrip()

        assert not empty_filter.validate(data).result


class TestHttpHeaderFilter(TestHttpHeaderBase):
    def test_no_modifications(self, empty_filter, caplog):
        data = dedent(
            """
            HTTP/1.1 302 Found
            Connection: keep-alive
            """
        ).lstrip()

        empty_filter.filter(data)
        assert "did not modify" in caplog.text

    def test_add_header(self):
        obj = self._build_filter([HeaderOp(op="add", key="New-Header", value="new value")])

        data = dedent(
            """
            HTTP/1.1 200 OK
            Content-Type: text/html; charset=UTF-8
            """
        ).lstrip()

        result = dedent(
            """
            HTTP/1.1 200 OK
            Content-Type: text/html; charset=UTF-8
            New-Header: new value
            """
        ).lstrip()

        assert obj.filter(data) == result

    def test_add_header_existing(self, caplog):
        obj = self._build_filter(
            [HeaderOp(op="add", key="Connection", value="keep-alive")],
        )

        data = dedent(
            """
            HTTP/1.1 200 OK
            Connection: close
            """
        ).lstrip()

        # existing headers must not be overwritten
        assert obj.filter(data) == data
        assert "can not add" in caplog.text

    def test_add_header_existing_case_insensitive(self, caplog):
        obj = self._build_filter(
            [HeaderOp(op="add", key="connection", value="keep-alive")],
        )

        data = dedent(
            """
            HTTP/1.1 204 No Content
            Connection: close
            """
        ).lstrip()

        # existing headers must not be overwritten (even if written case-insensitive)
        assert obj.filter(data) == data
        assert "can not add" in caplog.text

    def test_remove_header(self):
        obj = self._build_filter([HeaderOp(op="remove", key="Content-Length")])

        data = dedent(
            """
            HTTP/1.1 200 OK
            Content-Type: text/html; charset=UTF-8
            Content-Length: 155
            """
        ).lstrip()

        result = dedent(
            """
            HTTP/1.1 200 OK
            Content-Type: text/html; charset=UTF-8
            """
        ).lstrip()

        assert obj.filter(data) == result

    def test_remove_header_case_insensitive(self):
        obj = self._build_filter([HeaderOp(op="remove", key="content-length")])

        data = dedent(
            """
            HTTP/1.1 201 Created
            Content-Type: text/html; charset=UTF-8
            Content-Length: 155
            """
        ).lstrip()

        result = dedent(
            """
            HTTP/1.1 201 Created
            Content-Type: text/html; charset=UTF-8
            """
        ).lstrip()

        assert obj.filter(data) == result

    def test_remove_header_missing(self, caplog):
        obj = self._build_filter(
            [HeaderOp(op="remove", key="Connection")],
        )

        data = dedent(
            """
            HTTP/1.1 201 Created
            Content-Type: text/html; charset=UTF-8
            """
        ).lstrip()

        # missing headers can not be removed
        assert obj.filter(data) == data
        assert "can not remove" in caplog.text

    def test_replace_header(self):
        obj = self._build_filter(
            [HeaderOp(op="replace", key="Server", value="replaced value")],
        )

        data = dedent(
            """
            HTTP/1.1 200 OK
            Server: Apache/1.3.3.7 (Unix) (Red-Hat/Linux)
            """
        ).lstrip()

        result = dedent(
            """
            HTTP/1.1 200 OK
            Server: replaced value
            """
        ).lstrip()

        assert obj.filter(data) == result

    def test_replace_header_case_insensitive(self):
        obj = self._build_filter(
            [HeaderOp(op="replace", key="server", value="replaced value")],
        )

        data = dedent(
            """
            HTTP/1.1 201 Created
            Server: Apache/1.3.3.7 (Unix) (Red-Hat/Linux)
            """
        ).lstrip()

        result = dedent(
            """
            HTTP/1.1 201 Created
            Server: replaced value
            """
        ).lstrip()

        assert obj.filter(data) == result

    def test_replace_header_missing(self, caplog):
        obj = self._build_filter(
            [HeaderOp(op="replace", key="Connection")],
        )

        data = dedent(
            """
            HTTP/1.1 202 Accepted
            Content-Type: text/html; charset=UTF-8
            """
        ).lstrip()

        # missing headers can not be replaced
        assert obj.filter(data) == data
        assert "can not replace" in caplog.text
