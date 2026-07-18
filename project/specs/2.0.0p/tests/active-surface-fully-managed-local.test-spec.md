# Active Surface Fully Managed Local Test Specification

Date: 2026-07-17
Status: Reviewed Draft
Feature spec: `project/specs/2.0.0p/active-surface-fully-managed-local.spec.md`
Feature spec canonical status: Canonical draft leaf
Architecture ancestor: `project/architecture/project-checkouts-and-active-surface.md; project/architecture/acd-active-surface-ownership-transition.md`

## Overview

Verifies the route and helper behavior for in opt-in fully managed mode, preserve direct `.agents/skills` additions, edits, and deletions as candidates instead of accepting them silently.

## Application Integration Under Test

- App type: library-only with mixed route consumer.
- User/caller surface: reconciler consumed by `sync` and `watch` for fully managed workspaces.
- Invocation route: module call from reconciliation routes.
- Wiring owner/module: `skills_keeper.active_surface`.
- Observable result: candidate segregation records for direct add/edit/delete, restored or absent active state, status result, and sync/watch route output.
- Integration validation: route-level temporary fixture tests.

## Manual Smoke

- Exercise reconciler consumed by `sync` and `watch` for fully managed workspaces against a temporary datastore/workspace fixture and confirm the observable result without touching production state.

## Automated Smoke Tests

- Fast route smoke asserts exit code, stdout/stderr shape, and the primary file side effect for this leaf.

## Automated Acceptance Tests

- Unit/helper behavior:
  - fully managed add/edit/delete tests.
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
