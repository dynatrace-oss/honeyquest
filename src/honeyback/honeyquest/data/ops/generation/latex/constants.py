# Copyright 2024 Dynatrace LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Portions of this code, as identified in remarks, are provided under the
# Creative Commons BY-SA or the MIT license, and are provided without
# any warranty. In each of the remarks, we have provided attribution to the
# original creators and other attribution parties, along with the title of
# the code (if known) a copyright notice and a link to the license, and a
# statement indicating whether or not we have modified the code.

from typing import Dict, cast

EXPERIMENT_NAMES = {
    "pr0": "P0 Pre-Run",
    "ex1": "Security Professionals",
    "ex2": "Red Team",
    "ex3": "Mixed",
    "ctf1": "CTF Players",
}

JOB_NAMES = {
    "student": "Student",
    "dev": "Developer",
    "ops": "Admin",
    "secops": "SecOps",
    "biz": "Manager",
    "research": "Researcher",
    "other": "Other",
}

RANK_NAMES = {
    "none": "None",
    "little": "Little",
    "good": "Good",
    "advanced": "Advanced",
    "expert": "Expert",
}

LABEL_NAMES = {
    "neutral": "Neutral",
    "risky": "Risky",
    "deceptive": "Deceptive",
}

LABEL_NAMES_ABBRV = {
    "neutral": "N",
    "risky": "R",
    "deceptive": "D",
}

TYPE_NAMES = {
    "all": "All Techniques",
    "filesystem": "File System",
    "httpheaders": "HTTP Responses",
    "networkrequests": "HTTP Requests",
    "htaccess": ".htaccess Files",
}

TYPE_NAMES_ABBRV = {
    "-": "-",
    "all": "A",
    "filesystem": "F",
    "httpheaders": "P",
    "networkrequests": "S",
    "htaccess": "H",
}

PRESENT_WEAKNESS = {
    "filesystem-backup": "\\texttt{backup.tar.gz}",
    "filesystem-dns-update-key": "\\texttt{ddns-update-key}",
    "filesystem-kubernetes-manifests": "\\texttt{k8s-manifests}",
    "filesystem-openvpn-config": "\\texttt{salphard.ovpn}",
    "filesystem-private-key": "\\texttt{private-key.pem}",
    "httpheaders-proxy-auth-leak": "Proxy Auth. Leak",
    "httpheaders-cross-domain-referer-leakage": "Referer Leak",
    "networkrequests-log-spam-endpoint": "Log Spam Endpoint",
    "networkrequests-insecure-http": "Insecure HTTP",
}

PRESENT_VULNERABILITY = {
    "httpheaders-outdated-php": "Outdated PHP",
    "httpheaders-outdated-apache": "Outdated Server",
}

PRESENT_ATTACK = {
    "httpheaders-request-smuggling-clte": "Request Smugg.",
    "networkrequests-broken-function-level-authorization": "Brk. Fun. Lvl. Auth.",
    "networkrequests-broken-object-level-authorization": "Brk. Obj. Lvl. Auth.",
    "networkrequests-password-hashes-in-query-parameters": "Pass. Hash Param.",
    "networkrequests-dev-endpoint-accessible": "Developer Endpoint",
    "networkrequests-no-rate-limiting": "No Rate Limiting",
    "networkrequests-mass-assignment": "Mass Assignment",
    "networkrequests-nosql-injection": "NoSQL Injection",
}

PRESENT_RISK = {
    None: "-",
    "all": "All Risks",
}

PRESENT_RISK.update(cast(Dict[str | None, str], PRESENT_WEAKNESS))  # for mypy
PRESENT_RISK.update(cast(Dict[str | None, str], PRESENT_VULNERABILITY))  # for mypy
PRESENT_RISK.update(cast(Dict[str | None, str], PRESENT_ATTACK))  # for mypy

