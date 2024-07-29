---
id: owasp-api8-2019-injection
title: "OWASP API8:2019 Injection"
references:
  - https://github.com/OWASP/API-Security/blob/master/editions/2019/en/0xa8-injection.md
  - https://owasp.org/Top10/A03_2021-Injection/
  - https://wiki.owasp.org/index.php/Top_10-2017_A1-Injection
  - https://wiki.owasp.org/index.php/Top_10_2013-A1-Injection
author: The OWASP Foundation
license: CC-BY-SA-4.0
classification:
  owasp: ["API8:2019", "A03:2021", "A01:2017", "A01:2013"]
  cwe: [77, 89]
---

###### Threat agents & attack vectors

Attackers will feed the API with malicious data through whatever injection vectors are
available (e.g., direct input, parameters, integrated services, etc.), expecting it to
be sent to an interpreter.

###### Security weakness

Injection flaws are very common and are often found in SQL, LDAP, or NoSQL queries, OS
commands, XML parsers, and ORM. These flaws are easy to discover when reviewing the
source code. Attackers can use scanners and fuzzers.

###### Impacts

Injection can lead to information disclosure and data loss. It may also lead to DoS, or
complete host takeover.
