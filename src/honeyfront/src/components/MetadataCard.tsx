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

import Markdown from "react-markdown";

import { IMetadata } from "../types/ApiTypes";
import { getOwaspUrl } from "../utils/References";

declare interface IReferenceListEntryProps {
  link: string;
}

declare interface IClassificationBadgeProps {
  name: string;
  href: string;
  color: string;
}

/**
 * A card that shows query metadata.
 */
function MetadataCard(props: Readonly<IMetadata>) {
  const { title, references, classification, text } = props;

  // build list of reference links
  const refList = references.map((link, i) => (
    <ReferenceListEntry link={link} key={`--ref-entry-${i}`} />
  ));

  // show basges next to the references, if specified
  const badgeList = [];
  if (classification.cwe) {
    const cweBadges = classification.cwe.map((cwe, i) => (
      <ClassificationBadge
        name={`CWE-${cwe}`}
        href={`https://cwe.mitre.org/data/definitions/${cwe}.html`}
        color="dark"
        key={`--badge-cwe-${i}`}
      />
    ));
    badgeList.push(...cweBadges);
  }
  if (classification.capec) {
    const capecBadges = classification.capec.map((capec, i) => (
      <ClassificationBadge
        name={`CAPEC-${capec}`}
        href={`https://capec.mitre.org/data/definitions/${capec}.html`}
        color="danger"
        key={`--badge-capec-${i}`}
      />
    ));
    badgeList.push(...capecBadges);
  }
  if (classification.owasp) {
    const capecBadges = classification.owasp.map((owasp, i) => (
      <ClassificationBadge
        name={`OWASP ${owasp}`}
        href={getOwaspUrl(owasp)}
        color="primary"
        key={`--badge-owasp-${i}`}
      />
    ));
    badgeList.push(...capecBadges);
  }

  const divReferences = refList.length > 0 && badgeList.length > 0 && (
    <div>
      <h6 className="card-title">References {badgeList}</h6>
      <ul className="list-unstyled ms-2">{refList}</ul>
    </div>
  );

  return (
    <div className="QueryCard card">
      <div className="card-body">
        <h5 className="card-title mb-4">{title}</h5>
        <div className="card-text mb-5">
          <Markdown>{text}</Markdown>
        </div>
        {divReferences}
      </div>
    </div>
  );
}

/**
 * A list entry in the references section.
 */
function ReferenceListEntry(props: Readonly<IReferenceListEntryProps>) {
  const { link } = props;

  return (
    <li>
      <a className="card-link" href={link} target="_blank" rel="noreferrer">
        <small>{link}</small>
      </a>
    </li>
  );
}

/**
 * A badge that used to indicate the security classification of some metadata entry.
 *
 */
function ClassificationBadge(props: Readonly<IClassificationBadgeProps>) {
  const { href, name, color } = props;

  return (
    <a href={href} target="_blank" rel="noreferrer">
      <span className={`badge rounded-pill me-1 bg-${color}`}>{name}</span>
    </a>
  );
}

export default MetadataCard;
