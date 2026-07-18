# Proposal From Segregated Edit Test Specification

Date: 2026-07-17
Status: Reviewed Draft
Feature spec: `project/specs/2.0.0p/proposal-from-segregated-edit.spec.md`
Feature spec canonical status: Canonical draft leaf
Architecture ancestor: `project/architecture/library-update-proposals.md`; `project/architecture/project-checkouts-and-active-surface.md`; `project/architecture/acd-active-surface-ownership-transition.md`; `project/architecture/acd-2.0-implementation-defaults.md`

## Overview

Verifies that a preserved dirty checkout edit can enter the normal proposal
review lifecycle without directly mutating reusable library source.

## Application Integration Under Test

- App type: console.
- User/caller surface: `skillskeeper checkout propose-update <skill-id> --workspace <path>`.
- Invocation route: explicit CLI command.
- Wiring owner/module: `skills_keeper.cli`.
- Observable result: proposal id/path, `review_required` status, segregation proposed status, stdout, and exit code.
- Integration validation: CLI route test with temporary workspace, segregation record, proposal store, graph, and checkout fixtures.

## Manual Smoke

- Create a temporary dirty checkout fixture, run `checkout propose-update`, and confirm the proposal exists while reusable source remains unchanged.

## Automated Smoke Tests

- CLI `checkout propose-update` creates one `review_required` proposal from one segregation record.

## Automated Acceptance Tests

- Unit/helper behavior:
  - proposal source metadata, segregation proposed transition, invalid preserved skill, and duplicate proposal guard.
- Integrated route behavior:
  - command, args, stdout/stderr, exit code, proposal artifact, source-unchanged assertion, and segregation status.
- Failure and stale-result behavior, if applicable:
  - missing or invalid segregation record fails without proposal creation or segregation status mutation.

## App-Type Proof

- GUI proof:
  - not applicable.
- Console proof:
  - command, args, stdout/stderr, exit code, proposal artifact, and segregation status.
- API/service proof:
  - not applicable.
- Mixed-surface proof:
  - not applicable.
- Library-only proof:
  - not applicable.

## Fixtures And Data

- Temporary datastore, temporary workspace, generated checkout lockfile, preserved dirty checkout record, graph fixture, proposal root, and fixture skill folders.
- Production-data rule: tests must not require production data unless explicitly marked manual.

## Acceptance

- [x] Feature spec is canonical, or this test spec is explicitly temporary while split coverage is incomplete.
- [x] Route-level proof exists for the app type.
- [x] Helper-only tests cannot satisfy this feature contract.
- [x] Observable result is asserted or manually checked.
- [x] Failure behavior is covered where applicable.
