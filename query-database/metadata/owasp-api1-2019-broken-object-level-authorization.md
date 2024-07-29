---
id: owasp-api1-2019-broken-object-level-authorization
title: "OWASP API1:2019 Broken Object Level Authorization"
references:
  - https://github.com/OWASP/API-Security/blob/master/editions/2019/en/0xa1-broken-object-level-authorization.md
author: The OWASP Foundation
license: CC-BY-SA-4.0
classification:
  owasp: ["API1:2019"]
  cwe: [284, 285, 639]
---

###### Threat agents & attack vectors

Attackers can exploit API endpoints that are vulnerable to broken object level
authorization by manipulating the ID of an object that is sent within the request. This
may lead to unauthorized access to sensitive data. This issue is extremely common in
API-based applications because the server component usually does not fully track the
client’s state, and instead, relies more on parameters like object IDs, that are sent
from the client to decide which objects to access.

###### Security weakness

This has been the most common and impactful attack on APIs. Authorization and access
control mechanisms in modern applications are complex and wide-spread. Even if the
application implements a proper infrastructure for authorization checks, developers
might forget to use these checks before accessing a sensitive object. Access control
detection is not typically amenable to automated static or dynamic testing.

###### Impacts

Unauthorized access can result in data disclosure to unauthorized parties, data loss, or
data manipulation. Unauthorized access to objects can also lead to full account
takeover.
