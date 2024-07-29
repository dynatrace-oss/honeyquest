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

import re
from typing import Dict, Optional, Set

from dagster import (
    SolidExecutionContext,
    get_dagster_logger,
    job,
    make_values_resource,
    op,
)

from ...common.models.query import Query
from ..config import get_cached_config
from ..ops.loading import parse_all_queries

log = get_dagster_logger()


RISK_TYPE = "risk/type"
RISKY_LINES = "risk/risky-lines"
RISKY_ANNOTATIONS = {
    RISK_TYPE,
    RISKY_LINES,
    "risk/description",
}

PRESENT_WEAKNESS = "risk/present-weakness"
PRESENT_VULNERABILITY = "risk/present-vulnerability"
PRESENT_ATTACK = "risk/present-attack"
RISKY_ANNOTATIONS_AT_LEAST_ONE = {
    PRESENT_WEAKNESS,
    PRESENT_VULNERABILITY,
    PRESENT_ATTACK,
}

DECEPTIVE_LINES = "honeypatch/deceptive-lines"
ORIGINAL_QUERY = "honeypatch/original-query"
APPLIED_HONEYWIRE = "honeypatch/applied-honeywire"
DECEPTIVE_ANNOTATIONS = {
    DECEPTIVE_LINES,
    ORIGINAL_QUERY,
    APPLIED_HONEYWIRE,
    "honeypatch/description",
}

TUTORIAL_ANNOTATIONS = {
    "honeyquest/tutorial-end",
}

THREAT_TYPES = {
    "vulnerability",
    "weakness",
    "attack",
}

# extra annotations that might be set on deceptive queries
ORIGINAL_RISKY = "honeypatch/original-risky"
HONEYPATCH_ANNOTATIONS = {
    ORIGINAL_RISKY,
    RISKY_LINES,
}

ALLOW_LINES = "honeyquest/allow-lines"
HONEYQUEST_ANNOTATIONS = {
    "honeyquest/button-text",
    "honeyquest/select",
    "honeyquest/select-hacks",
    "honeyquest/select-traps",
    "honeyquest/max-hacks",
    "honeyquest/max-traps",
    ALLOW_LINES,
    # only for tutorial queries
    # "honeyquest/tutorial-end",
}

ALL_ANNOTATIONS = (
    RISKY_ANNOTATIONS
    | RISKY_ANNOTATIONS_AT_LEAST_ONE
    | DECEPTIVE_ANNOTATIONS
    | TUTORIAL_ANNOTATIONS
    | HONEYPATCH_ANNOTATIONS
    | HONEYQUEST_ANNOTATIONS
)

LICENSE_REFERENCES = {
    "payload/author",
    "payload/license",
}

ALL_REFERENCES = {
    "metaref",
    "payload/author",
    "payload/url",
    "payload/adapted",
    "payload/license",
    "payload/license/extra",
    "technique/doi",
    "technique/url",
    "technique/author",
}


@op(required_resource_keys={"paths"})
def read_queries(context: SolidExecutionContext) -> Dict[str, Query]:
    """
    Parses all queries from the queries directory.
    assumes that there are no duplicate ids.
    use the index job if you want to find duplicates.

    :return: A dictionary of queries, indexed by their id.
    """
    path = context.resources.paths["honeyquest_data"]
    return parse_all_queries(path, log)


@op
def validate_queries(queries: Dict[str, Query]) -> None:
    """
    Validates all queries to be as described in the QUERY_DATABASE.md specifcation.
    raises a warning for each non-conforming query.

    :param queries: A dictionary of queries, indexed by their id.
    """
    for query in queries.values():
        _validate_list_keys(
            query,
            "references",
            mustlist=LICENSE_REFERENCES,
            allowlist=ALL_REFERENCES,
        )
        _validate_list_keys(query, "annotations", allowlist=ALL_ANNOTATIONS)
        _validate_annotation_lines_syntax(query, ALLOW_LINES)
        if query.label == "neutral":
            validate_neutral_query(query)
        elif query.label == "deceptive":
            validate_deceptive_query(query, queries)
        elif query.label == "risky":
            validate_risky_query(query)


def validate_neutral_query(query: Query) -> None:
    assert query.label == "neutral"
    if query.annotations and query.type != "tutorial":
        log.error(
            f"[{query.id}] neutral queries should not have any annotations"
            " (except for tutorial queries)"
        )


def validate_deceptive_query(query: Query, all_queries: Dict[str, Query]) -> None:
    assert query.label == "deceptive"
    _validate_annotation_lines_syntax(query, DECEPTIVE_LINES)
    _validate_list_keys(
        query,
        "annotations",
        allowlist=DECEPTIVE_ANNOTATIONS | HONEYPATCH_ANNOTATIONS | HONEYQUEST_ANNOTATIONS,
        mustlist=DECEPTIVE_ANNOTATIONS,
    )

    if not _get_query_list_key(query, "annotations", APPLIED_HONEYWIRE):
        log.error(f"[{query.id}] {APPLIED_HONEYWIRE} must not be empty")

    if query.type != "tutorial":
        prefix = f"{query.type}-"
        _ensure_query_list_key_starts_with(query, "annotations", APPLIED_HONEYWIRE, prefix)

    if source_id := _get_query_list_key(query, "annotations", ORIGINAL_QUERY):
        if source_id not in all_queries:
            log.error(f"[{query.id}] unknown {ORIGINAL_QUERY} '{source_id}'")

        # some special rules apply when one tries to patch non-neutral queries ...
        original_label = all_queries[source_id].label
        original_risky = _get_query_list_key(query, "annotations", ORIGINAL_RISKY)
        risky_lines = _get_query_list_key(query, "annotations", RISKY_LINES)

        # check the risky lines if they exist
        _validate_annotation_lines_syntax(query, RISKY_LINES)

        if original_label == "deceptive":
            log.error(
                f"[{query.id}] {ORIGINAL_QUERY} '{source_id}'"
                " can not reference a query that is already deceptive"
            )
        if original_label != "risky" and original_risky:
            log.error(
                f"[{query.id}] {ORIGINAL_QUERY} '{source_id}' does not reference"
                f" a risky query although {ORIGINAL_RISKY} is set to true"
            )
        if original_label == "risky" and not original_risky:
            log.error(
                f"[{query.id}] {ORIGINAL_QUERY} '{source_id}' references"
                f" a risky query, but {ORIGINAL_RISKY} is missing or false"
            )
        if original_label == "risky" and not risky_lines:
            log.error(
                f"[{query.id}] {ORIGINAL_QUERY} '{source_id}' references"
                f" a risky query, but {RISKY_LINES} is missing or empty"
            )


