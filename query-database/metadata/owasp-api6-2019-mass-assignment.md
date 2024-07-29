---
id: owasp-api6-2019-mass-assignment
title: "OWASP API6:2019 Mass Assignment"
references:
  - https://github.com/OWASP/API-Security/blob/master/editions/2019/en/0xa6-mass-assignment.md
author: The OWASP Foundation
license: CC-BY-SA-4.0
classification:
  owasp: ["API6:2019"]
  cwe: [915]
---

###### Threat agents & attack vectors

Exploitation usually requires an understanding of the business logic, objects'
relations, and the API structure. Exploitation of mass assignment is easier in APIs,
since by design they expose the underlying implementation of the application along with
the properties’ names.

###### Security weakness

Modern frameworks encourage developers to use functions that automatically bind input
from the client into code variables and internal objects. Attackers can use this
methodology to update or overwrite sensitive object’s properties that the developers
never intended to expose.

###### Impacts

Exploitation may lead to privilege escalation, data tampering, bypass of security
mechanisms, and more.
