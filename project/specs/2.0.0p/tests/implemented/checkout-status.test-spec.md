# Checkout Status Test Specification

Date: 2026-07-17
Status: Implemented
Feature spec: `project/specs/2.0.0p/implemented/checkout-status.spec.md`
Feature spec canonical status: Implemented canonical leaf
Architecture ancestor: `project/architecture/project-checkouts-and-active-surface.md; project/architecture/acd-2.0-implementation-defaults.md`

## Overview

Verifies the route and helper behavior for report clean, dirty, missing, and stale checkout entries for a workspace without mutating active files.

## Application Integration Under Test

- App type: console.
- User/caller surface: `skillskeeper checkout status --workspace <path>`.
- Invocation route: explicit CLI command.
- Wiring owner/module: `skills_keeper.checkout`.
- Observable result: read-only clean, dirty, missing, and stale status output with exit code and no file mutations.
- Integration validation: route-level temporary fixture tests.

## Manual Smoke

- Exercise `skillskeeper checkout status --workspace <path>` against a temporary datastore/workspace fixture and confirm the observable result without touching production state.

## Automated Smoke Tests

- Fast route smoke asserts exit code, stdout/stderr shape, and the primary file side effect for this leaf.

## Automated Acceptance Tests

- Unit/helper behavior:
  - checkout status route tests.
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
