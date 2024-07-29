from dagster import repository

from .jobs.hackertarget import hackertarget_job
from .jobs.index import index_job
from .jobs.upload import upload_job
from .jobs.validate import validate_job

__all__ = ["hackertarget_job", "index_job", "upload_job", "validate_job"]


@repository
def honeyquest_repository():
    return [hackertarget_job, index_job, upload_job, validate_job]
