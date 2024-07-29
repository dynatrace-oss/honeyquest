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

from pathlib import Path
from typing import Dict, List

import yaml
from dagster import (
    AssetMaterialization,
    SolidExecutionContext,
    get_dagster_logger,
    job,
    make_values_resource,
    op,
)

from honeyquest.common.serializers import yaml_dump

from ...common.models.query import Query
from ...common.timestamps import epoch_time_to_iso_str
from ..config import get_cached_config

log = get_dagster_logger()


@op(required_resource_keys={"paths"})
def create_index(context: SolidExecutionContext) -> None:
    """
    Generates an `index_%TIMESTAMP%.yaml` based on the generated queries.
    See also QUERY_DATABASE.md.
    """
    path = Path(context.resources.paths["honeyquest_data"]).resolve()

    index: Dict[str, List[str]] = {}
    num_files = 0
    all_query_ids = set()

    yaml_globber = (path / "queries").rglob("*.yaml")
    for file in yaml_globber:
        relative_file = file.relative_to(path)
        rel_path = str(relative_file.as_posix())
        log.info(f"parsing {relative_file} ...")

        # parse queries and generate index
        with open(file, encoding="utf8") as stream:
            yaml_docs = yaml.safe_load_all(stream)
            queries = (Query(**d) for d in yaml_docs)
            ids = sorted(q.id for q in queries)

            # check for duplicate ids in this file and across all files
            for query_id in ids:
                if query_id in all_query_ids:
                    if (cnt := ids.count(query_id)) > 1:
                        raise ValueError(f"duplicate id {query_id} is {cnt} times in {rel_path}")
                    dup_path = next(k for k, v in index.items() if query_id in v)
                    raise ValueError(f"duplicate id {query_id} in {rel_path} and {dup_path}")

                all_query_ids.add(query_id)

            index[rel_path] = ids
            num_files += 1

    # store index file
    isostr = epoch_time_to_iso_str(timespec="seconds")
    index_path = path / "index" / f"index_{isostr}.yaml"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with open(index_path, "w+", encoding="utf8") as f:
        # order is the sampling order and index is the actual index
        document = yaml_dump(dict(order=[], index=index), sort_keys=True)
        f.write(document)

    context.log_event(
        AssetMaterialization(
            asset_key="honeyquest.queries.index",
            description="honeyquest query index",
            metadata={
                "path": index_path.resolve().as_posix(),
                "num_files": num_files,
                "num_queries": len(all_query_ids),
            },
        )
    )


@job(
    resource_defs={"paths": make_values_resource()},
    config=get_cached_config("index"),
)
def index_job():
    # pylint: disable=no-value-for-parameter
    create_index()
