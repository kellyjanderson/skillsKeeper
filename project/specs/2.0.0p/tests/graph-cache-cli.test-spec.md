# Graph Cache CLI Test Specification

Date: 2026-07-17
Status: Reviewed Draft
Feature spec: `project/specs/2.0.0p/graph-cache-cli.spec.md`
Feature spec canonical status: Canonical draft leaf
Architecture ancestor: `project/architecture/skill-library-graph.md; project/architecture/acd-2.0-implementation-defaults.md`

## Overview

Verifies the route and helper behavior for expose graph cache rebuild and status commands that write and report generated cache metadata.

## Application Integration Under Test

- App type: console.
- User/caller surface: `skillskeeper library graph rebuild`; `skillskeeper library graph status`.
- Invocation route: explicit CLI command.
- Wiring owner/module: `skills_keeper.cli`.
- Observable result: stdout status, exit code, cache metadata file.
- Integration validation: CLI smoke tests with temporary datastore fixtures.

## Manual Smoke

- Exercise `skillskeeper library graph rebuild`; `skillskeeper library graph status` against a temporary datastore/workspace fixture and confirm the observable result without touching production state.

## Automated Smoke Tests

- Fast route smoke asserts exit code, stdout/stderr shape, and the primary file side effect for this leaf.

## Automated Acceptance Tests

- Unit/helper behavior:
  - fresh, stale, missing, invalid metadata cases.
- Integrated route behavior:
  - CLI rebuild/status asserts output and exit codes.
- Failure and stale-result behavior, if applicable:
  - Invalid manifest prevents cache writes; missing cache is reported clearly.

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
