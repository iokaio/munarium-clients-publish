#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""The release plan: what one dispatch of publish.yml builds and publishes.

    python3 scripts/plan.py --source iokaio/munarium-matrix --family matrix-clients \
        --tag matrix-clients-v1.2.0 --src <checkout of that tag> [--sha <commit>] \
        [--publish-nuget] [--publish-pypi --pypi-target pypi] [--publish-maven] [--publish-crates]

Reads two files and trusts neither blindly:

  sources.json               (this repository) which source repositories and
                             families may be published at all
  <src>/clients/release.json (the source, at the tag) how each family is
                             versioned, tagged, gated and packaged

and refuses the run unless the family is allowed for that source, the tag is
exactly the family's tag pattern at the version the tagged tree declares, and
every package names a supported registry with the fields its build needs.
Then it asks each registry whether that version already exists, so a package
that is already published is built (as proof) but never published again.

Prints `plan=<json>` for $GITHUB_OUTPUT and, with --summary, appends a table
to that file. Stdlib only; the registry lookups are anonymous GETs.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SCHEMA = 1

# What each registry's build needs from release.json, beyond `registry` and `dir`.
REQUIRED = {
    "nuget": ("id", "project", "tests"),
    "pypi": ("name",),
    "maven": ("group", "artifact"),
    "crates": ("crate",),
}
SAFE_PATH = re.compile(r"^(?!/)(?!.*(^|/)\.\.(/|$))[A-Za-z0-9._/-]+$")
SAFE_FLAGS = re.compile(r"^(--[a-z][a-z-]*( --[a-z][a-z-]*)*)?$")
SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class PlanError(Exception):
    pass


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise PlanError(f"{path}: not found") from None
    except json.JSONDecodeError as e:
        raise PlanError(f"{path}: not valid JSON ({e})") from None


def safe_path(value: str, what: str) -> str:
    """A repository-relative path: no absolute path, no `..`, no shell metacharacters."""
    if not isinstance(value, str) or not SAFE_PATH.match(value):
        raise PlanError(f"{what}: {value!r} is not a plain repository-relative path")
    return value


def safe_identifier(value: str, what: str) -> str:
    """A registry identifier that is also safe in paths, labels and shells."""
    if not isinstance(value, str) or not SAFE_IDENTIFIER.fullmatch(value):
        raise PlanError(f"{what}: {value!r} is not a plain registry identifier")
    return value


