# syntax=docker/dockerfile:1.2

ARG WORKDIR=/opt/honeyquest

############################################################
FROM bitnami/git:2.45.2 AS git-commit

WORKDIR /home
COPY .git /home/.git

# store the full hash into a file
RUN /bin/bash -c 'git rev-parse HEAD > /GIT_COMMIT'
RUN /bin/bash -c 'git show -s --format=%s > /GIT_MESSAGE'
RUN /bin/bash -c 'git rev-parse --abbrev-ref HEAD > /GIT_BRANCH'

############################################################
FROM docker.io/nikolaik/python-nodejs:python3.10-nodejs20@sha256:97f8a87d28786db28a2796ca3932a52aaff75b703f9020a29fd6fc4387f64b47 AS node-deps
ARG WORKDIR

WORKDIR ${WORKDIR}/honeyfront

# install node dependencies
COPY ./src/honeyfront/package.json ./src/honeyfront/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm install

# build the node app (optimized for production)
COPY ./src/honeyfront/tsconfig.json ./
COPY ./src/honeyfront/tsconfig.node.json ./
COPY ./src/honeyfront/index.html ./
COPY ./src/honeyfront/public ./public
COPY ./src/honeyfront/src ./src
RUN npm run build

##############################################################
FROM docker.io/nikolaik/python-nodejs:python3.10-nodejs20@sha256:97f8a87d28786db28a2796ca3932a52aaff75b703f9020a29fd6fc4387f64b47 AS python-deps
ARG WORKDIR

WORKDIR ${WORKDIR}/honeyback

ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

# install python dependencies
COPY ./src/honeyback/poetry.lock ./src/honeyback/pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/pypoetry \
    poetry install --no-root

###############################################
FROM docker.io/nikolaik/python-nodejs:python3.10-nodejs20@sha256:97f8a87d28786db28a2796ca3932a52aaff75b703f9020a29fd6fc4387f64b47 AS final
ARG WORKDIR

WORKDIR ${WORKDIR}

# install an nginx server (https://docs.nginx.com/nginx/admin-guide/installing-nginx/installing-nginx-docker/) and circus
# - nginx serves the static files from the node app & proxies /api to the python api
# - circus starts both the python api and the nginx server processes
RUN addgroup --system --gid 102 nginx && \
    adduser --system --uid 102 --ingroup nginx --disabled-login --gecos "nginx user" --no-create-home --home /nonexistent --shell /bin/false nginx && \
    apt-get update && \
    apt-get install --no-install-recommends --no-install-suggests -y nginx && \
    python -m pip install --no-cache-dir circus && \
    rm -rf /var/lib/apt/lists/*

# process manager and nginx config
COPY ./src/docker/entrypoint.py ./
COPY ./src/docker/nginx.conf /etc/nginx/sites-available/honeyquest.conf
RUN ln -s /etc/nginx/sites-available/honeyquest.conf /etc/nginx/sites-enabled/honeyquest.conf && \
    unlink /etc/nginx/sites-enabled/default

WORKDIR ${WORKDIR}/honeyfront

# copy static files from node build to the nginx root
COPY --from=node-deps ${WORKDIR}/honeyfront/dist ./

WORKDIR ${WORKDIR}/honeyback

ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

# copy python source and install the root project
COPY --from=python-deps ${WORKDIR}/honeyback ./
COPY ./src/honeyback/honeyquest ./honeyquest
RUN poetry install --no-cache --only-root

# copy git version information
COPY --from=git-commit /GIT_* ${WORKDIR}

WORKDIR ${WORKDIR}

EXPOSE 3000

ENTRYPOINT ["python", "./entrypoint.py"]
