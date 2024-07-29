---
id: owasp-api3-2019-excessive-data-exposure
title: "OWASP API3:2019 Excessive Data Exposure"
references:
  - https://github.com/OWASP/API-Security/blob/master/editions/2019/en/0xa3-excessive-data-exposure.md
author: The OWASP Foundation
license: CC-BY-SA-4.0
classification:
  owasp: ["API3:2019"]
  cwe: [213]
---

###### Threat agents & attack vectors

Exploitation of Excessive Data Exposure is simple, and is usually performed by sniffing
the traffic to analyze the API responses, looking for sensitive data exposure that
should not be returned to the user.

###### Security weakness

APIs rely on clients to perform the data filtering. Since APIs are used as data sources,
sometimes developers try to implement them in a generic way without thinking about the
sensitivity of the exposed data. Automatic tools usually can’t detect this type of
vulnerability because it’s hard to differentiate between legitimate data returned from
the API, and sensitive data that should not be returned without a deep understanding of
the application.

###### Impacts

Excessive Data Exposure commonly leads to exposure of sensitive data.
