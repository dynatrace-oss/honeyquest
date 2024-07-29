# Creating Honeyquest Queries

This document describes available tools to help you create your own queries for Honeyquest.

The structure of the query database is described in the 📄 [QUERY_DATABASE.md](QUERY_DATABASE.md) document.

## Prerequisites

We use Dagster data pipelines to orchestrate the creation of datasets and queries.

Interim pipeline results can be cached if you set the `DAGSTER_HOME` environment variable before you run them.
If you do not set this, your pipelines will always run from scratch and use an [ephemeral cache](https://docs.dagster.io/deployment/dagster-instance#default-local-behavior).
We recommend to set this to the `.dagster` directory in the repository root, although, feel free to point it wherever you like.

```sh
export DAGSTER_HOME=/absolute/path/to/.dagster
```

Most Dagster pipelines require a configuration file to run.
The default configuration is stored in [`config.yaml`](../src/honeyback/honeyquest/data/config.yaml).
You should copy this file and save it as `config.local.yaml` and add your custom values, if necessary.
If you do not provide a `config.local.yaml` file, the default values will be used.

### Run Dagster Jobs

There are [many options to run jobs](https://docs.dagster.io/guides/dagster/intro-to-ops-jobs/single-op-job#step-3-execute-your-first-job).
We recommend to start the Dagit UI and trigger jobs in there.
Open a terminal at the repository root, run `dagit`, and open the URL in your browser.
Within the Dagit UI, select the job, go to the Launchpad, and hit "Launch Run".

```sh
dagit
```

Alternatively, you can run the pipelines from the command line, for example, the index job.

```sh
dagster job execute -m honeyquest.data.jobs.index
```

### Job Description

Currently, the following jobs exist to create datasets.

| Job            | Description                                                                                      |
| -------------- | ------------------------------------------------------------------------------------------------ |
| `hackertarget` | Samples from 500k HTTP headers from [Hacker Target](https://hackertarget.com/500k-http-headers/) |

Also, the following jobs are necessary to orchestrate the created data.

| Job        | Description                                                                     |
| ---------- | ------------------------------------------------------------------------------- |
| `index`    | Creates a fast index for the frontend. Run it, whenever you create new queries. |
| `validate` | Validates a few semantic rules that queries and their fields should follow.     |
| `upload`   | Creates a query archive and uploads that to an S3 bucket.                       |
