# Query Label Glossary

Query labels reflect the design strategy of a certain query.
We use the following three design strategies:

- **`neutral`** queries may be harmless, secure, benign, well-protected, or of neutral appearance.
- **`risky`** queries may be harmful, insecure, malicious, lack security measures, or have negative intent.
- **`deceptive`** queries want to grab the attention of an adversary, often by seeming risky.

Risky queries are further classified by their `risk/type` annotation.

- **`vulnerability`** contains at least one indicator in the query that points to a known vulnerability
- **`weakness`** display a insecure pattern that might lead to a vulnerability
- **`attack`** showcases a deliberate attempt to do to harm, often by exploiting a vulnerability or weakness

Risky queries often reference one of the following external sources:

- [CVE IDs](https://cve.mitre.org/index.html) for vulnerabilities
- [CWE IDs](https://cwe.mitre.org/data/index.html) for weaknesses
- [CAPEC IDs](https://capec.mitre.org/index.html) for attack patterns

## Examples

### `neutral` query

A `GET` request to a Wikipedia article. Nothing suspicious here.

```text
GET /wiki/Cat HTTP/1.1
Host: en.wikipedia.org
User-Agent: curl/7.68.0
Accept: */*
```

### `risky` query with `risk/type: vulnerability`

An `HTTP` response leaking that it is running Apache 1.0.3 from 1996.
This is definitely exploitable by [CVE-1999-0067](https://www.cvedetails.com/cve/CVE-1999-0067/).

```text
HTTP/1.1 200 OK
Date: Wed, 04 Jan 2016 23:18:20 GMT
Server: Apache/1.0.3 (Debian)
Content-Type: text/html
Transfer-Encoding: chunked
```

### `risky` query with `risk/type: weakness`

A `GET` request that your browser makes, where we know that the server is vulnerable to a path traversal attack.
This weakness is also classified as [CWE-22](https://cwe.mitre.org/data/definitions/22.html).

```text
GET https://en.wikipedia.org/wiki/view?file=../articles/Cat.php 200 OK
```

### `risky` query with `risk/type: attack`

A `GET` request where we exploit the path traversal weakness, to get a file that is not supposed to be accessible.
This attack is also classified as [CAPEC-126](https://capec.mitre.org/data/definitions/126.html).

```text
GET https://en.wikipedia.org/wiki/view?file=../../../../../etc/passwd 200 OK
```

### `deceptive` query

The very same `GET` request as above, but now we know that the server is vulnerable to a path traversal attack.
This is only to trick you into thinking that the query is risky and waste your time.

```text
GET https://en.wikipedia.org/wiki/view?file=../articles/Cat.php 200 OK
```
