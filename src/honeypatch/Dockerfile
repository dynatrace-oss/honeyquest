# syntax=docker/dockerfile:1.2

ARG WORKDIR=/opt/honeypatch

##############################################################
FROM docker.io/nikolaik/python-nodejs:python3.10-nodejs20@sha256:d494ba62a80c2d59a55f80ae540701c592f2920fa1ea0c0344a13f1ddcaad713 AS python-deps
ARG WORKDIR

WORKDIR ${WORKDIR}

ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

# install python dependencies
COPY poetry.lock pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/pypoetry \
    poetry install --no-root

###############################################
FROM docker.io/nikolaik/python-nodejs:python3.10-nodejs20@sha256:d494ba62a80c2d59a55f80ae540701c592f2920fa1ea0c0344a13f1ddcaad713 AS final
ARG WORKDIR

WORKDIR ${WORKDIR}

# entrypoint that sources our venv
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

# copy python source and install the root project
COPY --from=python-deps ${WORKDIR} ./
COPY ./honeypatch ./honeypatch
RUN poetry install --no-cache --only-root

ENTRYPOINT [ "./entrypoint.sh", "python", "-m", "honeypatch" ]
CMD ["--help"]
