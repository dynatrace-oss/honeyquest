// Copyright 2024 Dynatrace LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// Portions of this code, as identified in remarks, are provided under the
// Creative Commons BY-SA or the MIT license, and are provided without
// any warranty. In each of the remarks, we have provided attribution to the
// original creators and other attribution parties, along with the title of
// the code (if known) a copyright notice and a link to the license, and a
// statement indicating whether or not we have modified the code.

/* eslint-disable @typescript-eslint/naming-convention */

// prettier-ignore
const owaspTopTen: Record<string, string> = {
  /* OWASP Top 10 - 2013 */
  "A01:2013": "https://wiki.owasp.org/index.php/Top_10_2013-A1-Injection",
  "A02:2013": "https://wiki.owasp.org/index.php/Top_10_2013-A2-Broken_Authentication_and_Session_Management",
  "A03:2013": "https://wiki.owasp.org/index.php/Top_10_2013-A3-Cross-Site_Scripting_(XSS)",
  "A04:2013": "https://wiki.owasp.org/index.php/Top_10_2013-A4-Insecure_Direct_Object_References",
  "A05:2013": "https://wiki.owasp.org/index.php/Top_10_2013-A5-Security_Misconfiguration",
  "A06:2013": "https://wiki.owasp.org/index.php/Top_10_2013-A6-Sensitive_Data_Exposure",
  "A07:2013": "https://wiki.owasp.org/index.php/Top_10_2013-A7-Missing_Function_Level_Access_Control",
  "A08:2013": "https://wiki.owasp.org/index.php/Top_10_2013-A8-Cross-Site_Request_Forgery_(CSRF)",
  "A09:2013": "https://wiki.owasp.org/index.php/Top_10_2013-A9-Using_Components_with_Known_Vulnerabilities",
  "A10:2013": "https://wiki.owasp.org/index.php/Top_10_2013-A10-Unvalidated_Redirects_and_Forwards",
  /* OWASP Top 10 - 2017 */
  "A01:2017": "https://wiki.owasp.org/index.php/Top_10-2017_A1-Injection",
  "A02:2017": "https://wiki.owasp.org/index.php/Top_10-2017_A2-Broken_Authentication",
  "A03:2017": "https://wiki.owasp.org/index.php/Top_10-2017_A3-Sensitive_Data_Exposure",
  "A04:2017": "https://wiki.owasp.org/index.php/Top_10-2017_A4-XML_External_Entities_(XXE)",
  "A05:2017": "https://wiki.owasp.org/index.php/Top_10-2017_A5-Broken_Access_Control",
  "A06:2017": "https://wiki.owasp.org/index.php/Top_10-2017_A6-Security_Misconfiguration",
  "A07:2017": "https://wiki.owasp.org/index.php/Top_10-2017_A7-Cross-Site_Scripting_(XSS)",
  "A08:2017": "https://wiki.owasp.org/index.php/Top_10-2017_A8-Insecure_Deserialization",
  "A09:2017": "https://wiki.owasp.org/index.php/Top_10-2017_A9-Using_Components_with_Known_Vulnerabilities",
  "A10:2017": "https://wiki.owasp.org/index.php/Top_10-2017_A10-Insufficient_Logging%26Monitoring",
  /* OWASP Top 10 - 2021 */
  "A01:2021": "https://owasp.org/Top10/A01_2021-Broken_Access_Control/",
  "A02:2021": "https://owasp.org/Top10/A02_2021-Cryptographic_Failures/",
  "A03:2021": "https://owasp.org/Top10/A03_2021-Injection/",
  "A04:2021": "https://owasp.org/Top10/A04_2021-Insecure_Design/",
  "A05:2021": "https://owasp.org/Top10/A05_2021-Security_Misconfiguration/",
  "A06:2021": "https://owasp.org/Top10/A06_2021-Vulnerable_and_Outdated_Components/",
  "A07:2021": "https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/",
  "A08:2021": "https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/",
  "A09:2021": "https://owasp.org/Top10/A09_2021-Security_Logging_and_Monitoring_Failures/",
  "A10:2021": "https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery_%28SSRF%29/",
  /* OWASP API Security Top 10 - 2019 */
  "API1:2019": "https://github.com/OWASP/API-Security/blob/master/editions/2019/en/0xa1-broken-object-level-authorization.md",
  "API2:2019": "https://github.com/OWASP/API-Security/blob/master/editions/2019/en/0xa2-broken-user-authentication.md",
  "API3:2019": "https://github.com/OWASP/API-Security/blob/master/editions/2019/en/0xa3-excessive-data-exposure.md",
  "API4:2019": "https://github.com/OWASP/API-Security/blob/master/editions/2019/en/0xa4-lack-of-resources-and-rate-limiting.md",
  "API5:2019": "https://github.com/OWASP/API-Security/blob/master/editions/2019/en/0xa5-broken-function-level-authorization.md",
  "API6:2019": "https://github.com/OWASP/API-Security/blob/master/editions/2019/en/0xa6-mass-assignment.md",
  "API7:2019": "https://github.com/OWASP/API-Security/blob/master/editions/2019/en/0xa7-security-misconfiguration.md",
  "API8:2019": "https://github.com/OWASP/API-Security/blob/master/editions/2019/en/0xa8-injection.md",
  "API9:2019": "https://github.com/OWASP/API-Security/blob/master/editions/2019/en/0xa9-improper-assets-management.md",
  "API10:2019": "https://github.com/OWASP/API-Security/blob/master/editions/2019/en/0xaa-insufficient-logging-monitoring.md",
};

