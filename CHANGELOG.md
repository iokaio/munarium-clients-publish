# munarium-clients-publish release notes

This repository publishes other repositories' releases and has none of its own. The workflow is
versioned by `main`; the entries below record what changed in it and when. The versions of the
packages it publishes are recorded in their source repositories.

## Unreleased

- **Governance and contribution files.** `NOTICE`; `SECURITY.md`; `CONTRIBUTING.md`; `SUPPORT.md`;
  `CODE_OF_CONDUCT.md`; `TRADEMARK.md`; `AGENTS.md` and its identical copy `CLAUDE.md`; issue and
  pull request templates; `CODEOWNERS` and `FUNDING.yml`; the DCO and repository-hygiene workflows
  with the checks they run (`check_license.py`, `scripts/private_material_scan.py`,
  `scripts/docs_linkcheck.py`, gitleaks); a README section on where this repository sits in the
  Munarium Governance Platform. `LICENSE` normalized to the canonical Apache-2.0 text so that the
  licence gate can pin it; copyright is recorded in `NOTICE`.

## 28 September 2026

- **The central client publishing workflow** (`publish.yml`), `sources.json` and the offline release
  planner (`scripts/plan.py`, `scripts/test_plan.py`), with the planner's tests running in `ci.yml`.
  Families: `server-crates` and `server-clients` from `iokaio/munarium`; `matrix-clients` from
  `iokaio/munarium-matrix`.
- Repository created.
