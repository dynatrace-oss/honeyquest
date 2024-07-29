# Honeyquest Query Database Specification

This document describes the structure of the Honeyquest query database.

Tooling to create your own queries with Dagster is described in the 📄 [QUERY_CREATION.md](QUERY_CREATION.md) document.

## Query Format

One or more questions (or, queries) are stored in a single YAML file.
One file should always hold queries of the same `type` and `label`.
On the semantic meaning of the labels, please refer to the 📄 [QUERY_GLOSSARY.md](QUERY_GLOSSARY.md) document.
Each individual query has the following fields.

- `id` is a globally unique identifier for this query
- `label` is one of `neutral | risky | deceptive`
- `type` is one of `filesystem | htaccess | httpheaders | networkrequests`
- `data` holds the payload, note the [syntax for YAML multiline strings](https://yaml-multiline.info/)
- `references` _(optional)_ is a list of key-value pairs referencing metadata:
  - `metaref` keys can reference to a metadata entry (see below)
  - `payload/author` keys denote the original creator of the artifact that this query was derived from (can be repeated)
  - `payload/url` keys hold a URL to the original artifact that this query was derived from (can be repeated)
  - `payload/adapted` keys can be used to indicate if the original artifact was adapted or modified (can be repeated)
  - `payload/license` keys hold a SPDX identifier of the license of the artifact that this query was derived from (can be repeated)
  - `payload/license/extra` keys can be used to give credit, indicate if changes were made, or list additional terms (can be repeated)
  - `technique/author` keys hold an author name of the creator of an applied cyber deception technique (can be repeated)
  - `technique/doi` keys hold a DOI to a bibliographic reference of the creator of an applied cyber deception technique (can be repeated)
  - `technique/url` keys hold a URL to a bibliographic reference of the creator of an applied cyber deception technique (can be repeated)
- `annotations` _(optional)_ is a list of key-value pairs highlighting code fragments:
  - `risk/type` describes the type of threat on risky queries, usually `vulnerability | weakness | attack`
  - `risk/present-weakness` names the weakness that is present in that query
  - `risk/present-vulnerability` names the vulnerability that is present in that query
  - `risk/present-attack` names the attack that is present in that query
  - `risk/description` holds a human-readable description of the risk
  - `risk/risky-lines` marks risky code fragments (see line annotations syntax below)
  - `honeypatch/deceptive-lines` marks deceptive code fragments (see line annotations syntax below)
  - `honeypatch/original-query` names the query id that has been patched with a honeywire
  - `honeypatch/original-risky` must be set to `true` when the original query was risky
  - `honeypatch/applied-honeywire` names the honeywire that the original query has been patched with
  - `honeypatch/description` holds a human-readable description of the deception technique
  - `honeyquest/button-text` overrides the text of the continue button in the UI
  - `honeyquest/select` enables or disables that lines can be selected in the UI
  - `honeyquest/select-hacks` enables or disables that lines can be selected as hacks in the UI
  - `honeyquest/select-traps` enables or disables that lines can be selected as traps in the UI
  - `honeyquest/max-hacks` sets the maximum number of hacks that can be selected in the UI
  - `honeyquest/max-traps` sets the maximum number of traps that can be selected in the UI
  - `honeyquest/allow-lines` restricts the lines that can be selected in the UI (see line annotations syntax below)
  - `honeyquest/tutorial-end` indicates to the UI that this is the last query of the tutorial

```yaml
# csic-133x.yaml

id: csic-1337
label: neutral
type: httpheaders
data: |
  HTTP/1.1 301 Moved Permanently
  Location: https://www.example.org/index.asp%{HTTP_HOST}^www\.(.*)$
---
id: csic-1338
label: risky
type: httpheaders
references:
  - metaref: path-traversal
  - technique/url: https://portswigger.net/web-security/file-path-traversal
  - technique/url: https://owasp.org/www-community/attacks/Path_Traversal
annotations:
  - risk/type: attack
  - risk/risky-lines: "L3:39-60"
data: |
  HTTP/1.1 200 OK
  Date: Mon, 23 May 2005 22:38:34 GMT
  Content-Type: text/html; charset=UTF-8%D../../../etc/passwd
  Content-Length: 155
  Last-Modified: Wed, 08 Jan 2003 23:11:55 GMT
  Server: Apache/1.3.3.7 (Unix) (Red-Hat/Linux)
  Accept-Ranges: bytes
  Connection: close
---
id: csic-1339
label: deceptive
type: httpheaders
annotations:
  - honeypatch/deceptive-lines: "L3"
  - honeypatch/original-query: csic-1337
  - honeypatch/applied-honeywire: httpheaders-apiserver
data: |
  HTTP/1.1 301 Moved Permanently
  Location: https://www.example.org/index.asp%{HTTP_HOST}^www\.(.*)$
  X-Kube-ApiServer: /hko/api
```

### Line Annotations Syntax (LAS)

Line annotations are used to mark sections of the payload.
The syntax permits to have a comma-separated list of line annotations.
Note that line numbers and column numbers start counting at 1.

- `L2,L2-5,L3:5-10,L8:10` is a valid example of a line annotation string.

The syntax of a single component is as follows:

- `L2` marks line 2
- `L2-5` marks line 2, 3, 4, and 5
- `L3:5-10` marks character 5, 6, 7, 8, 9, and 10 on line 3
- `L8:10` marks line 8 from character 10 to the end of the line

## Metadata Format

Metadata can be used to describe vulnerabilities, weaknesses, or attack patterns that are shown in queries.
Especially risky queries might have additional metadata attached to them.
These are stored in separate Markdown files with YAML front matter.
They can be linked by their `id` to the `metaref` key in the `references` field in the queries.

- `id` is a globally unique identifier for this metadata entry that MUST be equal to its filename
- `title` is a human-readable description of the metadata entry
- `references` holds zero or more links to external URLs
- `author` attributes the written text to some author
- `license` describes the license of the written text by their [SPDX identifier](https://spdx.org/licenses/)
- `classification.cwe` is a list of references to the [CWE ID](https://cwe.mitre.org/data/index.html) of this weakness
- `classification.capec` is a list of references to the [CAPEC ID](https://capec.mitre.org/index.html) of this attack pattern
- `classification.owasp` is a list of references to the [OWASP ID](https://owasp.org/www-project-top-ten/) of this weakness
- The Markdown-formatted description that may be presented along with a query follows

```yaml
# path-traversal.md
---
id: path-traversal
title: Path Traversal
references:
  - https://portswigger.net/web-security/file-path-traversal
  - https://owasp.org/www-community/attacks/Path_Traversal
author: Mario Kahlhofer <mario.kahlhofer@dynatrace.com>
license: CC-BY-4.0
classification:
  owasp: ["A01:2021"]
  cwe: [22]
  capec: [126]
---
A path traversal vulnerability arises if a user can control
the path of a file or directory that is accessed by the application,
outside of the intended directory structure. This can often be identified
by seeing a sequence of `../` that tries to navigate the file system.
```

## Directory Structure

For easy retrieval, queries are structured in folders based on their `type` and `label`.
This is NOT enforced by Honeyquest but its a good convention to follow.

```text
.
├── index
│   └── main.yaml
├── metadata
│   └── http-path-traversal.yaml
└── queries
    ├── httpheaders
    │   ├── neutral
    │   │   └── csic-42xx.yaml
    │   └── risky
    │       ├── csic-133x.yaml
    │       └── csic-134x.yaml
    └── jsonresponse
        ├── neutral
        │   └── jzon-1x.yaml
        └── risky
            └── jzon-1x.yaml

```

## Query Index

YAML documents might contain multiple queries.
Further, you might want to design experiments that may only use a subset of queries.
For easy retrieval and organization, we have index files that keep a reference to all of them.

Index files are stored in a directory `index`.
You should tell Honeyquest what index to use on start, or it will fall-back to `main.yaml` otherwise.

Please note that there is the `honeyquest.data.jobs.index` Dagster job that automatically creates an index for you.
Refer to the 📄 [QUERY_CREATION.md](QUERY_CREATION.md) document for more details.

```yaml
# index.yaml

index:
  queries/httpheader/neutral/csic-42xx.yaml:
    - csic-4201
    - csic-4202
    - csic-4203
    - csic-4204
    - csic-4205
  queries/httpheader/risky/csic-133x.yaml:
    - csic-1337
    - csic-1338
    - csic-1339
  queries/httpheader/risky/csic-134x.yaml:
    - csic-1340
```

### Query Buckets

The index can also be used to enforce a certain order of queries.
Queries can be grouped into buckets, which are then presented to the user in a specific order.
For each bucket, you can specify if queries in that bucket shall be sampled in a random order or not.

- `buckets.<bucket_name>` is an internal identifier for the bucket
- `buckets.<bucket_name>.description` is a human-readable description of the bucket that is also shown in the UI
- `buckets.<bucket_name>.strategy` is one of `random | sorted`
- `buckets.<bucket_name>.queries` is a list of query ids that are part of this bucket
- `order` is a list of bucket names that specify the order in which the buckets are presented to the user

```yaml
# index-with-buckets.yaml

index:
  queries/tutorial/tutorial.yaml:
    - TR125.tutorial.welcome-01
    - TR125.tutorial.welcome-02
    - TR125.tutorial.welcome-03
  queries/httpheader/risky/csic-133x.yaml:
    - csic-1337
    - csic-1338
    - csic-1339

buckets:
  tutorial:
    strategy: sorted
    description: Tutorial
    queries:
      - TR125.tutorial.welcome-01
      - TR125.tutorial.welcome-02
      - TR125.tutorial.welcome-03

  experiment:
    strategy: random
    description: Experiment
    queries:
      - csic-1337
      - csic-1338
      - csic-1339

order:
  - tutorial
  - warmup
```
