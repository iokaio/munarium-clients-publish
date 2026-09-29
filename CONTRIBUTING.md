# Contributing to munarium-clients-publish

Contributions are welcome from anyone. What follows is the whole process; there is no contributor
license agreement to sign. This repository is release tooling, so the bar for a change to the
workflow is a rehearsal that proves it, not a description of it.

## Rights and license

- **Every commit carries a Developer Certificate of Origin sign-off**: `git commit -s`, which adds
  `Signed-off-by: Your Name <you@example.com>`. By signing off you certify the
  [DCO](https://developercertificate.org/), that the work is yours to submit under this
  repository's license, or that you have the right to submit it. A pull request with an unsigned
  commit fails its check.
- **Accepted code is Apache-2.0**, the license of the whole repository ([LICENSE](LICENSE)), by
  section 5 of the license itself: a contribution intentionally submitted for inclusion is licensed
  under the same terms, copyright and patent alike. That is why no CLA exists; a CLA would add the
  right to relicense your contribution later, and that right is not wanted.
- A contribution changes nothing about Ioka's trademarks ([TRADEMARK.md](TRADEMARK.md)), the
  support boundary ([SUPPORT.md](SUPPORT.md)), or who holds the publishing credentials.

## Disclosure

The pull request template asks four questions; answer each, and "none" is an answer:

1. **third-party code**: any file or fragment you did not write, with its license;
2. **generated code**: what generated it, from what;
3. **AI-tool provenance**: which tools helped, and that you reviewed every line;
4. **employer or contractual restrictions** on what you may contribute.

You must have the right to submit every file in the pull request. Every contribution has a human
submitter who accepts responsibility for it.

## Process

1. Fork the repository (maintainers: a topic branch) and make the change.
2. Run the gates below. Every new source file carries `SPDX-License-Identifier: Apache-2.0` on its
   first line, the second after a shebang, and `check_license.py` names any file that does not.
3. Open a pull request against `main`. CI runs the planner's tests and the repository-wide gates
   with no credential. **Nothing in a pull request can reach a registry**: publish jobs run only
   from this repository's `main` in the reviewer-gated `release` environment, and a rehearsal
   dispatched from a branch holds no secret.
4. For a change to `publish.yml`, dispatch a rehearsal (every registry unticked) from your branch
   against a real source tag, and link the run in the pull request. A workflow change without a
   rehearsal is a description, not evidence.
5. A code owner reviews ([.github/CODEOWNERS](.github/CODEOWNERS)); Ioka squash-merges. External
   pull requests never gain publishing authority.

## Gates

| Gate | Command |
|---|---|
| Planner tests | `python3 -m unittest discover -s scripts -p 'test_*.py'` |
| Offline plan | `python3 scripts/plan.py --source <owner/repo> --family <family> --tag <tag> --src <local checkout> --offline` |
| `sources.json` parses | `python3 -c "import json; json.load(open('sources.json', encoding='utf-8'))"` |
| Licence and notices | `py check_license.py` |
| Private material | `py scripts/private_material_scan.py` |
| Documentation links | `py scripts/docs_linkcheck.py` |
| Secret scan | `gitleaks dir . --config .gitleaks.toml` |
| Whitespace | `git diff --check` |

Use `python` or `python3` where `py` is unavailable. The CI workflows under `.github/workflows/`
are the source of truth for what runs.

Rules the gates and reviewers enforce that are easy to trip:

- **`sources.json` is a release setting.** It decides what can reach a public registry, and a change
  to it is reviewed like one: the pull request says which source, which family, and why.
- **Source code runs only in credential-free jobs.** Preflight's gates and the build jobs hold no
  secret; the NuGet, PyPI and Maven publish jobs run nothing from the source; `cargo publish` is the
  one documented exception and its verification happens before the credential exists. A change
  that moves source execution into a credentialed job, or a credential into a job that executes
  source, is declined.
- **Every action is pinned by commit**, with the version in a trailing comment. A tag is not a pin.
- **Workflow permissions stay at `contents: read`.** A job that needs more says so on the job, not
  the workflow, and says why.
- **Nothing here writes to a source repository.** Tags are created in the source by a maintainer
  before the dispatch.
- **A rehearsal is not a release**, and TestPyPI never counts as one.

## Conduct and venues

[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) applies everywhere in this project. Questions go to GitHub
Discussions, defects to Issues, and suspected vulnerabilities to the private channel
[SECURITY.md](SECURITY.md) names, never to a public issue or a proof-of-concept pull request.

## Protected files

Only Ioka changes `LICENSE`, `NOTICE`, `TRADEMARK.md`, this file, `CODE_OF_CONDUCT.md`,
`SECURITY.md`, `SUPPORT.md`, `AGENTS.md` and `CLAUDE.md`, anything under `.github/`,
`sources.json`, the `release` environment and its secrets and variables, and the trusted-publisher
registrations on the registries. A pull request that touches them is declined unless a maintainer
opened it.
