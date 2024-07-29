---
id: owasp-api4-2019-lack-of-resources-and-rate-limiting
title: "OWASP API4:2019 Lack of Resources & Rate Limiting"
references:
  - https://github.com/OWASP/API-Security/blob/master/editions/2019/en/0xa4-lack-of-resources-and-rate-limiting.md
author: The OWASP Foundation
license: CC-BY-SA-4.0
classification:
  owasp: ["API4:2019"]
  cwe: [307, 770]
---

###### Threat agents & attack vectors

Exploitation requires simple API requests. No authentication is required. Multiple
concurrent requests can be performed from a single local computer or by using cloud
computing resources.

###### Security weakness

It’s common to find APIs that do not implement rate limiting or APIs where limits are
not properly set.

###### Impacts

Exploitation may lead to DoS, making the API unresponsive or even unavailable.
