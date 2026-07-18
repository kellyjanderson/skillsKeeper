# Checkout Segregated Discard Test Specification

Date: 2026-07-17
Status: Reviewed Draft
Feature spec: `project/specs/2.0.0p/checkout-segregated-discard.spec.md`
Feature spec canonical status: Canonical draft leaf
Architecture ancestor: `project/architecture/project-checkouts-and-active-surface.md`; `project/architecture/acd-active-surface-ownership-transition.md`; `project/architecture/acd-2.0-implementation-defaults.md`

## Overview

Verifies the user-facing recovery command for discarding a segregated dirty
generated checkout edit.

## Application Integration Under Test

- App type: console.
- User/caller surface: `skillskeeper checkout discard <skill-id> --workspace <path>`.
- Invocation route: explicit CLI command.
- Wiring owner/module: `skills_keeper.cli`.
- Observable result: segregation discarded status, stdout, exit code, unchanged library source, and unchanged restored active checkout.
- Integration validation: CLI route test with temporary workspace and segregation fixture.

## Manual Smoke

- Create a temporary dirty checkout fixture, run `checkout discard`, and confirm the preserved edit is marked discarded while library source remains unchanged.

## Automated Smoke Tests

- CLI `checkout discard` resolves one segregation record and reports discarded status.

## Automated Acceptance Tests

- Unit/helper behavior:
  - segregation lookup, discard transition, already-resolved handling, and unchanged-source assertions.
- Integrated route behavior:
  - command, args, stdout/stderr, exit code, segregation status, and unchanged library/active files.
- Failure and stale-result behavior, if applicable:
  - missing segregation record fails without mutating active skills, library source, or checkout lockfile.

## App-Type Proof

- GUI proof:
  - not applicable.
- Console proof:
  - command, args, stdout/stderr, exit code, segregation status, and unchanged source assertions.
- API/service proof:
  - not applicable.
- Mixed-surface proof:
  - not applicable.
- Library-only proof:
  - not applicable.

## Fixtures And Data

- Temporary datastore, temporary workspace, generated checkout lockfile, preserved dirty checkout record, and fixture skill folders.
- Production-data rule: tests must not require production data unless explicitly marked manual.

## Acceptance

- [x] Feature spec is canonical, or this test spec is explicitly temporary while split coverage is incomplete.
- [x] Route-level proof exists for the app type.
- [x] Helper-only tests cannot satisfy this feature contract.
- [x] Observable result is asserted or manually checked.
- [x] Failure behavior is covered where applicable.
