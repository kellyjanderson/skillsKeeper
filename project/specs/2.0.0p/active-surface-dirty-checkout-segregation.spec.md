# Active Surface Dirty Checkout Segregation Specification

Date: 2026-07-17
Status: Reviewed Draft
Primary ancestor: `project/architecture/project-checkouts-and-active-surface.md`
Architecture ancestor: `project/architecture/project-checkouts-and-active-surface.md; project/architecture/acd-active-surface-ownership-transition.md; project/architecture/acd-2.0-implementation-defaults.md`
Source artifact: `project/architecture/project-checkouts-and-active-surface.md`
Split provenance: `project/specs/2.0.0p/active-surface-reconciliation.spec.md`
Canonical status: `Canonical draft leaf`
Prerequisites:

- `project/specs/2.0.0p/active-surface-ownership-policy.spec.md` - segregation only applies after ownership classification
- `project/specs/2.0.0p/checkout-skill-materialization.spec.md` - requires generated checkout fixtures

## Work Units

Unit: Implementation Work Unit (IWU).
Definition: one independently deliverable, reviewable change set with its own verification surface. An IWU is intentionally abstract so the same unit can size software, documentation, tooling, service, research, design, and process projects.
Standard measures: count 1 IWU when the work has one primary outcome, one coherent responsibility boundary, one reviewable artifact or change set, one explicit verification method, declared inputs and outputs, and explicitly named unresolved assumptions or decisions. Split the work when any measure becomes plural, ambiguous, or unnamed.
Count: 1 IWU.
Basis: one dirty-checkout recovery behavior preserving edits and restoring clean generated copy.

## Review Score

- Prior recorded score: none for this split child.
- Adversarial rescore basis: recounted from this leaf after splitting parent responsibilities; checked for hidden coupling, unrecorded routes, missing readiness fields, destructive writes, privacy-sensitive paths, and prerequisite order.
- Functions/methods: 4 x 2 = 8
- Data structures/models: 2 x 1 = 2
- Dependencies/services: 2 x 1 = 2
- Returns/outputs/signals: 1 x 1 = 1
- Existing reusable code reused as-is: 0 x 0.5 = 0
- Adding code to an existing library/module: 1 x 1 = 1
- Creating a new reusable library/module: 0 x 3 = 0
- Async/concurrency behavior: 0 x 3 = 0
- Destructive/write behavior: 1 x 3 = 3
- Security/privacy-sensitive behavior: 1 x 3 = 3
- Performance-sensitive behavior: 1 x 2 = 2
- Total: 22
- Split decision: score 16-24 retained because preserve-and-restore is one active-surface repair route.

## Source Field Carryover

- Source purpose:
  - Preserve direct edits to generated library checkouts outside `.agents/skills` and restore the clean library source copy.
- Source responsibilities by category:
  - Functions/methods, data structures, dependencies, outputs, write behavior, privacy, and performance are narrowed in the detailed sections below.
- Source open questions / nuance discovered:
  - No additional architecture gap remains after linked ACD defaults and parent architecture are applied.
- Source split/provenance notes:
  - Split from `project/specs/2.0.0p/active-surface-reconciliation.spec.md` during review pass 1.

## Purpose

Preserve direct edits to generated library checkouts outside `.agents/skills` and restore the clean library source copy.

## Scope

Owns:

- dirty generated checkout detection
- segregation storage for dirty checkout edits
- clean source restoration after preservation

Does not own:

- fully managed local add/edit/delete
- proposal creation from segregated edits
- watch loop debounce strategy

## Split Coverage

- Parent spec: `project/specs/2.0.0p/active-surface-reconciliation.spec.md`
- Parent coverage status: covered by reviewed child specs.
- Parent responsibilities owned by this child:
  - dirty library checkout detection, segregation metadata, and restoration.
- Parent responsibilities still missing from children:
  - none

## Refinement History

| Request ledger | Latest pass | Active specs reviewed | New leaves created this round | Fixed-point status |
|---|---:|---|---|---|
| `project/spec-refinement-history/2.0.0p-20260717-190429.md` | 2 | `project/specs/2.0.0p/active-surface-dirty-checkout-segregation.spec.md` | `none` | reached |

## Implementation Routing

- Primary modules/files:
  - `skills_keeper/active_surface.py` - dirty checkout reconciliation
- Supporting modules/files:
  - `skills_keeper/cli.py` - thin command wiring and existing error handling.
- GUI/QML files, if applicable:
  - `not applicable`
- Reusable library/module files:
  - `skills_keeper/active_surface.py` - dirty checkout reconciliation
- Tests:
  - `tests/test_active_surface.py` - dirty checkout segregation tests

## Chosen Defaults / Parameters

- segregation root is `.agents/skillskeeper-segregated`
- preserve dirty content before restore
- do not merge edits automatically

## Data Ownership

- Source of truth: lockfile hash and library source.
- Read ownership: active-surface reconciler.
- Write ownership: active-surface reconciler writes segregation and restored active copy.
- Derived/cache data: restored copy derives from library source.
- Privacy/logging constraints: report ids, status, and paths only; do not print full skill bodies.

## Dependencies And Routes

- Domain/service dependencies:
  - `skills_keeper/active_surface.py` and related SkillsKeeper helpers.
