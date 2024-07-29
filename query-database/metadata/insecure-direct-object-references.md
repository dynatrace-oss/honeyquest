---
id: insecure-direct-object-references
title: Insecure Direct Object References (IDOR)
references:
  - https://portswigger.net/web-security/access-control/idor
  - https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html
author: Mario Kahlhofer <mario.kahlhofer@dynatrace.com>
license: CC-BY-SA-4.0
classification:
  owasp: ["A04:2013"]
  cwe: [22, 639]
---

Insecure direct object references (IDOR) are vulnerabilities where potentially sensitive
content can be retrieved by guessing (predictable) identifiers (IDs).
