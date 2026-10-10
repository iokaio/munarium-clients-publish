# munarium-clients-publish

The one place Munarium client packages are built for release and published
from. The clients, their tests and their CI live with the service they speak
to; this repository holds only the publishing workflow and the credentials, so
moving a client between repositories never moves a trusted publisher or a
secret.

| Source | Family | Packages | Tag |
|---|---|---|---|
| [iokaio/munarium](https://github.com/iokaio/munarium) | `server-crates` | `munarium-proto`, `munarium-api-types` (crates.io) | `server-crates-v<version>` |
| [iokaio/munarium](https://github.com/iokaio/munarium) | `server-clients` | `Ioka.Munarium.Client` (NuGet), `munarium-client` (PyPI, crates.io), `io.ioka.munarium:munarium-client` (Maven Central) | `clients-v<version>` |
| [iokaio/munarium-matrix](https://github.com/iokaio/munarium-matrix) | `matrix-clients` | `Ioka.Munarium.Matrix.Client` (NuGet), `munarium-matrix` (PyPI), `io.ioka.munarium:munarium-matrix-client` (Maven Central) | `matrix-clients-v<version>` |

[`sources.json`](sources.json) is the allowlist: which source repositories may
be published from and which families each may publish. Each source describes
its families in `clients/release.json` (below); the table above is what those
files say today.

## Releasing

1. Bump the family's versions in the source repository, merge through a pull
   request, and let its CI finish green.
2. Tag the merged commit in the source repository with the family's tag, for
   example `git tag matrix-clients-v1.2.0 <commit> && git push origin matrix-clients-v1.2.0`.
3. Dispatch [publish.yml](.github/workflows/publish.yml) from `main` here,
   naming the source, family and tag. Leave every registry unticked first: that
   is a rehearsal that builds, tests and scans everything and reports what the
   registries already hold.
4. Dispatch again with the registries ticked. Each publish job waits for a
   reviewer on the `release` environment. No registry job starts until every
   package type in the family has built and tested. Already-published versions
   are skipped, so a registry-side partial failure is fixed by dispatching
   again.

For the Server's Rust client, publish `server-crates` before `server-clients`:
`munarium-client` resolves its wire crates from crates.io.

Package types outside the selected family are intentionally skipped. Publish
jobs use an explicit cancellation check so those skipped builds do not suppress
uploads after the build barrier passes. Preflight and the full build barrier
must both succeed; cancelled runs, unticked registries and already-published
versions cannot upload. A successful rehearsal proves the builds, not registry
publication: verify the publish jobs and the resulting registry versions too.

### What preflight refuses

- a source or family [`sources.json`](sources.json) does not list;
- a tag whose commit is not on the source's `main`, did not arrive through a
  merged pull request, or has an unfinished or failing check on that pull
  request's final head or on the commit itself;
- a tag that is not exactly the family's tag pattern at the version the tagged
  tree declares;
- a `release.json` whose paths are not plain repository-relative paths, whose
  package identifiers contain path or shell syntax, or whose packages name an
  unknown registry or lack a field their build needs.

It then runs the source's own gates (the `gates` list) before any build job
starts. Source code runs only in jobs that hold no credential. The NuGet, PyPI
and Maven publish jobs push what the build jobs uploaded; `cargo publish` is
the one publish step that packages from source, because crates.io accepts no
prebuilt package. Its tests and package-file inspection run before the
credential exists; the upload uses `cargo publish --no-verify` so source build
scripts do not run with that credential in the environment, and invokes Cargo
from this repository so source-owned `.cargo/config` files are not discovered.

## `clients/release.json`

```json
{
  "schema": 1,
  "gates": ["python3 clients/check_compatibility.py", "python3 check_license.py"],
  "artifact_check": "clients/check_license.py",
  "families": {
    "matrix-clients": {
      "tag": "matrix-clients-v{version}",
      "version": {"file": "clients/python/pyproject.toml", "toml": "project.version"},
      "copy": [],
      "packages": [
        {"registry": "nuget", "id": "Ioka.Munarium.Matrix.Client", "dir": "clients/dotnet",
         "project": "src/Ioka.Munarium.Matrix.Client", "tests": "tests/Ioka.Munarium.Matrix.Client.Tests"},
        {"registry": "pypi", "name": "munarium-matrix", "dir": "clients/python"},
        {"registry": "maven", "group": "io.ioka.munarium", "artifact": "munarium-matrix-client", "dir": "clients/java"}
      ]
    }
  }
}
```

- `gates`: commands run from the source root, without credentials, before
  anything is built. A source keeps its versions consistent here (for example
  a compatibility check that fails when two manifests disagree).
- `artifact_check`: a script taking `--artifact <files>` (wheels, sdists,
  nupkgs, jars) and, for a family with crates, `--rust-list <cargo package
  --list output>`.
- `version`: the file and dotted TOML key holding the family's version. The
  tag must equal `tag` with `{version}` replaced.
- `copy`: files a crate packages that the tree does not track, copied within
  the checkout before a crate is packaged or published.
- `packages`: each has a `registry` (`nuget`, `pypi`, `maven` or `crates`) and
  a `dir`, and is built there with `dotnet build/test/pack`,
  `pip install -e .[dev]` + `pytest` + `python -m build`,
  `./gradlew build publishToMavenLocal`, or `cargo package --list` +
  `cargo test`. A crate may add `package_flags`. Crates publish in the order
  listed.

## Setup

These live here and nowhere else; the source repositories hold no publishing
credential.

| What | Where | Value |
|---|---|---|
| `release` environment | this repository | deployment branches: `main` only; required reviewer |
| `NUGET_USER` | repository variable | the NuGet.org profile that owns the trusted-publishing policy |
| NuGet trusted-publishing policy | nuget.org | owner `iokaio`, repository `munarium-clients-publish`, workflow `publish.yml`, environment `release` |
| PyPI trusted publisher | pypi.org and test.pypi.org, each project | same repository, workflow and environment |
| crates.io trusted publisher | each crate's settings | same repository, workflow and environment |
| `CENTRAL_USERNAME`, `CENTRAL_PASSWORD` | `release` environment secrets | a Sonatype Central Portal user token |
| `GPG_PRIVATE_KEY`, `GPG_PASSPHRASE` | `release` environment secrets | the release signing key, ASCII-armored |

Package metadata still names each source repository; trusted-publishing
provenance and PyPI attestations name this one.

## Development

`python3 -m unittest discover -s scripts -p 'test_*.py'` runs the planner's
tests; the repository-wide gates (licence, private material, documentation
links, secrets) are in [CONTRIBUTING.md](CONTRIBUTING.md).
`scripts/plan.py --offline` plans a release against a local checkout
without asking the registries:

```console
python3 scripts/plan.py --source iokaio/munarium-matrix --family matrix-clients \
  --tag matrix-clients-v1.2.0 --src ../munarium-matrix --offline
```

## Where this repository sits

Munarium is growing from a governed-memory foundation into the Munarium Governance Platform: nine
open-source components (Registry, Harness, Warden, Gate, Gateway, Council, Sentinel, Assure and
Console) around Munarium Server and Munarium Matrix, coordinated from the public hub
[iokaio/munarium-platform](https://github.com/iokaio/munarium-platform). This repository is not one
of the nine. It is release tooling for the foundation's client libraries, and it holds one
platform invariant for them: **untrusted pull-request code cannot acquire release secrets or
replace the controls that approve a release.** Preflight and build jobs hold no publishing
credential; the NuGet, PyPI and Maven publish jobs run nothing from the source. `cargo publish`
is the documented exception: packaging uses the verified source, with build-script verification
completed before the credential is present. Publishing credentials live in a reviewer-gated
environment that accepts this repository's `main` and nothing else.

The platform plan expects Munarium Harness to publish client bindings that identify the contract
digest they were generated from. Whether those packages publish through this repository is decided
when they exist, as a change to `sources.json` reviewed like any other release setting.

| Repository | Plane | Role |
|---|---|---|
| [iokaio/munarium-platform](https://github.com/iokaio/munarium-platform) | hub | Architecture, normative contracts, decision records, roadmap and composition evidence for the whole platform |
| [iokaio/munarium](https://github.com/iokaio/munarium) | foundation (mediation) | Munarium Server: governed memory, the append-only ledger, and the Server client libraries |
| [iokaio/munarium-matrix](https://github.com/iokaio/munarium-matrix) | foundation (mediation) | Munarium Matrix: governed, read-only structured evidence from enterprise data sources |
| [iokaio/munarium-registry](https://github.com/iokaio/munarium-registry) | authority | Inventory of agents, tools, manifests, and policy bundles |
| [iokaio/munarium-harness](https://github.com/iokaio/munarium-harness) | agent | SDKs that make the governed path easy for honest agents |
| [iokaio/munarium-warden](https://github.com/iokaio/munarium-warden) | authority | Workload identity, delegation, just-in-time credentials, kill switches |
| [iokaio/munarium-gate](https://github.com/iokaio/munarium-gate) | mediation | Policy decision and enforcement point for every tool call |
| [iokaio/munarium-gateway](https://github.com/iokaio/munarium-gateway) | mediation | Model-call mediation: routing, BYOK, budgets, screening |
| [iokaio/munarium-council](https://github.com/iokaio/munarium-council) | authority | Approvals, policy lifecycle, ratified governance transitions |
| [iokaio/munarium-sentinel](https://github.com/iokaio/munarium-sentinel) | assurance | Telemetry, anomaly detection, circuit breakers, incident replay |
| [iokaio/munarium-assure](https://github.com/iokaio/munarium-assure) | assurance | Control-framework mapping and evidence packs |
| [iokaio/munarium-console](https://github.com/iokaio/munarium-console) | assurance | One interface for approvers, operators, and auditors |
| [iokaio/munarium-clients-publish](https://github.com/iokaio/munarium-clients-publish) | tooling | The one place Munarium client packages are built for release and published from |
| [iokaio/munarium-demo](https://github.com/iokaio/munarium-demo) | examples | Munarium Demo: working applications and bundled datasets for evaluating the foundation |

The development tool VCP ([iokaio/vcp](https://github.com/iokaio/vcp)) is separate: not one of the
nine components and not a runtime dependency for adopters. Ioka's private repositories hold
planning material awaiting publication review and the proprietary Matrix analytics adapters;
nothing from them is copied into a public repository without that review.

## Licensing

Apache-2.0 ([LICENSE](LICENSE), [NOTICE](NOTICE)). The names are not part of that grant:
[TRADEMARK.md](TRADEMARK.md) says what you may do without asking, which is most things. A fork can
publish its own packages under its own names; it cannot publish under Ioka's, which are
trusted-publisher registrations tied to this repository.

## Contributing, support, security

Signed-off pull requests, no CLA ([CONTRIBUTING.md](CONTRIBUTING.md)); a change to `publish.yml`
comes with a linked rehearsal run. Questions go to Discussions, defects in the workflow or planner
to Issues, defects in a published package to its source repository, and suspected vulnerabilities to
the private channel [SECURITY.md](SECURITY.md) names, never a public issue. What is and is not
supported: [SUPPORT.md](SUPPORT.md). Conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). History of
the workflow: [CHANGELOG.md](CHANGELOG.md).
