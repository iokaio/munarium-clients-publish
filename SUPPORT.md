# Support

This repository is open source under the Apache License 2.0 ([LICENSE](LICENSE)). **The license
includes no support from Ioka LLC**, and nothing in this repository is a support commitment.

## What this repository is

Release tooling: the workflow, allowlist and planner through which Ioka publishes the Munarium
client packages. It is not a component of the platform and it publishes nothing of its own. The
packages it publishes are supported, or not, by their source repositories:
[iokaio/munarium](https://github.com/iokaio/munarium) for the Server client libraries and
[iokaio/munarium-matrix](https://github.com/iokaio/munarium-matrix) for the Matrix client libraries.

## What is available to everyone

- **Questions** about the publishing workflow go to GitHub Discussions on this repository.
- **Defects** in the workflow or the planner go to GitHub Issues, with the source, family and tag
  you dispatched, a link to the run, and what preflight or the failing job said. A defect in a
  published package goes to its source repository.
- **Vulnerabilities** go to the private channel in [SECURITY.md](SECURITY.md), never an issue.
- **What is published where** is in the README's table, and each source repository records the
  versions its registries serve.

Issues are read and triaged by one maintainer. There is no response-time commitment on this
repository, and a defect may be closed as "recorded, not scheduled", which is a truthful answer
rather than a dismissal.

## What is not

A production support relationship, a guarantee that a given version is on a given registry by a
given date, or access to Ioka's publishing credentials and trusted-publisher registrations, which
stay with Ioka. Munarium Enterprise is a separate, proprietary distribution built on Munarium Server
and Munarium Matrix; it is not published from here. Commercial enquiries go to **info@ioka.io**.

## Running it yourself

Everything the workflow needs is in the README's Setup table, and the planner runs offline against
a local checkout. A fork can publish its own packages under its own names with its own credentials.
It cannot publish under Ioka's package names: those are trusted-publisher registrations tied to this
repository, and the names themselves are covered by [TRADEMARK.md](TRADEMARK.md).
