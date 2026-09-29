# Security

Do not file a vulnerability as an issue or a pull request.

Report a suspected vulnerability in anything in this repository privately, by either route:

- GitHub's private vulnerability reporting ("Report a vulnerability" under the Security tab), or
- email to **info@ioka.io** with "security" in the subject.

Say what you found, where, and how to reproduce it. Do not include live credentials, customer data,
or a proof of concept run against a system you do not operate. You will get an acknowledgement
within two business days, and a fix, or a recorded decision, on the affected path before any related
release. Credit is given if you ask for it.

## Supported versions

This repository publishes other repositories' releases and has none of its own. The publishing
workflow is versioned by `main`, and a fix lands there. A vulnerability in a published client
package is a vulnerability in its source repository ([iokaio/munarium](https://github.com/iokaio/munarium)
or [iokaio/munarium-matrix](https://github.com/iokaio/munarium-matrix)); report it there, or here
through the same private channel and it is routed.

## What matters most here

This repository exists so that no client package can reach a public registry except from a
reviewed, merged, checked commit of an allowlisted source, with source verification separated from
publishing credentials and the Cargo packaging exception documented below. The findings that will
be taken most seriously and most quickly:

- **A path by which source code runs with a credential.** Preflight and the build jobs run the
  source's own gates and builds without any secret; the NuGet, PyPI and Maven publish jobs run
  nothing from the source. `cargo publish` is the one documented exception, and its tests and
  package-file inspection happen before the credential exists. Any job, step, script or action that
  breaks that separation is the finding this repository exists to prevent.
- **A pull request, a fork, or a non-`main` ref acquiring a publishing credential.** Publish jobs
  run only from this repository's `main` in the reviewer-gated `release` environment; a rehearsal
  from another ref must hold nothing.
- **Preflight accepting what it should refuse**: a source or family not in `sources.json`; a tag
  whose commit is not on the source's `main`, did not arrive through a merged pull request, or has
  a failing or unfinished check; a tag that is not the family's pattern at the version the tree
  declares; a `release.json` whose paths or package identifiers carry path or shell syntax.
- **A credential that outlives its job**, or a token requested earlier than the step that uploads.
- **A trusted-publisher identity that does not name this repository, `publish.yml` and the
  `release` environment exactly**, or one still registered against a repository a client has
  moved out of.
- **An action pinned by tag rather than by commit**, or a pinned commit that no longer matches the
  action it claims to be.

## What is deliberate, and is not a defect

- **Rehearsal is the default.** A dispatch with every registry unticked builds, tests, scans and
  reports, and publishes nothing. That a rehearsal can be dispatched from any ref is the design;
  that it holds no credential is the invariant.
- **`cargo publish --no-verify`.** crates.io accepts no prebuilt package, so the crate is packaged
  from source in the publish job. `--no-verify` exists so that source build scripts do not run
  while the credential is in the environment; the verification `cargo` would have done ran in the
  credential-free steps before. Cargo is invoked from this repository so that source-owned
  `.cargo/config` files are not discovered.
- **Already-published versions are skipped, not failed**, so a registry-side partial failure is
  repaired by dispatching again.
- **Maven Central is checked against the public repository**, so a bundle validated but not yet
  published in the Portal is not seen as published. The README says how to handle that.

## Secrets

Nothing in this tree is a credential. If you believe a token, key or passphrase has been exposed
through a workflow log, an artifact or a dispatch, treat it as compromised: rotate it first, then
report it.