def read_version(src: Path, spec: dict) -> str:
    """`{"file": "server/Cargo.toml", "toml": "workspace.package.version"}`."""
    file = safe_path(spec.get("file", ""), "version.file")
    keys = spec.get("toml", "")
    if not keys:
        raise PlanError("version: needs `file` and a dotted `toml` key")
    try:
        node = tomllib.loads((src / file).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise PlanError(f"version.file {file}: not in the tagged tree") from None
    for key in keys.split("."):
        if not isinstance(node, dict) or key not in node:
            raise PlanError(f"version: {file} has no {keys}")
        node = node[key]
    if not isinstance(node, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+([-+][0-9A-Za-z.-]+)?", node):
        raise PlanError(f"version: {file} {keys} = {node!r} is not a release version")
    return node


def validate(sources: dict, release: dict, source: str, family: str, tag: str, src: Path) -> dict:
    allowed = sources.get(source)
    if allowed is None:
        raise PlanError(f"{source} is not a source this repository publishes (sources.json)")
    if family not in allowed.get("families", []):
        raise PlanError(f"{family} is not a family sources.json allows for {source}: {allowed.get('families')}")
    if release.get("schema") != SCHEMA:
        raise PlanError(f"clients/release.json: schema must be {SCHEMA}")
    fam = release.get("families", {}).get(family)
    if fam is None:
        raise PlanError(f"clients/release.json at {tag} declares no family {family}")

    version = read_version(src, fam.get("version", {}))
    expected = fam.get("tag", "").replace("{version}", version)
    if "{version}" not in fam.get("tag", ""):
        raise PlanError(f"{family}: tag pattern must contain {{version}}")
    if tag != expected:
        raise PlanError(f"tag {tag} does not name this tree's {family} release; it must be {expected}")

    gates = release.get("gates", [])
    if not isinstance(gates, list) or not all(isinstance(g, str) and g.strip() for g in gates):
        raise PlanError("clients/release.json: gates must be a list of commands")
    artifact_check = safe_path(release.get("artifact_check", ""), "artifact_check")

    copies = []
    for c in fam.get("copy", []):
        copies.append({"from": safe_path(c.get("from", ""), "copy.from"), "to": safe_path(c.get("to", ""), "copy.to")})

    out = {"nuget": [], "pypi": [], "maven": [], "crates": []}
    for i, pkg in enumerate(fam.get("packages", [])):
        reg = pkg.get("registry")
        if reg not in REQUIRED:
            raise PlanError(f"{family} package {i}: registry {reg!r} is not one of {sorted(REQUIRED)}")
        entry = {"registry": reg, "dir": safe_path(pkg.get("dir", ""), f"{family} package {i} dir"),
                 "version": version}
        for field in REQUIRED[reg]:
            value = pkg.get(field)
            if not isinstance(value, str) or not value:
                raise PlanError(f"{family} package {i} ({reg}): missing {field}")
            entry[field] = (
                safe_path(value, f"{family} package {i} {field}")
                if field in ("project", "tests")
                else safe_identifier(value, f"{family} package {i} {field}")
            )
        if reg == "crates":
            flags = pkg.get("package_flags", "")
            if not SAFE_FLAGS.match(flags):
                raise PlanError(f"{family} package {i}: package_flags {flags!r} must be plain --flags")
            entry["package_flags"] = flags
        if reg == "maven":
            entry["group_path"] = entry["group"].replace(".", "/")
        entry["label"] = entry.get("id") or entry.get("name") or entry.get("artifact") or entry.get("crate")
        out[reg].append(entry)
    if not any(out.values()):
        raise PlanError(f"{family}: no packages")
    return {"version": version, "gates": gates, "artifact_check": artifact_check, "copy": copies, **out}


def fetch(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": "iokaio/munarium-clients-publish (github actions)"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""


def published(entry: dict, pypi_host: str) -> tuple[bool, str]:
    v = entry["version"]
    reg = entry["registry"]
    if reg == "nuget":
        code, body = fetch(f"https://api.nuget.org/v3-flatcontainer/{entry['id'].lower()}/index.json")
        return code == 200 and v in json.loads(body).get("versions", []), "NuGet"
    if reg == "pypi":
        code, _ = fetch(f"https://{pypi_host}/pypi/{entry['name']}/{v}/json")
        return code == 200, pypi_host
    if reg == "maven":
        code, _ = fetch(f"https://repo1.maven.org/maven2/{entry['group_path']}/{entry['artifact']}/{v}/")
        return code == 200, "Maven Central"
    code, _ = fetch(f"https://crates.io/api/v1/crates/{entry['crate']}/{v}")
    return code == 200, "crates.io"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--source", required=True)
    ap.add_argument("--family", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--src", required=True, type=Path, help="checkout of the source at the tag")
    ap.add_argument("--sha", default="")
    ap.add_argument("--publish-nuget", action="store_true")
    ap.add_argument("--publish-pypi", action="store_true")
    ap.add_argument("--pypi-target", choices=("testpypi", "pypi"), default="testpypi")
    ap.add_argument("--publish-maven", action="store_true")
    ap.add_argument("--publish-crates", action="store_true")
    ap.add_argument("--summary", type=Path, help="append a Markdown table to this file")
    ap.add_argument("--offline", action="store_true", help="skip the registry lookups (tests)")
    a = ap.parse_args(argv)

    try:
        sources = load_json(HERE / "sources.json")
        release = load_json(a.src / "clients" / "release.json")
        plan = validate(sources, release, a.source, a.family, a.tag, a.src)
    except PlanError as e:
        print(f"::error::{e}", file=sys.stderr)
        return 1

    pypi_host = "test.pypi.org" if a.pypi_target == "testpypi" else "pypi.org"
    selected = {"nuget": a.publish_nuget, "pypi": a.publish_pypi, "maven": a.publish_maven, "crates": a.publish_crates}
    for reg in ("nuget", "pypi", "maven", "crates"):
        for entry in plan[reg]:
            entry["published"], entry["registry_name"] = (False, reg) if a.offline else published(entry, pypi_host)
        plan[f"{reg}_todo"] = [e for e in plan[reg] if not e["published"]]
        if selected[reg] and not plan[f"{reg}_todo"] and plan[reg]:
            print(f"::notice::every {reg} package of {a.family} {plan['version']} is already published", file=sys.stderr)

    plan.update({"source": a.source, "family": a.family, "tag": a.tag, "sha": a.sha})
    print("plan=" + json.dumps(plan))

    if a.summary:
        with a.summary.open("a", encoding="utf-8") as s:
            s.write(f"## {a.family} {plan['version']} from {a.source}\n\n"
                    f"tag `{a.tag}` at `{a.sha or 'unresolved'}`\n\n"
                    "| package | version | registry | state |\n|---|---|---|---|\n")
            for reg in ("nuget", "pypi", "maven", "crates"):
                for e in plan[reg]:
                    state = "already published, skipped" if e["published"] else "to publish (if its registry is ticked)"
                    s.write(f"| `{e['label']}` | {e['version']} | {e['registry_name']} | {state} |\n")
    for reg in ("nuget", "pypi", "maven", "crates"):
        for e in plan[reg]:
            if e["published"]:
                print(f"::notice::{e['registry_name']} already has {e['label']} {e['version']}; "
                      "it will be built but not published", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
