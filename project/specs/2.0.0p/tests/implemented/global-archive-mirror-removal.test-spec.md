# Global Archive Mirror Removal Test Specification

Date: 2026-07-17
Status: Implemented
Feature spec: `project/specs/2.0.0p/implemented/global-archive-mirror-removal.spec.md`
Feature spec canonical status: Implemented canonical leaf
Architecture ancestor: `project/architecture/acd-global-archive-mirror-removal.md`

## Overview

Verifies that archiving a managed global skill removes the matching generated Codex mirror while preserving unrelated mirrors and backup-only local behavior.

## Application Integration Under Test

- App type: console.
- User/caller surface: `skillskeeper archive <workspace> <source-kind> <identity>`.
- Invocation route: explicit CLI command.
- Wiring owner/module: `skills_keeper.cli`.
- Observable result: archive path, mirror path, mirror removed/missing status, exit code.
- Integration validation: CLI archive smoke with temp datastore and temp Codex skills root.

## Manual Smoke

- In a temp fixture, create a managed global active skill and generated mirror, run archive, and confirm the mirror path is gone while unrelated mirrors remain.

## Automated Smoke Tests

- Archive command removes an existing matching generated mirror and reports `removed`.

## Automated Acceptance Tests

- Unit/helper behavior:
  - path normalization, root containment, missing mirror, unrelated mirror.
- Integrated route behavior:
  - CLI archive moves datastore active copy and removes matching mirror.
- Failure and stale-result behavior, if applicable:
  - archive failure prevents mirror deletion.

## App-Type Proof

- GUI proof:
  - not applicable.
- Console proof:
  - command, args, stdout/stderr, exit code, datastore and mirror side effects.
- API/service proof:
  - not applicable.
- Mixed-surface proof:
  - not applicable.
- Library-only proof:
  - mirror helper behavior is covered through the command route.

## Fixtures And Data

- Temporary datastore active/archive tree, temporary Codex skills root, generated mirror folders, unrelated mirror folders, backup-only workspace folder.
- Production-data rule: tests must not require production datastore or real `~/.codex/skills`.

## Acceptance

- [x] Feature spec is canonical, or this test spec is explicitly temporary while split coverage is incomplete.
- [x] Route-level proof exists for the app type.
- [x] Helper-only tests cannot satisfy this feature contract.
- [x] Observable result is asserted or manually checked.
- [x] Failure behavior is covered where applicable.
