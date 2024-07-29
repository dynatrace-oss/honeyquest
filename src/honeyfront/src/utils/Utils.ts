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

/**
 * A random color, e.g. formatted like `#3ec852`.
 */
export function randomColor(): string {
  return "#" + Math.round(0xffffff * Math.random()).toString(16);
}

/**
 * A logical XOR, because JavaScript has no operator for that.
 *
 * @param a The first value
 * @param b The second value
 * @returns The XOR of the two values
 */
export function xor(a: boolean, b: boolean): boolean {
  return (a && !b) || (!a && b);
}

/**
 * From a set of numbers, e.g. `1,2,3,5,7,8,9`,
 * gives a readable range, e.g. `1-3, 5, 7-9`.
 *
 * @param set The set of numbers
 * @returns A string describing the range
 */
export function readableRange(set: Set<number>): string {
  if (set.size === 0) return "";

  const ordered = Array.from(set).sort((a, b) => a - b);
  const ranges: string[] = [];

  // generate ranges
  let [start, last]: [number, number] = [ordered[0], ordered[0]];
  for (const i of ordered.slice(1)) {
    if (last + 1 === i) {
      last = i;
    } else {
      ranges.push(start === last ? `${start}` : `${start}-${last}`);
      start = i;
      last = i;
    }
  }

  // possibly close the last range
  ranges.push(start === last ? `${start}` : `${start}-${last}`);

  return ranges.join(", ");
}

/**
 * From a set of numbers, e.g. `1,2,3,5,7,8,9` with prefix `line`,
 * gives a readable range, e.g. `lines 1-3, 5, 7-9`, that respects
 * singular and plural for the prefix.
 *
 * @param set The set of numbers
 * @param prefix The prefix to use
 * @returns A string describing the range, with the prefix
 */
export function prefixedReadableRange(
  set: Set<number>,
  prefix: string,
): string {
  const range = readableRange(set);
  const term = set.size === 1 ? prefix : prefix + "s";
  return range ? `${term} ${range}` : "";
}

/**
 * A short helper for building CSS class names. Use it like
 * `addSuffixIf("MyDiv", "selected", isSelected)` to either
 * get `MyDiv` or `MyDiv selected` if the condition is true.
 *
 * @param text The text to add the suffix to.
 * @param suffix The suffix to add, separated by a space unless text is empty
 * @param condition Only adds the suffix if the condition is satisfied
 * @returns The text with the suffix, if the condition is satisfied
 */
export function addSuffixIf(
  text: string | undefined,
  suffix: string,
  condition: boolean | undefined,
): string | undefined {
  if (condition) return !text ? suffix : `${text} ${suffix}`;
  return text;
}

/**
 * A short helper for building CSS class names. Use it like
 * `addSuffixIfMultiple("MyDiv", {"a": ifA, "b": ifB})` to either
 * get `MyDiv` or `MyDiv a` or `MyDiv b` or `MyDiv a b` depending
 * on the conditions.
 *
 * @param text The text to add the suffix to.
 * @param suffixes Keys are the suffixes, values are the conditions
 * @returns The text with the suffixes, if the conditions are satisfied
 */
export function addSuffixIfMultiple(
  text: string | undefined,
  suffixes: Record<string, boolean | undefined>,
): string | undefined {
  let result = text;
  for (const suffix in suffixes) {
    result = addSuffixIf(result, suffix, suffixes[suffix]);
  }
  return result;
}

/**
 * Drops element from array by value
 * @param arr The array
 * @param item The element to drop
 * @returns
 */
export function drop<E>(arr: E[], item: E) {
  const index = arr.indexOf(item);
  if (index !== -1) arr.splice(index, 1);
}

/**
 * Grabs a key from a list of dictionaries, returning the first value
 * from the first dictionary that contains the key. If the key is not
 * present in any dictionary, returns the default value. Further, the
 * value is transformed to the specified type.
 *
 * @param key The key to grab
 * @param list The list of dictionaries
 * @param transform The type to transform the value to
 * @param defaultValue Default value if the key is not present
 * @returns The value of the key, or null if it is not present
 */
export function grabKey<V, R>(
  key: string,
  list: Record<string, V>[],
  transform: (v: V) => R,
  defaultValue: R,
): R {
  for (const element of list) {
    if (key in element) {
      return transform(element[key]);
    }
  }
  return defaultValue;
}

/**
 * Following the line annotation syntax in QUERY_DATABASE.md,
 * extracts the ranges specified in the syntax.
 *
 * @param syntax The line annotation syntax (LAS)
 * @returns A list of ranges
 */
export function parseLAS(syntax: string): { from: number; to: number }[] {
  return syntax.split(",").map((las) => {
    const woPrefix = las.slice(1);
    const woCols = woPrefix.split(":")[0];
    const [from, to] = woCols.split("-").map((e) => parseInt(e));
    return { from, to: to || from };
  });
}

/**
 * Checks if the line is in the range specified in the
 * line annotation syntax (LAS). Use `extractLASRanges`
 * to parse the ranges from a LAS string.
 *
 * @param line The line number to check
 * @param ranges A list of ranges
 */
export function inLAS(
  line: number,
  ranges: { from: number; to: number }[],
): boolean {
  for (const { from, to } of ranges) {
    if (line >= from && line <= to) {
      return true;
    }
  }

  // not in any range
  return false;
}
