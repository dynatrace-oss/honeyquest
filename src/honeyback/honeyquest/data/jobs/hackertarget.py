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

import math
import random
import tarfile
import warnings
from io import BytesIO
from pathlib import Path
from typing import Dict, List

import requests
from dagster import (
    AssetMaterialization,
    ExperimentalWarning,
    Noneable,
    SolidExecutionContext,
    SourceHashVersionStrategy,
    get_dagster_logger,
    job,
    make_values_resource,
    op,
)

from ...common.models.query import Query
from ...common.serializers import yaml_dump_all
from ..config import get_cached_config

# we know that SourceHashVersionStrategy is an experimental feature
warnings.filterwarnings("ignore", category=ExperimentalWarning)

log = get_dagster_logger()

QUERY_TYPE = "httpheaders"
QUERY_LABEL = "neutral"
NUM_HEADERS = 500_000
HackerTargetHeaders = Dict[int, List[List[str]]]


@op(config_schema={"mirror": str})
def download_headers(context: SolidExecutionContext) -> bytes:
    """
    Downloads the raw .tar.gz dataset with 500k http headers.

    :return: the raw bytes of the dataset
    """
    url = context.op_config["mirror"]
    log.info(f"attempting download from {url} ...")
    response = requests.get(url, timeout=10)
    if not response.ok:
        raise IOError(f"response status code was {response.status_code}")

    size = int(response.headers["Content-Length"]) / (1024 * 1024)
    log.info(f"Downloaded {size:.2f} MB of http headers (status code: {response.status_code})")

    return response.content


@op(
    config_schema={
        "sample_rate": float,
        "seed": Noneable(int),
    }
)
def extract_headers(context: SolidExecutionContext, data: bytes) -> HackerTargetHeaders:
    """
    Maps the raw http header dataset to a dictionary, like in the example below.
    the index is the original id from the dataset. the value is a list of the
    http headers that have been received. there might be more due to redirects.

    >>> queries = {
    >>>     16: [
    >>>         ["HTTP/1.1 302 Found", b"Location: http://www.demo.com/"],
    >>>         ["HTTP/1.1 200 OK", b"Content-Length: 277001"],
    >>>     ]
    >>> }

    :param context: the dagster context
    :param data: the original .tar.gz dataset file
    :return: a pre-processed structure of the dataset
    """
    sample_rate = context.op_config["sample_rate"]
    seed = context.op_config["seed"]
    num_samples = int(sample_rate * NUM_HEADERS)
    log.info(
        f"will sample only {num_samples:,d} queries "
        f"from the original archive ({NUM_HEADERS:,d} samples) ..."
    )

    # chose the indexes that we will sample from the archive
    random.seed(seed)
    sample_indexes = [random.randint(0, NUM_HEADERS - 1) for _ in range(num_samples)]

    nskip = 0
    queries = {}
    buff = BytesIO(data)
    with tarfile.open(fileobj=buff, mode="r:gz", encoding="utf-8") as tar:
        for i, tarinfo in enumerate(tar):
            if not tarinfo.isreg() or not tarinfo.name.endswith(".header"):
                continue

            if i not in sample_indexes:
                continue

            tfile = tar.extractfile(tarinfo)
            if tfile is None:
                raise IOError(f"could not extract {tarinfo.name}")

            # decode, and split on empty line
            # empty lines indicate multiple headers
            headers: List[List[str]] = [[]]
            for byteline in tfile.read().splitlines():
                if byteline == b"":
                    headers.append([])
                else:
                    # decode with \xNN escape chars and strip trailing whitespace
                    strline = byteline.decode("utf8", errors="backslashreplace").rstrip()
                    headers[-1].append(strline)

            # drop trailing blocks
            if len(headers[-1]) == 0:
                del headers[-1]

            # skip empty files
            if len(headers) == 0:
                nskip += 1
                continue

            # store with original header number
            no = int(Path(tarinfo.name).stem)
            queries[no] = headers

    if nskip > 0:
        log.warning(f"skipped {nskip:,d} empty .header files during processing")

    return queries


@op(required_resource_keys={"paths"}, config_schema={"chunk_size": int})
def store_headers(context: SolidExecutionContext, data: HackerTargetHeaders) -> None:
    """
    Store the hackertarget dataset in a format that is compatible with honeyquest.

    :param context: the dagster context
    :param data: the pre-processed dataset
    """
    path = Path(context.resources.paths["honeyquest_data"]).resolve()
    base_path = path / "queries" / QUERY_TYPE / QUERY_LABEL
    base_path.mkdir(parents=True, exist_ok=True)

    chunk_size = context.op_config["chunk_size"]
    num_chunks = math.ceil(len(data) // chunk_size)
    log.info(f"storing data to {base_path} in {num_chunks} chunks of {chunk_size} queries ...")

    # just for formatting the chunk id with leading zeros
    zlen = len(str(num_chunks))

    chunks: List[Query] = []
    chunk_id = 0
    for i, (no, headers) in enumerate(data.items()):
        query_id = f"hackertarget-{no:06d}.{len(headers):02d}"
        query_data = "\n".join(headers[-1])  # only take the last header

        query = Query(
            id=query_id,
            label=QUERY_LABEL,
            type=QUERY_TYPE,
            data=query_data,
            references=[
                {"payload/author": "Hacker Target Pty Ltd"},
                {"payload/license": "CC-BY-4.0"},
                {"payload/adapted": False},
                {"payload/url": "https://hackertarget.com/500k-http-headers/"},
            ],
        )
        chunks.append(query)

        # write to disk in chunks and don't forget the last chunk
        if len(chunks) == chunk_size or i == len(data) - 1:
            chunk_path = base_path / f"hackertarget-{str(chunk_id).zfill(zlen)}.yaml"
            with open(chunk_path, "w+", encoding="utf8") as f:
                document = yaml_dump_all([q.model_dump() for q in chunks])
                f.write(document)

            chunks.clear()
            chunk_id += 1

    context.log_event(
        AssetMaterialization(
            asset_key=f"honeyquest.queries.{QUERY_TYPE}.hackertarget",
            description="500k http response headers from the top 500k sites",
            metadata={
                "path": base_path.resolve().as_posix(),
                "num_chunks": chunk_id,
                "num_queries": len(data),
            },
        )
    )


@job(
    resource_defs={"paths": make_values_resource()},
    config=get_cached_config("hackertarget"),
    version_strategy=SourceHashVersionStrategy(),
)
def hackertarget_job():
    # pylint: disable=no-value-for-parameter
    archive = download_headers()
    data = extract_headers(archive)
    store_headers(data)
