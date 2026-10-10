# SPDX-License-Identifier: Apache-2.0
"""Structural guards for registry admission; hosted rehearsals validate the workflow.

These checks do not emulate GitHub's scheduler or prove registry publication.
They prevent restoring the observed implicit-success skip bug or weakening the
explicit conditions that replace it.
"""
from pathlib import Path
import re
import unittest


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/publish.yml"
REGISTRIES = ("nuget", "pypi", "maven", "crates")


def admission_terms(registry):
    return {
        "!cancelled()",
        "needs.preflight.result == 'success'",
        "needs.builds-passed.result == 'success'",
        f"inputs.publish_{registry}",
        f"fromJSON(needs.preflight.outputs.plan).{registry}_todo[0] != null",
    }


def check_admission(workflow, registry):
    block = re.search(
        rf"(?ms)^  publish-{registry}:\n(.*?)(?=^  [a-z]|\Z)", workflow
    )
    assert block, f"Missing publish-{registry} job"
    body = block.group(1)
    assert "    needs: [preflight, builds-passed]\n" in body
    assert "    environment: release\n" in body
    condition = re.search(r"(?m)^    if: \$\{\{ (.*?) \}\}$", body)
    assert condition, "Admission must be an explicit expression"
    terms = {term.strip() for term in condition.group(1).split("&&")}
    assert terms == admission_terms(registry), f"Unsafe publish-{registry} admission"


class PublishWorkflowTests(unittest.TestCase):
    def test_all_registries_preserve_admission_after_skipped_builds(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        for registry in REGISTRIES:
            with self.subTest(registry=registry):
                check_admission(workflow, registry)

    def test_removing_any_admission_guard_is_rejected(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        for registry in REGISTRIES:
            for removed in admission_terms(registry):
                remaining = sorted(admission_terms(registry) - {removed})
                original = next(
                    line for line in workflow.splitlines()
                    if line.startswith("    if:") and f".{registry}_todo[0]" in line
                )
                mutated = workflow.replace(original, "    if: ${{ " + " && ".join(remaining) + " }}")
                with self.subTest(registry=registry, removed=removed):
                    self.assertTrue(workflow != mutated, "Negative control did not alter the guard")
                    with self.assertRaises(AssertionError):
                        check_admission(mutated, registry)

    def test_bypassing_build_barrier_or_release_environment_is_rejected(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        for line in ("    needs: [preflight, builds-passed]\n", "    environment: release\n"):
            for registry in REGISTRIES:
                with self.subTest(registry=registry, removed=line):
                    with self.assertRaises(AssertionError):
                        check_admission(workflow.replace(line, ""), registry)


if __name__ == "__main__":
    unittest.main()