/* eslint-enable @typescript-eslint/naming-convention */

/**
 * Gets the correct OWASP URL for the given OWASP ID.
 */
export function getOwaspUrl(owaspId: string): string {
  return owaspTopTen[owaspId] ?? "https://owasp.org/www-project-top-ten/";
}

export function getNiceQueryTypeName(type: string): string {
  const nbsp = "\u00A0";
  switch (type) {
    case "httpheaders":
      return `HTTP${nbsp}headers`;
    case "htaccess":
      return `.htaccess${nbsp}file`;
    case "filesystem":
      return `filesystem${nbsp}listing`;
    case "networkrequests":
      return `network${nbsp}requests`;
    default:
      return `${type}${nbsp}query`;
  }
}

export function getTypeDescription(type: string): string {
  switch (type) {
    case "httpheaders":
      return "You either see HTTP response or request headers, but always without any payload";
    case "htaccess":
      return "You see the configuration directives in an .htaccess file, which is used to configure Apache web servers";
    case "filesystem":
      return "You see the output of the command `ls -lah` listing the file type and permissions, the number of links to the file, the owner, the group, the size, the last modification date and the file name";
    case "networkrequests":
      return "You see the network requests made by a web application, listing the time in seconds since the start of the request, the request method, the full URL, the response status code, and the response size, if the response was not empty";
    default:
      return "";
  }
}

export function getExploitDescription(type: string): string {
  switch (type) {
    case "httpheaders":
      return "An exploit mark means that you see a vulnerability / or want to use this header in an attack";
    case "htaccess":
      return "An exploit mark means that you see a vulnerability / want to access this path / or want to use it in an attack";
    case "filesystem":
      return "An exploit mark means that you see a vulnerability / want to examine this file or directory / or attack it";
    case "networkrequests":
      return "An exploit mark means that you see a vulnerability / want to access this path / or attack it";
    default:
      return "Click to the left of a line to mark lines to exploit";
  }
}

export function getTrapDescription(type: string): string {
  switch (type) {
    case "httpheaders":
      return "A trap mark means that you think this header is a trap you must avoid";
    case "htaccess":
      return "A trap mark means that you think this directive is a trap you must avoid";
    case "filesystem":
      return "A trap mark means that you think this file or directory is a trap you must avoid";
    case "networkrequests":
      return "A trap mark means that you think this request is a trap you must avoid";
    default:
      return "Click to the right of a line to mark traps to avoid";
  }
}
