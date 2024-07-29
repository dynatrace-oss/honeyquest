---
id: path-traversal
title: Path Traversal
references:
  - https://portswigger.net/web-security/file-path-traversal
  - https://owasp.org/www-community/attacks/Path_Traversal
author: Mario Kahlhofer <mario.kahlhofer@dynatrace.com>
license: CC-BY-SA-4.0
classification:
  owasp: ["A01:2021"]
  cwe: [22]
  capec: [126]
---

A path traversal vulnerability arises if a user can control
the path of a file or directory that is accessed by the application,
outside of the intended directory structure. This can often be identified
by seeing a sequence of `../` that tries to navigate the file system.
