# Graph Traversal API Test Specification

Date: 2026-07-17
Status: Reviewed Draft
Feature spec: `project/specs/2.0.0p/graph-traversal-api.spec.md`
Feature spec canonical status: Canonical draft leaf
Architecture ancestor: `project/architecture/skill-library-graph.md; project/architecture/acd-2.0-implementation-defaults.md`

## Overview

Verifies the route and helper behavior for provide deterministic top-down checkout resolution and bottom-up impact traversal over the validated graph.

## Application Integration Under Test

- App type: library-only.
- User/caller surface: graph traversal APIs consumed by checkout and proposal modules.
- Invocation route: module call.
- Wiring owner/module: `skills_keeper.graph`.
- Observable result: TraversalResult containing skill ids, path metadata, conflicts, and affected roots.
- Integration validation: consumer tests from checkout and proposal routes plus graph unit tests.

## Manual Smoke

- Exercise graph traversal APIs consumed by checkout and proposal modules against a temporary datastore/workspace fixture and confirm the observable result without touching production state.

## Automated Smoke Tests

- Fast route smoke asserts exit code, stdout/stderr shape, and the primary file side effect for this leaf.

## Automated Acceptance Tests

- Unit/helper behavior:
  - top-down, bottom-up, conflict, missing root, and cycle cases.
- Integrated route behavior:
  - checkout and proposal acceptance tests prove consumer integration.
- Failure and stale-result behavior, if applicable:
  - Missing root, unsupported relationship, and cycle errors are explicit and deterministic.

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