HONEYWIRE_QUERY_TYPE = {
    None: "-",
    "all": "all",
    "filesystem-backup": "filesystem",
    "filesystem-card3rz": "filesystem",
    "filesystem-config": "filesystem",
    "filesystem-customer-list": "filesystem",
    "filesystem-keys": "filesystem",
    "filesystem-passwords": "filesystem",
    "filesystem-private-key": "filesystem",
    "filesystem-rowe": "filesystem",
    "filesystem-spam-list": "filesystem",
    "htaccess-admin-redirect": "htaccess",
    "httpheaders-apiserver": "httpheaders",
    "httpheaders-devtoken": "httpheaders",
    "httpheaders-admin-cookie": "httpheaders",
    "httpheaders-path-traversal": "httpheaders",
    "httpheaders-proxy-referer": "httpheaders",
    "networkrequests-admin-false": "networkrequests",
    "networkrequests-cleartext-password": "networkrequests",
    "networkrequests-dev-endpoint": "networkrequests",
    "networkrequests-idor-read-secrets": "networkrequests",
    "networkrequests-log-endpoint": "networkrequests",
    "networkrequests-mass-assignment": "networkrequests",
    "networkrequests-path-traversal": "networkrequests",
    "networkrequests-sessid-parameter": "networkrequests",
    "networkrequests-system-parameter": "networkrequests",
    "networkrequests-unescaped-javascript": "networkrequests",
    "networkrequests-unescaped-json": "networkrequests",
}

HONEYWIRE_NAMES = {
    None: "-",
    "all": "All Techniques",
    "filesystem-backup": "\\texttt{backup.tar.gz}",
    "filesystem-card3rz": "\\texttt{card3rz\\_reg\\_details.html}",
    "filesystem-config": "\\texttt{config.ini}",
    "filesystem-customer-list": "\\texttt{customer\\_list\\_2010.html}",
    "filesystem-keys": "\\texttt{keys.json}",
    "filesystem-passwords": "\\texttt{passwords.txt}",
    "filesystem-private-key": "\\texttt{private-key.pem}",
    "filesystem-rowe": "Rowe et al.",
    "filesystem-spam-list": "\\texttt{SPAM\\_list.pdf}",
    "htaccess-admin-redirect": "Admin Redirect",
    "httpheaders-apiserver": "API Server",
    "httpheaders-devtoken": "Developer Token",
    "httpheaders-admin-cookie": "Cookie",
    "httpheaders-path-traversal": "Path Traversal",
    "httpheaders-proxy-referer": "Proxy Referer",
    "networkrequests-admin-false": "Admin Param.",
    "networkrequests-cleartext-password": "Clear-Text Pass.",
    "networkrequests-dev-endpoint": "Developer Endpoint",
    "networkrequests-idor-read-secrets": "IDOR Secrets",
    "networkrequests-log-endpoint": "Log Endpoint",
    "networkrequests-mass-assignment": "Mass Assignment",
    "networkrequests-path-traversal": "Path Traversal",
    "networkrequests-sessid-parameter": "SESSID Param.",
    "networkrequests-system-parameter": "System Param.",
    "networkrequests-unescaped-javascript": "Unescaped JS",
    "networkrequests-unescaped-json": "Unespaced JSON",
}

GROUPER_NAMES = {
    "deceptive": "All Deceptive Queries",
    "risky": "All Risky Queries",
    "neutral": "All Neutral Queries",
    "filesystem/deceptive": TYPE_NAMES["filesystem"],
    "filesystem/risky": TYPE_NAMES["filesystem"],
    "filesystem/neutral": TYPE_NAMES["filesystem"],
    "htaccess/deceptive": TYPE_NAMES["htaccess"],
    "htaccess/risky": TYPE_NAMES["htaccess"],
    "htaccess/neutral": TYPE_NAMES["htaccess"],
    "httpheaders/deceptive": TYPE_NAMES["httpheaders"],
    "httpheaders/risky": TYPE_NAMES["httpheaders"],
    "httpheaders/neutral": TYPE_NAMES["httpheaders"],
    "networkrequests/deceptive": TYPE_NAMES["networkrequests"],
    "networkrequests/risky": TYPE_NAMES["networkrequests"],
    "networkrequests/neutral": TYPE_NAMES["networkrequests"],
}

GROUPER_NAMES.update(TYPE_NAMES)

CITE_LEET11 = "https://www.usenix.org/conference/leet11/exposing-lack-privacy-file-hosting-services"
CITE_MAP_URL = {
    CITE_LEET11: "Nikiforakis2011:ExposingLackPrivacy",
}

CITE_MAP_DOI = {
    "10.1145/3140549.3140555": "Han2017:EvaluationDeceptionBasedWeb",
    "10.1109/SPW54247.2022.9833858": "Sahin2022:MeasuringDevelopersWeb",
    "10.14722/madweb.2020.23005": "Sahin2020:LessonsLearnedSunDEW",
    "10.1109/IAW.2006.1652099": "Rowe2006:FakeHoneypotsDefensive",
    "10.4304/JCP.2.2.25-36": "Rowe2007:DefendingCyberspaceFake",
    "10.1109/MIPRO.2015.7160478": "Petrunic2015:HoneytokensActiveDefense",
}
