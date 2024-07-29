---
id: owasp-api9-2019-improper-assets-management
title: "OWASP API9:2019 Improper Assets Management"
references:
  - https://github.com/OWASP/API-Security/blob/master/editions/2019/en/0xa9-improper-assets-management.md
  - https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/
author: The OWASP Foundation
license: CC-BY-SA-4.0
classification:
  owasp: ["API9:2019", "A08:2021"]
  cwe: [1059]
---

###### Threat agents & attack vectors

Old API versions are usually unpatched and are an easy way to compromise systems without
having to fight state-of-the-art security mechanisms, which might be in place to protect
the most recent API versions.

###### Security weakness

Outdated documentation makes it more difficult to find and/or fix vulnerabilities. Lack
of assets inventory and retire strategies leads to running unpatched systems, resulting
in leakage of sensitive data. It’s common to find unnecessarily exposed API hosts
because of modern concepts like microservices, which make applications easy to deploy
and independent (e.g., cloud computing, k8s).

###### Impacts

Attackers may gain access to sensitive data, or even takeover the server through old,
unpatched API versions connected to the same database.
