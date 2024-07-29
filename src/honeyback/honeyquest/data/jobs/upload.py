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

import tarfile
import tempfile
from pathlib import Path

import boto3
from dagster import (
    AssetMaterialization,
    Noneable,
    SolidExecutionContext,
    get_dagster_logger,
    job,
    make_values_resource,
    op,
)

from ..config import get_cached_config

log = get_dagster_logger()


@op(
    required_resource_keys={"paths"},
    config_schema={
        "s3_bucket_alias": Noneable(str),
        "s3_bucket_name": str,
        "s3_bucket_prefix": str,
        "s3_bucket_key": str,
    },
)
def upload_s3_archive(context: SolidExecutionContext) -> None:
    """Archives a data directory and uploads it to an s3 bucket."""
    path = Path(context.resources.paths["honeyquest_data"]).resolve()
    bucket_alias = context.op_config["s3_bucket_alias"]
    bucket_name = context.op_config["s3_bucket_name"]
    bucket_prefix = context.op_config["s3_bucket_prefix"]
    bucket_key = context.op_config["s3_bucket_key"]

    if bucket_alias is None:
        bucket_alias = f"{bucket_name}.s3.amazonaws.com"

    archive_tmp = tempfile.NamedTemporaryFile(prefix="honeyquest_", suffix=".tar.gz", delete=False)
    archive_file = Path(archive_tmp.name).resolve()

    # archive the contents (i.e., the children) of the honeyquest data folder
    with tarfile.open(archive_file, "w:gz") as tar:
        for child in path.iterdir():
            tar.add(child, arcname=child.name)
    size = int(archive_file.stat().st_size) / (1024 * 1024)
    log.info(f"Archived directory {path} to {archive_file} ({size:.2f} MB)")

    try:
        s3_bucket = boto3.resource("s3").Bucket(bucket_name)
        s3_bucket.upload_file(str(archive_file), f"{bucket_prefix}/{bucket_key}")

        context.log_event(
            AssetMaterialization(
                asset_key="honeyquest.queries.archive",
                description="archived honeyquest data directory",
                metadata={"url": f"https://{bucket_alias}/{bucket_prefix}/{bucket_key}"},
            )
        )

        # verify what files are in the bucket
        log.info("Uploaded archive to S3, the following files are available now:")
        for obj in s3_bucket.objects.filter(Prefix=f"{bucket_prefix}/"):
            url = f"https://{bucket_alias}/{obj.key}"
            size = int(obj.size) / (1024 * 1024)
            log.info(f"{str(obj.last_modified):>30} {url} ({size:.2f} MB)")

    finally:
        try:
            if archive_file.exists():
                archive_file.unlink(missing_ok=True)
        except Exception:
            log.warn(f"Could not delete temporary archive file {archive_file}")


@job(
    resource_defs={"paths": make_values_resource()},
    config=get_cached_config("upload"),
)
def upload_job():
    # pylint: disable=no-value-for-parameter
    upload_s3_archive()
