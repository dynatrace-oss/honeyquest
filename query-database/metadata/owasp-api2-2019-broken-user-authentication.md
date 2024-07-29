---
id: owasp-api2-2019-broken-user-authentication
title: "OWASP API2:2019 Broken User Authentication"
references:
  - https://github.com/OWASP/API-Security/blob/master/editions/2019/en/0xa2-broken-user-authentication.md
  - https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/
  - https://wiki.owasp.org/index.php/Top_10-2017_A2-Broken_Authentication
  - https://wiki.owasp.org/index.php/Top_10_2013-A2-Broken_Authentication_and_Session_Management
author: The OWASP Foundation
license: CC-BY-SA-4.0
classification:
  owasp: ["API2:2019", "A07:2021", "A02:2017", "A02:2013"]
  cwe: [798]
---

###### Threat agents & attack vectors

Authentication in APIs is a complex and confusing mechanism. Software and security
engineers might have misconceptions about what are the boundaries of authentication and
how to implement it correctly. In addition, the authentication mechanism is an easy
target for attackers, since it’s exposed to everyone. These two points makes the
authentication component potentially vulnerable to many exploits.

###### Security weakness

There are two sub-issues: 1. Lack of protection mechanisms: APIs endpoints that are
responsible for authentication must be treated differently from regular endpoints and
implement extra layers of protection 2. Misimplementation of the mechanism: The
mechanism is used / implemented without considering the attack vectors, or it’s the
wrong use case (e.g., an authentication mechanism designed for IoT clients might not be
the right choice for web applications).

###### Impacts

Attackers can gain control to other users’ accounts in the system, read their personal
data, and perform sensitive actions on their behalf, like money transactions and sending
personal messages.