def validate_risky_query(query: Query) -> None:
    assert query.label == "risky"
    _validate_annotation_lines_syntax(query, RISKY_LINES)
    _validate_list_keys(
        query,
        "annotations",
        allowlist=RISKY_ANNOTATIONS | RISKY_ANNOTATIONS_AT_LEAST_ONE | HONEYQUEST_ANNOTATIONS,
        mustlist=RISKY_ANNOTATIONS,
        atleastonelist=RISKY_ANNOTATIONS_AT_LEAST_ONE,
    )

    if threat_type := _get_query_list_key(query, "annotations", RISK_TYPE):
        if threat_type not in THREAT_TYPES:
            log.error(f"[{query.id}] unknown {RISK_TYPE} '{threat_type}'")

    if query.type != "tutorial":
        prefix = f"{query.type}-"
        _ensure_query_list_key_starts_with(query, "annotations", PRESENT_WEAKNESS, prefix)
        _ensure_query_list_key_starts_with(query, "annotations", PRESENT_VULNERABILITY, prefix)
        _ensure_query_list_key_starts_with(query, "annotations", PRESENT_ATTACK, prefix)

        rt = _get_query_list_key(query, "annotations", RISK_TYPE)
        present_weakness = _get_query_list_key(query, "annotations", PRESENT_WEAKNESS)
        if rt == "weakness" and not present_weakness:
            log.error(f"[{query.id}] {RISK_TYPE} is '{rt}' but {PRESENT_WEAKNESS} is missing")

        present_vulnerability = _get_query_list_key(query, "annotations", PRESENT_VULNERABILITY)
        if rt == "vulnerability" and not present_vulnerability:
            log.error(f"[{query.id}] {RISK_TYPE} is '{rt}' but {PRESENT_VULNERABILITY} is missing")

        present_attack = _get_query_list_key(query, "annotations", PRESENT_ATTACK)
        if rt == "attack" and not present_attack:
            log.error(f"[{query.id}] {RISK_TYPE} is '{rt}' but {PRESENT_ATTACK} is missing")


def _validate_list_keys(
    query: Query,
    key: str,
    allowlist: Optional[Set[str]] = None,
    mustlist: Optional[Set[str]] = None,
    atleastonelist: Optional[Set[str]] = None,
) -> None:
    assert hasattr(query, key)
    all_list_keys = set()
    for items in getattr(query, key):
        all_list_keys.update(items.keys())
        if len(items) != 1:
            log.error(f"[{query.id}] items in {key} must be placed on a single 'key: value' line")

    mismatched_keys = all_list_keys - allowlist if allowlist else set()
    while mismatched_keys:
        log.error(f"[{query.id}] unknown key in {key}: '{mismatched_keys.pop()}'")

    missing_keys = mustlist - all_list_keys if mustlist else set()
    while missing_keys:
        log.error(f"[{query.id}] missing key in {key}: '{missing_keys.pop()}'")

    if atleastonelist and not atleastonelist.intersection(all_list_keys):
        log.error(
            f"[{query.id}] missing at least one of those keys in {key}:"
            f" {', '.join(atleastonelist)}"
        )


def _validate_annotation_lines_syntax(query: Query, key: str) -> bool:
    if (value := _get_query_list_key(query, "annotations", key)) is not None:
        if not _validate_lines_syntax(value):
            log.error(f"[{query.id}] invalid line syntax '{value}' in field {key}")
    return False


def _validate_lines_syntax(value: str) -> bool:
    components = value.split(",")
    for comp in components:
        row_query = re.match(r"^L\d+(-\d+)?$", comp)  # e.g. L1, L1-2
        col_query = re.match(r"^L\d+:\d+(-\d+)?$", comp)  # e.g. L1:5, L1:5-10
        if not (row_query or col_query):
            return False
    return True


def _get_query_list_key(query: Query, item: str, key: str) -> Optional[str]:
    assert hasattr(query, item)
    for items in getattr(query, item):
        if key in items:
            return items[key]
    return None


def _ensure_query_list_key_starts_with(query: Query, item: str, key: str, prefix: str) -> None:
    if value := _get_query_list_key(query, item, key):
        if not value.startswith(prefix):
            log.error(f"[{query.id}] {key} '{value}' does not start with '{prefix}'")


@job(
    resource_defs={"paths": make_values_resource()},
    config=get_cached_config("index"),
)
def validate_job():
    # pylint: disable=no-value-for-parameter
    queries = read_queries()
    validate_queries(queries)
