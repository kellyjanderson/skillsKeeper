# Active Surface Sync Watch Route Specification

Date: 2026-07-17
Status: Reviewed Draft
Primary ancestor: `project/architecture/project-checkouts-and-active-surface.md`
Architecture ancestor: `project/architecture/project-checkouts-and-active-surface.md; project/architecture/acd-active-surface-ownership-transition.md`
Source artifact: `project/architecture/project-checkouts-and-active-surface.md`
Split provenance: `project/specs/2.0.0p/active-surface-reconciliation.spec.md`
Canonical status: `Canonical draft leaf`
Prerequisites:

- `project/specs/2.0.0p/active-surface-dirty-checkout-segregation.spec.md` - route calls dirty checkout reconciliation
- `project/specs/2.0.0p/active-surface-fully-managed-local.spec.md` - route calls fully managed reconciliation

## Work Units

Unit: Implementation Work Unit (IWU).
Definition: one independently deliverable, reviewable change set with its own verification surface. An IWU is intentionally abstract so the same unit can size software, documentation, tooling, service, research, design, and process projects.
Standard measures: count 1 IWU when the work has one primary outcome, one coherent responsibility boundary, one reviewable artifact or change set, one explicit verification method, declared inputs and outputs, and explicitly named unresolved assumptions or decisions. Split the work when any measure becomes plural, ambiguous, or unnamed.
Count: 1 IWU.
Basis: one integration route wires reconciler behavior into sync/watch without changing backup-only behavior.

## Review Score

- Prior recorded score: none for this split child.
- Adversarial rescore basis: recounted from this leaf after splitting parent responsibilities; checked for hidden coupling, unrecorded routes, missing readiness fields, destructive writes, privacy-sensitive paths, and prerequisite order.
- Functions/methods: 2 x 2 = 4
- Data structures/models: 1 x 1 = 1
- Dependencies/services: 3 x 1 = 3
- Returns/outputs/signals: 1 x 1 = 1
- Existing reusable code reused as-is: 0 x 0.5 = 0
- Adding code to an existing library/module: 1 x 1 = 1
- Creating a new reusable library/module: 0 x 3 = 0
- Async/concurrency behavior: 1 x 3 = 3
- Destructive/write behavior: 1 x 3 = 3
- Security/privacy-sensitive behavior: 1 x 3 = 3
- Performance-sensitive behavior: 1 x 2 = 2
- Total: 21
- Split decision: score 16-24 retained because route wiring, idempotence, and service proof are one integration contract.

## Source Field Carryover

- Source purpose:
  - Wire active-surface reconciliation into explicit sync and watcher flows with idempotent repeated-event behavior.
- Source responsibilities by category:
  - Functions/methods, data structures, dependencies, outputs, write behavior, privacy, and performance are narrowed in the detailed sections below.
- Source open questions / nuance discovered:
  - No additional architecture gap remains after linked ACD defaults and parent architecture are applied.
- Source split/provenance notes:
  - Split from `project/specs/2.0.0p/active-surface-reconciliation.spec.md` during review pass 1.

## Purpose

Wire active-surface reconciliation into explicit sync and watcher flows with idempotent repeated-event behavior.

## Scope

Owns:

- sync route integration
- watch route integration
- idempotent repeated-event behavior
- backup-only regression proof through routes

Does not own:

- low-level dirty detection implementation
- fully managed local detection implementation
- LaunchAgent installer changes

## Split Coverage

- Parent spec: `project/specs/2.0.0p/active-surface-reconciliation.spec.md`
- Parent coverage status: covered by reviewed child specs.
- Parent responsibilities owned by this child:
  - sync/watch reconciliation route and repeated-event behavior.
- Parent responsibilities still missing from children:
  - none

## Refinement History

| Request ledger | Latest pass | Active specs reviewed | New leaves created this round | Fixed-point status |
|---|---:|---|---|---|
| `project/spec-refinement-history/2.0.0p-20260717-190429.md` | 2 | `project/specs/2.0.0p/active-surface-sync-watch-route.spec.md` | `none` | reached |

## Implementation Routing

- Primary modules/files:
  - `skills_keeper/cli.py` - sync/watch reconciliation call sites
- Supporting modules/files:
  - `skills_keeper/cli.py` - thin command wiring and existing error handling.
- GUI/QML files, if applicable:
  - `not applicable`
- Reusable library/module files:
  - `skills_keeper/cli.py` - sync/watch reconciliation call sites
- Tests:
  - `tests/test_active_surface.py` - sync/watch route integration tests

## Chosen Defaults / Parameters

- reconciliation runs for registered workspaces only
- logs status and paths, not file bodies
- repeated unchanged events do not create duplicate segregation records

## Data Ownership

- Source of truth: registered workspace state and active-surface module results.
- Read ownership: sync/watch command routes.
- Write ownership: active-surface module invoked by routes.
- Derived/cache data: route output derives from reconciliation result.
- Privacy/logging constraints: report ids, status, and paths only; do not print full skill bodies.

## Dependencies And Routes

- Domain/service dependencies:
  - `skills_keeper/cli.py` and related SkillsKeeper helpers.
- Database dependencies:
  - none unless explicitly named as datastore files.
- GUI route, if applicable:
  - not applicable
- Background/concurrency route, if applicable:
  - watch filesystem events trigger idempotent reconciliation; repeated unchanged events must not create duplicate segregation records.

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
  - `project/specs/2.0.0p/active-surface-dirty-checkout-segregation.spec.md` - route calls dirty checkout reconciliation
  - `project/specs/2.0.0p/active-surface-fully-managed-local.spec.md` - route calls fully managed reconciliation
- Progression handling:
  - implement after dirty checkout and fully managed local leaves.

## Application Integration

- App type: mixed console and background service.
- User/caller surface: `skillskeeper sync`; `skillskeeper watch`.
- Invocation route: explicit sync command and background watcher trigger.
- Wiring owner/module: `skills_keeper.cli`.
- Observable result: sync stdout, watcher-style reconciliation result, service log/status entries, segregation records, restored active files, and no duplicate segregation on repeated events.
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
  - feature API in `skills_keeper/cli.py` plus thin CLI wiring when applicable.
- New reusable modules to expose:
  - `skills_keeper/cli.py` if it does not already exist.
- One-off code justification, if any:
  - none

## Required DTOs / Functions / Components

- DTOs/models:
  - `ReconciliationResult` - changed paths, preserved records, restored entries, warnings
- Functions/methods:
  - `reconcile_workspace_active_surface(workspace) -> ReconciliationResult`
  - `sync_all(...) -> tuple[int, bool, bool] with reconciliation hook`
  - `watch callback -> reconciliation trigger`
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
  - sync/watch route integration tests.
- Service/DB tests:
  - temporary datastore/workspace fixtures only.
- GUI/controller tests, if applicable:
  - not applicable
- Integrated route tests:
  - CLI or consumer route smoke asserts observable result and side effects.
- Production-data rule:
  - Tests must not require the user's production database, live service, or real Codex skills root.

## Acceptance Criteria

- Sync invokes active-surface reconciliation.
- Watcher-style trigger invokes reconciliation.
- Repeated unchanged events do not duplicate segregation.
- Backup-only local archive behavior remains unchanged through sync.

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
