# Graph Manifest Schema Validation Test Specification

Date: 2026-07-17
Status: Reviewed Draft
Feature spec: `project/specs/2.0.0p/graph-manifest-schema-validation.spec.md`
Feature spec canonical status: Canonical draft leaf
Architecture ancestor: `project/architecture/skill-library-graph.md; project/architecture/acd-2.0-implementation-defaults.md`

## Overview

Verifies the route and helper behavior for define and validate the json skill graph manifest so downstream graph operations have trusted normalized input.

## Application Integration Under Test

- App type: library-only with console error exposure.
- User/caller surface: graph validation consumed by `skillskeeper library graph rebuild` and `status`.
- Invocation route: module call from graph command handlers.
- Wiring owner/module: `skills_keeper.graph`.
- Observable result: validation errors, normalized ids, and manifest hash.
- Integration validation: module tests plus CLI rebuild failure smoke for invalid fixtures.

## Manual Smoke

- Exercise graph validation consumed by `skillskeeper library graph rebuild` and `status` against a temporary datastore/workspace fixture and confirm the observable result without touching production state.

## Automated Smoke Tests

- Fast route smoke asserts exit code, stdout/stderr shape, and the primary file side effect for this leaf.

## Automated Acceptance Tests

- Unit/helper behavior:
  - valid, duplicate, missing target, unknown type, bad relationship, and deterministic hash cases.
- Integrated route behavior:
  - CLI rebuild failure proves validation errors reach the command route.
- Failure and stale-result behavior, if applicable:
  - Invalid manifests return all practical validation errors and prevent cache writes.

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
