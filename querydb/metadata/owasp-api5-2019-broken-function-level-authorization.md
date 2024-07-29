---
id: owasp-api5-2019-broken-function-level-authorization
title: "OWASP API5:2019 Broken Function Level Authorization"
references:
  - https://github.com/OWASP/API-Security/blob/master/editions/2019/en/0xa5-broken-function-level-authorization.md
author: The OWASP Foundation
license: CC-BY-SA-4.0
classification:
  owasp: ["API5:2019"]
  cwe: [285]
---

###### Threat agents & attack vectors

Exploitation requires the attacker to send legitimate API calls to the API endpoint that
they should not have access to. These endpoints might be exposed to anonymous users or
regular, non-privileged users. It’s easier to discover these flaws in APIs since APIs
are more structured, and the way to access certain functions is more predictable (e.g.,
replacing the HTTP method from GET to PUT, or changing the “users” string in the URL to
"admins").

###### Security weakness

Authorization checks for a function or resource are usually managed via configuration,
and sometimes at the code level. Implementing proper checks can be a confusing task,
since modern applications can contain many types of roles or groups and complex user
hierarchy (e.g., sub-users, users with more than one role).

###### Impacts

Such flaws allow attackers to access unauthorized functionality. Administrative
functions are key targets for this type of attack.
