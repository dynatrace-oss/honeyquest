# Honeyquest Cloud Deployment

Honeyquest can be deployed in any environment that can host containers.

## Deployment with AWS Copilot

[AWS Copilot](https://aws.github.io/copilot-cli/) helps to deploy Honeyquest as an instance in [Amazon ECS](https://docs.aws.amazon.com/ecs/).

### Prerequisites

You need the following toolchain installed:

- [AWS Copilot CLI](https://aws.github.io/copilot-cli/docs/getting-started/install/) to interface with AWS Copilot
- [AWS CLI](https://aws.amazon.com/cli/) to configure AWS credentials
- [Docker Engine](https://docs.docker.com/engine/install/) (or similar) to build container images

AWS Copilot will populate your repository with some configuration files in a top-level `copilot` directory.
We recommend to fork this repository so that your custom configuration is stored in your fork only.

### Initial deployment

First, navigate to the AWS Console and create a hosted zone in Route 53 for Honeyquest.
In our example, we want Honeyquest to be accessible via `honeyquest.yourdomain.test` and assume you created a hosted zone for that name.

Next, we recommend to create two files that pre-initialize AWS Copilot.

In this repository, create file `/copilot/.workspace` with the following content:

```yaml
application: honeyquest
path: ""
```

In this repository, create file `/copilot/honeyquest/manifest.yml` with the following content and adapt three things:

- Set the `http.alias` to your domain
- Set the `environments.prod.variables.COOKIE_SECRET` to some random string and treat it like a secret
- Set the `environments.prod.variables.ADMIN_TOKEN` to some random string and treat it like a secret
- Possibly adjust the `image.build` path to your Dockerfile, if the repository structure differs

Please refer to the root [README](../README.md) for more details about the available environment variables.

```yaml
# spec: https://aws.github.io/copilot-cli/docs/manifest/lb-web-service/

name: honeyquest
type: Load Balanced Web Service

http:
  path: "/"
  alias: honeyquest.yourdomain.test

image:
  build: Dockerfile
  port: 3000

variables:
  HONEYQUEST_RESULTS: /opt/honeyquest/results
  COMPRESS_RESULTS: "false"
  SAMPLE_DUPLICATES: "false"
  API_BURST_LIMIT: 10
  API_RATE_LIMIT: 1

environments:
  prod:
    variables:
      HONEYQUEST_DATA_URL: https://raw.githubusercontent.com/dynatrace-oss/honeyquest/main/.github/hostedfiles/querydb.tar.gz
      HONEYQUEST_INDEX: main
      COOKIE_SECRET: cookie
      ADMIN_TOKEN: admin

storage:
  volumes:
    honeyquest-results:
      efs: true
      path: /opt/honeyquest/results
      read_only: false

# only the following combinations are allowed:
# https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-cpu-memory-error.html
cpu: 512
memory: 1024

count: 1 # number of tasks
exec: true # enable running commands in the container
```

Finally, authenticate your AWS CLI and setup the application and environments with AWS Copilot:

```sh
aws configure
copilot app init --domain honeyquest.yourdomain.test
copilot svc init -n honeyquest
copilot env init -n prod
copilot env deploy --name prod
```

#### Deploying multiple environments

The above steps configure a single `prod` environment.
You can easily create multiple replicas of Honeyquest by adding multiple sections to the `environments` along with their own subdomain:

```yaml
dev:
  http:
    alias: dev.honeyquest.yourdomain.test
  variables:
    HONEYQUEST_DATA_URL: https://raw.githubusercontent.com/dynatrace-oss/honeyquest/main/.github/hostedfiles/querydb.tar.gz
    HONEYQUEST_INDEX: main
    COOKIE_SECRET: cookie
    ADMIN_TOKEN: admin
```

You can than initialize these environments with AWS Copilot:

```sh
copilot env init -n dev
copilot env deploy --name dev
```

### Application upgrade

Deploy and upgrade the app with the following commands.
You may also deploy to the other environments by naming them explicitly.

```sh
copilot deploy -e prod
copilot svc show
```

To get a shell in the deployed container, run the following.

```sh
copilot svc exec -c /bin/bash -e prod
```

### Decommissioning

If you want to delete some environment again, run the following.

```sh
copilot svc delete -e prod
copilot env delete -n prod
```

If you want to remove all traces of the AWS Copilot deployment, also delete the CloudFormation templates and the AppConfig elements directly.
