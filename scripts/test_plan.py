# SPDX-License-Identifier: Apache-2.0
"""Offline tests for plan.py: each refusal the planner exists to make."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import plan

SOURCES = {"iokaio/example": {"branch": "main", "families": ["things"]}}


def release(**family_overrides) -> dict:
    family = {
        "tag": "things-v{version}",
        "version": {"file": "clients/python/pyproject.toml", "toml": "project.version"},
        "packages": [
            {"registry": "pypi", "name": "example-things", "dir": "clients/python"},
            {"registry": "nuget", "id": "Example.Things", "dir": "clients/dotnet",
             "project": "src/Example.Things", "tests": "tests/Example.Things.Tests"},
            {"registry": "maven", "group": "io.example", "artifact": "things", "dir": "clients/java"},
            {"registry": "crates", "crate": "example-proto", "dir": "server", "package_flags": "--allow-dirty"},
        ],
    }
    family.update(family_overrides)
    return {"schema": 1, "gates": ["python3 clients/check.py"], "artifact_check": "clients/check_license.py",
            "families": {"things": family}}


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.src = Path(self.tmp.name)
        (self.src / "clients/python").mkdir(parents=True)
        (self.src / "clients/python/pyproject.toml").write_text('[project]\nname = "x"\nversion = "1.2.0"\n')

    def tearDown(self):
        self.tmp.cleanup()

    def plan(self, rel=None, tag="things-v1.2.0", source="iokaio/example", family="things"):
        return plan.validate(SOURCES, rel or release(), source, family, tag, self.src)

    def test_a_consistent_release_plans_every_registry(self):
        p = self.plan()
        self.assertEqual(p["version"], "1.2.0")
        self.assertEqual([e["label"] for e in p["pypi"] + p["nuget"] + p["maven"] + p["crates"]],
                         ["example-things", "Example.Things", "things", "example-proto"])
        self.assertEqual(p["maven"][0]["group_path"], "io/example")

    def test_a_tag_that_is_not_this_trees_version_is_refused(self):
        with self.assertRaisesRegex(plan.PlanError, "must be things-v1.2.0"):
            self.plan(tag="things-v1.1.0")

    def test_a_family_the_allowlist_does_not_name_is_refused(self):
        rel = release()
        rel["families"]["other"] = rel["families"]["things"]
        with self.assertRaisesRegex(plan.PlanError, "not a family sources.json allows"):
            self.plan(rel, family="other", tag="things-v1.2.0")
        with self.assertRaisesRegex(plan.PlanError, "not a source this repository publishes"):
            self.plan(source="someone/else")

    def test_an_unknown_registry_or_missing_field_is_refused(self):
        with self.assertRaisesRegex(plan.PlanError, "registry 'npm'"):
            self.plan(release(packages=[{"registry": "npm", "dir": "x"}]))
        with self.assertRaisesRegex(plan.PlanError, "missing tests"):
            self.plan(release(packages=[{"registry": "nuget", "id": "A", "dir": "d", "project": "p"}]))

    def test_paths_and_flags_cannot_escape_or_inject(self):
        for bad in ("../outside", "/abs", "a/../../b", "x; rm -rf /", "$(id)"):
            with self.assertRaises(plan.PlanError, msg=bad):
                self.plan(release(packages=[{"registry": "pypi", "name": "n", "dir": bad}]))
        with self.assertRaisesRegex(plan.PlanError, "package_flags"):
            self.plan(release(packages=[{"registry": "crates", "crate": "c", "dir": "d", "package_flags": "--x; curl"}]))
        with self.assertRaises(plan.PlanError):
            self.plan(release(copy=[{"from": "server/proto", "to": "../../etc"}]))

    def test_registry_identifiers_cannot_inject_paths_or_shell(self):
        bad_packages = (
            {"registry": "nuget", "id": "$(id)", "dir": "d", "project": "p", "tests": "t"},
            {"registry": "pypi", "name": "name/../../other", "dir": "d"},
            {"registry": "maven", "group": "io.example", "artifact": "a;curl", "dir": "d"},
            {"registry": "crates", "crate": "crate name", "dir": "d"},
        )
        for package in bad_packages:
            with self.subTest(package=package), self.assertRaisesRegex(
                plan.PlanError, "plain registry identifier"
            ):
                self.plan(release(packages=[package]))

    def test_a_non_release_version_is_refused(self):
        (self.src / "clients/python/pyproject.toml").write_text('[project]\nversion = "main"\n')
        with self.assertRaisesRegex(plan.PlanError, "not a release version"):
            self.plan(tag="things-vmain")

    def test_the_repository_allowlist_parses_and_names_known_families(self):
        sources = json.loads((plan.HERE / "sources.json").read_text(encoding="utf-8"))
        for name, entry in sources.items():
            if name.startswith("$"):
                continue
            self.assertEqual(entry["branch"], "main")
            self.assertTrue(entry["families"])


if __name__ == "__main__":
    unittest.main()
