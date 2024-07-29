---
id: http-request-smuggling-clte
title: HTTP Request Smuggling CL.TE vulnerability
references:
  - https://portswigger.net/web-security/request-smuggling/finding
author: Mario Kahlhofer <mario.kahlhofer@dynatrace.com>
license: CC-BY-SA-4.0
classification:
  cwe: [444]
  capec: [33]
---

Request smuggling abuses the parsing of HTTP requests to secrectly send additional,
often unauthorized or malicious, HTTP requests to the backend server.

The variant shown here shows a response confirming a CL.TE vulnerability,
where the frontend server uses the `Content-Length` header and the backend
uses the `Transfer-Encoding` header.

The resulting differential responses indicates that the request got processed
differently by the frontend and backend server.
