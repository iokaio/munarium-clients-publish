## What and why

<!-- One paragraph. Link the issue if there is one. -->

## Behavior and review scope

<!-- Describe the observable change, its regression and an adjacent valid case. For a
     publish.yml change: which jobs change, which hold a credential, and whether any
     source code runs in them. Size triggers a review decision; it is not a merge gate. -->

## Validation evidence and limitations

<!-- Name commands, results and unavailable coverage. For a publish.yml change, link the
     rehearsal run (every registry unticked) dispatched from this branch against a real
     source tag, or state that none was run and why. A description of what the workflow
     should do is not evidence of what it does. Keep automatic CI enabled. -->

## Checks

- [ ] Every commit is signed off (`git commit -s`; the DCO, see CONTRIBUTING.md).
- [ ] `python3 -m unittest discover -s scripts -p 'test_*.py'` passes.
- [ ] `check_license.py`, `scripts/private_material_scan.py` and `scripts/docs_linkcheck.py` are green;
      `gitleaks dir . --config .gitleaks.toml` finds nothing.
- [ ] For a `publish.yml` change: a rehearsal run is linked above; every action is pinned by commit
      with its version in a comment; workflow `permissions` stay at `contents: read`.
- [ ] For a `sources.json` change: the pull request says which source, which family, and why.
- [ ] New source files carry `SPDX-License-Identifier: Apache-2.0` on the first line.
- [ ] The README still describes what the workflow does after this change.

## Disclosure

Answer each; "none" is an answer.

1. **Third-party code** in this pull request (any file or fragment you did not write), with its license:
2. **Generated code** (what generated it, from what):
3. **AI-tool provenance** (which tools helped write this, and that you reviewed every line):
4. **Employer or contractual restrictions** on contributing this:

I have the right to submit every file in this pull request under the Apache License 2.0.

## Maintainer self-review

<!-- For a pull request the owner merges on their own review: the compensating control
     for a sole approver. -->

- [ ] Read the whole diff once more after CI went green, as a reviewer would.
- [ ] No credential, hostname, internal path, or private document entered the tree.
- [ ] No job that holds a credential runs source code, and no credential is requested before the
      step that uploads; `cargo publish` remains the one documented exception.
- [ ] Preflight's refusals are unchanged, or the change to them is the point of the PR and says so.
