# Active Surface Sync Watch Route Test Specification

Date: 2026-07-17
Status: Reviewed Draft
Feature spec: `project/specs/2.0.0p/active-surface-sync-watch-route.spec.md`
Feature spec canonical status: Canonical draft leaf
Architecture ancestor: `project/architecture/project-checkouts-and-active-surface.md; project/architecture/acd-active-surface-ownership-transition.md`

## Overview

Verifies the route and helper behavior for wire active-surface reconciliation into explicit sync and watcher flows with idempotent repeated-event behavior.

## Application Integration Under Test

- App type: mixed console and background service.
- User/caller surface: `skillskeeper sync`; `skillskeeper watch`.
- Invocation route: explicit sync command and background watcher trigger.
- Wiring owner/module: `skills_keeper.cli`.
- Observable result: sync stdout, watcher-style reconciliation result, service log/status entries, segregation records, restored active files, and no duplicate segregation on repeated events.
- Integration validation: route-level temporary fixture tests.

## Manual Smoke

- Exercise `skillskeeper sync`; `skillskeeper watch` against a temporary datastore/workspace fixture and confirm the observable result without touching production state.

## Automated Smoke Tests

- Fast route smoke asserts exit code, stdout/stderr shape, and the primary file side effect for this leaf.

## Automated Acceptance Tests

- Unit/helper behavior:
  - sync/watch route integration tests.
- Integrated route behavior:
  - CLI or consumer route smoke asserts observable result and side effects.
- Failure and stale-result behavior, if applicable:
  - Fail before destructive writes where possible; preserve recovery evidence when writes partially fail.

## App-Type Proof

- GUI proof:
  - not applicable.
- Console proof:
  - command, args, stdout/stderr, exit code, and file side effects where the leaf has a CLI route.
- API/service proof:
  - not applicable.
- Mixed-surface proof:
  - separate proof for console and watcher-style route when named.
- Library-only proof:
  - consuming module/downstream caller proof is required when no direct command exists.

## Fixtures And Data

- Temporary datastore, temporary workspace, fixture skills, fixture graph/lockfile/proposal records as required by the feature spec.
- Production-data rule: tests must not require production data unless explicitly marked manual.

## Acceptance

- [x] Feature spec is canonical, or this test spec is explicitly temporary while split coverage is incomplete.
- [x] Route-level proof exists for the app type.
- [x] Helper-only tests cannot satisfy this feature contract.
- [x] Observable result is asserted or manually checked.
- [x] Failure behavior is covered where applicable.