- Database dependencies:
  - none unless explicitly named as datastore files.
- GUI route, if applicable:
  - not applicable
- Background/concurrency route, if applicable:
  - watcher/sync integration is specified in `project/specs/2.0.0p/active-surface-sync-watch-route.spec.md`.

## Prerequisite Handling

- Architecture feedback artifacts:
  - `none` - no additional architecture feedback created by review.
- Architecture feedback status:
  - resolved or tracked in linked ACDs.
- Already implemented prerequisites:
  - existing `KeeperError`, path resolution, validation, and clean-copy helpers where named.
- Missing prerequisite architecture:
  - none
- Missing prerequisite specifications:
  - none
- Unimplemented prerequisite specifications:
  - `project/specs/2.0.0p/active-surface-ownership-policy.spec.md` - segregation only applies after ownership classification
  - `project/specs/2.0.0p/checkout-skill-materialization.spec.md` - requires generated checkout fixtures
- Progression handling:
  - implement after policy and checkout materialization.

## Application Integration

- App type: library-only with mixed route consumer.
- User/caller surface: reconciler consumed by `sync` and `watch`.
- Invocation route: module call from reconciliation routes.
- Wiring owner/module: `skills_keeper.active_surface`.
- Observable result: segregation record, preserved dirty copy path, restored clean active checkout, status result, and route output from sync/watch consumers.
- Integration validation: route-level temporary fixture tests.
- Incomplete status risk: helper-only implementation without this route proof is incomplete.

App-type-specific proof:

- GUI: not applicable.
- Console: command, args, stdout/stderr, exit code, and file side effects where the leaf has a CLI route.
- API-service: not applicable.
- Mixed: separate proof for console and watcher-style route when named.
- Library-only: consuming module proof is required when there is no direct CLI route.

## Reuse And Extraction Plan

- Existing code to reuse:
  - existing path, validation, copy, archive, or state helpers named by the implementation routing.
- Current reuse readiness:
  - available or extracted during this leaf without broad refactor.
- Extraction/wrapping needed:
  - only extract shared helpers when needed to avoid duplicated behavior.
- Additions to existing library/modules:
  - feature API in `skills_keeper/active_surface.py` plus thin CLI wiring when applicable.
- New reusable modules to expose:
  - `skills_keeper/active_surface.py` if it does not already exist.
- One-off code justification, if any:
  - none

## Required DTOs / Functions / Components

- DTOs/models:
  - `DirtyStatus` - clean, dirty, missing
  - `SegregationRecord` - original path, preserved path, reason, hashes, timestamp
- Functions/methods:
  - `detect_dirty_checkout(entry) -> DirtyStatus`
  - `segregate_active_skill(workspace, path, reason) -> SegregationRecord`
  - `restore_checkout(entry) -> RestoreResult`
- UI fields / visible data, if applicable:
  - not applicable
- UI elements / controls, if applicable:
  - not applicable
- UI components, if applicable:
  - not applicable

## Performance Contract

- Bound work to explicit datastore, workspace, lockfile, proposal, or mirror paths named by the route.

## Error And State Behavior

- Fail before destructive writes where possible; preserve recovery evidence when writes partially fail.

## Test Strategy

- Unit tests:
  - dirty checkout segregation tests.
- Service/DB tests:
  - temporary datastore/workspace fixtures only.
- GUI/controller tests, if applicable:
  - not applicable
- Integrated route tests:
  - CLI or consumer route smoke asserts observable result and side effects.
- Production-data rule:
  - Tests must not require the user's production database, live service, or real Codex skills root.

## Acceptance Criteria

- Dirty checkout edit is preserved.
- Clean source copy is restored.
- Segregation metadata names original and preserved paths.
- No automatic merge or overlay is attempted.

## Readiness Checklist

- [x] Primary ancestor and architecture ancestor are explicit.
- [x] Work Units count and basis are explicit.
- [x] Review Score is adversarially recounted from the current spec text; prior scores are challenged instead of trusted.
- [x] Source fields are carried into spec sections or preserved as explicit provenance/history.
- [x] Canonical status is explicit.
- [x] Prerequisites are linked, implemented, or marked not applicable.
- [x] Missing or stale prerequisite architecture discovered after the architecting phase has an ACD link, or is marked not applicable.
- [x] Missing prerequisite behavior has a final spec link, or is marked not applicable.
- [x] Split coverage is complete, or marked not applicable.
- [x] Per-request review ledger records the latest new-leaf list for the review round, or is marked not applicable before review.
- [x] Implementation owner/module is named.
- [x] Existing code reuse/extraction decision is explicit.
- [x] Existing library/module additions or new reusable module boundaries are named, or marked not applicable.
- [x] UI fields/elements are listed, or marked not applicable.
- [x] Chosen defaults are explicit.
- [x] Data source of truth and write owner are explicit.
- [x] GUI/concurrency route is explicit, or marked not applicable.
- [x] App type and application integration route are explicit.
- [x] Integrated route validation is named.
- [x] GUI/console/API-service/mixed/library-only proof matches the app type.
- [x] Performance bounds are explicit, or marked not applicable.
- [x] Privacy/logging constraints are explicit, or marked not applicable.
- [x] Test strategy does not depend on production data.
- [x] Acceptance criteria are testable.
