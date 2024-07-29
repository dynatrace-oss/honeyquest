---
id: owasp-api7-2019-security-misconfiguration
title: "OWASP API7:2019 Security Misconfiguration"
references:
  - https://github.com/OWASP/API-Security/blob/master/editions/2019/en/0xa7-security-misconfiguration.md
author: The OWASP Foundation
license: CC-BY-SA-4.0
classification:
  owasp: ["API7:2019"]
  cwe: [2, 16, 388]
---

###### Threat agents & attack vectors

Attackers will often attempt to find unpatched flaws, common endpoints, or unprotected
files and directories to gain unauthorized access or knowledge of the system.

###### Security weakness

Security misconfiguration can happen at any level of the API stack, from the network
level to the application level. Automated tools are available to detect and exploit
misconfigurations such as unnecessary services or legacy options.

###### Impacts

Security misconfigurations can not only expose sensitive user data, but also system
details that may lead to full server compromise.
