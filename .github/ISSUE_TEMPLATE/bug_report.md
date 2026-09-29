---
name: Bug report
about: A dispatch, the planner, or the documentation behaved differently from what the README says
labels: bug
---

<!-- A vulnerability does not go here: SECURITY.md names the private channel.
     A defect in a published client package belongs in its source repository:
     iokaio/munarium for the Server clients, iokaio/munarium-matrix for the Matrix clients. -->

**Dispatch** (source, family, tag; rehearsal or publish; link to the run), or **planner command**:

**What you did**

**What you expected**, citing the README section that says so, if one does.

**What happened instead**: what preflight refused, which job failed and what it printed, or what
the planner reported. Credentials, tokens and hostnames removed.

**Smallest reproduction**, if the planner can show it offline (`scripts/plan.py --offline`).
