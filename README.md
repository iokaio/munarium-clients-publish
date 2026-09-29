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
tests. `scripts/plan.py --offline` plans a release against a local checkout
without asking the registries:

```console
python3 scripts/plan.py --source iokaio/munarium-matrix --family matrix-clients \
  --tag matrix-clients-v1.2.0 --src ../munarium-matrix --offline
```

Licensed under the Apache License 2.0 ([LICENSE](LICENSE)).
