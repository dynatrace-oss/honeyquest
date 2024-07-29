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
import shutil
import tarfile
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile, mkdtemp
from uuid import uuid4

import requests
import uvicorn
from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

from .config import Settings, get_settings
from .routes import admin, api
from .services.query import get_query_sampler_svc
from .services.storage import get_persistence_svc

# reuse the uvicorn logger
log = logging.getLogger("uvicorn.error")

STATIC_PATH = Path(__file__).parent / "static"


def create_app(debug: bool):
    settings = get_settings()
    cookie_max_age = 3600 * 24 * settings.cookie_expire_days

    app = FastAPI(
        debug=debug,
        middleware=[
            # middlewares are always "wrapped around" the following middleware,
            # so be sure to follow the correct declaration order here
            Middleware(
                SessionMiddleware,
                secret_key=settings.cookie_secret,
                max_age=cookie_max_age,
            ),
        ],
    )

    app.include_router(api.router, prefix="/api")
    app.include_router(admin.router, prefix="/api/admin")

    # get service singletons to initialize them now
    # and not one the first requests
    get_query_sampler_svc()
    get_persistence_svc()

    return app


def production_app():
    return create_app(debug=False)


def development_app():
    return create_app(debug=True)


def download_data(url: str, target: str):
    """
    Downloads the URL, extracts the contents of the .tar.gz file, and moves them to the target.

    :param url: URL to a .tar.gz file
    :param target: Target directory where the extracted contents are placed
    """
    resp = requests.get(url, allow_redirects=True, timeout=60)
    with tarfile.open(fileobj=BytesIO(resp.content), mode="r:gz", encoding="utf-8") as tar:
        tar.extractall(path=target)
    log.warning(f"downloaded data from {url} to {target}")


def try_fallback_index(data_path: Path | str):
    """
    Finds a fallback index to use if none was specified.
    Will raise an error if no fallback is possible.

    :param data_path: Path to the data directory
    :return: The name of the fallback index, if possible
    """
    data_path = Path(data_path)
    available_files = (data_path / "index").iterdir()
    available_indexes = [f.stem for f in available_files if f.is_file() and f.suffix == ".yaml"]
    selected_index = None

    if "main" in available_indexes:  # take the main index
        selected_index = "main"
        log.warning("no index set, using 'main' as the default index.")
    elif len(available_indexes) == 1:  # take the only one
        selected_index = available_indexes[0]
        log.warning(
            f"no index set, using '{selected_index}' as the only available index. "
            f"use --index={selected_index} (or HONEYQUEST_INDEX in the environment) "
            "to declare this explicitly or rename this one to 'main'."
        )
    else:  # nothing to recover, raise an error
        errmsg = "no index set, and no default index 'main' found. "
        errmsg += "use --index=INDEX_NAME (or HONEYQUEST_INDEX in the environment) to declare one."
        if len(available_indexes) > 0:
            errmsg += " found indexes: " + ", ".join(f"'{e}'" for e in available_indexes)

        log.error(errmsg)
        raise ValueError(errmsg)

    return selected_index


def run_server(settings: Settings, debug: bool = False):
    """Start the uvicorn server.

    :param settings: Settings object for the server instance
    :param debug: Watch for changes, use dev sources, enable debug mode (default: False)
    """
    # possibly generate a random cookie secret
    if not settings.cookie_secret:
        # TODO: RT-2490 improve handling of config and secrets
        settings.cookie_secret = str(uuid4())
        log.warning(
            "no cookie secret set, generated a random one. "
            f"set it with --cookie-secret={settings.cookie_secret} "
            "(or COOKIE_SECRET in the environment) "
            "so that users are able to re-use their session cookies."
        )

    # possibly generate a random admin token
    if not settings.admin_token:
        settings.admin_token = str(uuid4())
        log.warning(
            "no admin token set, generated a random one. "
            f"set it with --admin-token={settings.admin_token} "
            "(or ADMIN_TOKEN in the environment)."
        )

    # possibly fallback to a temporary results directory
    if not settings.honeyquest_results:
        settings.honeyquest_results = mkdtemp(prefix="honeyquest_results_")
        log.warning(
            "no results directory set, created a temporary directory. "
            f"use --results={settings.honeyquest_results} "
            "(or RESULTS in the environment) "
            "to have a permanent results location."
        )

    # possibly download the data first
    if settings.honeyquest_data_url:
        settings.honeyquest_data = mkdtemp(prefix="honeyquest_data_")
        download_data(settings.honeyquest_data_url, settings.honeyquest_data)

    # possibly fallbacks for the index name
    if not settings.honeyquest_index:
        assert settings.honeyquest_data is not None
        settings.honeyquest_index = try_fallback_index(settings.honeyquest_data)

    # configuration can only be passed with a .env file to uvicorn.
    # to keep type safety, we extract a .env file representation
    # of the settings object (with __repr_str__) for uvicorn.
    env_file = NamedTemporaryFile(mode="w+", encoding="utf8", prefix="honeyquest_", delete=False)
    env_file.write(str(settings).replace(" ", "\n"))
    env_file.close()

    try:
        app_name = "production_app" if not debug else "development_app"
        uvicorn.run(
            f"{__name__}:{app_name}",
            factory=True,
            host="0.0.0.0",
            port=3001,
            reload=debug,
            env_file=env_file.name,
        )

    finally:
        Path(env_file.name).unlink(missing_ok=True)

        # if the data directory was downloaded, cleanup as well
        if settings.honeyquest_data_url and settings.honeyquest_data:
            data_dir = Path(settings.honeyquest_data)
            if data_dir.exists():
                shutil.rmtree(data_dir, ignore_errors=True)
