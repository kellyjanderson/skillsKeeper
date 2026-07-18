# Checkout Segregated Discard Specification

Date: 2026-07-17
Status: Reviewed Draft
Primary ancestor: `project/architecture/project-checkouts-and-active-surface.md`
Architecture ancestor: `project/architecture/project-checkouts-and-active-surface.md`; `project/architecture/acd-active-surface-ownership-transition.md`; `project/architecture/acd-2.0-implementation-defaults.md`
Source artifact: `project/architecture/project-checkouts-and-active-surface.md`
Split provenance: `project/specs/2.0.0p/checkout-segregated-localize-discard.spec.md`
Canonical status: `Canonical draft leaf`
Prerequisites:

- `project/specs/2.0.0p/active-surface-dirty-checkout-segregation.spec.md` - discard operates on a preserved dirty checkout record.

## Work Units

Unit: Implementation Work Unit (IWU).
Definition: one independently deliverable, reviewable change set with its own verification surface. An IWU is intentionally abstract so the same unit can size software, documentation, tooling, service, research, design, and process projects.
Standard measures: count 1 IWU when the work has one primary outcome, one coherent responsibility boundary, one reviewable artifact or change set, one explicit verification method, declared inputs and outputs, and explicitly named unresolved assumptions or decisions. Split the work when any measure becomes plural, ambiguous, or unnamed.
Count: 1 IWU.
Basis: one command records a discard decision for one preserved generated checkout edit.

## Review Score

- Prior recorded score: split from parent score 27.5.
- Adversarial rescore basis: recounted from the discard-only route; checked for hidden localize/proposal responsibilities, destructive preserved-record handling, privacy, and route proof.
- Functions/methods: 2 x 2 = 4
- Data structures/models: 1 x 1 = 1
- Dependencies/services: 1 x 1 = 1
- Returns/outputs/signals: 1 x 1 = 1
- UI surfaces/components: 0 x 2 = 0
- UI fields/elements: 0 x 1 = 0
- Existing reusable code reused as-is: 1 x 0.5 = 0.5
- Adding code to an existing library/module: 1 x 1 = 1
- Creating a new reusable library/module: 0 x 3 = 0
- Database queries/tables/migrations: 0 x 2 = 0
- Async/concurrency behavior: 0 x 3 = 0
- Destructive/write behavior: 1 x 3 = 3
- Security/privacy-sensitive behavior: 1 x 3 = 3
- Performance-sensitive behavior: 1 x 2 = 2
- Cross-screen reusable behavior: 0 x 2 = 0
- Readiness blockers: 0 x 2 = 0
- Missing prerequisites: 0 x 2 = 0
- Total: 16.5
- Split decision: score 16-24 retained because discard is one small recovery route with a single durable state transition.

## Source Field Carryover

- Source purpose:
  - Architecture names `checkout discard` as a recovery action after dirty generated checkout segregation.
- Source responsibilities by category:
  - Functions/methods: find segregation record and mark it discarded.
  - Data structures/models: segregation record status.
  - Dependencies/services: active-surface segregation store.
  - Returns/outputs/signals: discarded status, stdout, exit code.
  - UI surfaces/components: not applicable.
  - UI fields/elements: not applicable.
  - Reusable code plan: active-surface recovery helper consumed by CLI.
  - Database queries/tables/migrations: none.
  - Async/concurrency behavior: not applicable.
  - Destructive/write behavior: removes or marks preserved candidate inactive.
  - Security/privacy-sensitive behavior: preserved skill body is local user data.
  - Performance-sensitive behavior: one workspace and one skill id.
- Source open questions / nuance discovered:
  - Discard does not decide retention pruning policy beyond 2.0.0's explicit user action.
- Source split/provenance notes:
  - Split from the localize/discard parent during architecture cross-check review.

## Purpose

Let users explicitly discard a preserved dirty generated checkout edit without
mutating library source or the restored clean active checkout.

## Scope

Owns:

- `skillskeeper checkout discard <skill-id> --workspace <path>`
- segregation record transition to discarded
- source-unchanged and active-clean-checkout-unchanged guarantees

Does not own:

- localize recovery
- proposal creation from the preserved edit
- retention pruning of discarded records beyond marking or moving one record

## Split Coverage

- Parent spec: `project/specs/2.0.0p/checkout-segregated-localize-discard.spec.md`
- Parent coverage status: covered by reviewed child specs.
- Parent responsibilities owned by this child:
  - discard recovery command and segregation status transition.
- Parent responsibilities still missing from children:
  - none

## Refinement History

| Request ledger | Latest pass | Active specs reviewed | New leaves created this round | Fixed-point status |
|---|---:|---|---|---|
| `project/spec-refinement-history/2.0.0p-architecture-crosscheck-20260717-194042.md` | 2 | `project/specs/2.0.0p/checkout-segregated-discard.spec.md` | none | reached |

## Implementation Routing

- Primary modules/files:
  - `skills_keeper/active_surface.py` - segregation record lookup and discard action.
  - `skills_keeper/cli.py` - `checkout discard` command handler.
- Supporting modules/files:
  - `skills_keeper/cli.py` - existing path resolution and command error handling until helpers are extracted.
- GUI/QML files, if applicable:
  - `not applicable`
- Reusable library/module files:
  - `skills_keeper/active_surface.py` - reusable discard recovery API.
- Tests:
  - `tests/test_active_surface.py` - discard recovery tests.

## Chosen Defaults / Parameters

- Segregation records are addressed by skill id plus workspace.
- Discard marks a record discarded or moves it into a discarded state.
- Discard does not mutate reusable library source.
- Discard does not mutate the restored clean active checkout.

## Data Ownership

- Source of truth: segregation record.
- Read ownership: active-surface discard helper reads segregation metadata.
- Write ownership: discard command writes segregation status.
- Derived/cache data: none; discard result is a durable user choice.
- Privacy/logging constraints: command output may name paths and statuses, not full skill bodies.

## Dependencies And Routes

- Domain/service dependencies:
  - `skills_keeper.active_surface`
- Database dependencies:
  - none.
- GUI route, if applicable:
  - not applicable
- Background/concurrency route, if applicable:
  - not applicable; this is an explicit recovery command.

## Prerequisite Handling

- Architecture feedback artifacts:
  - `project/architecture/acd-active-surface-ownership-transition.md`
  - `project/architecture/acd-2.0-implementation-defaults.md`
- Architecture feedback status:
  - tracked in ACDs.
- Already implemented prerequisites:
  - existing path and state helpers.
- Missing prerequisite architecture:
  - none
- Missing prerequisite specifications:
  - none
- Unimplemented prerequisite specifications:
  - `project/specs/2.0.0p/active-surface-dirty-checkout-segregation.spec.md`
- Progression handling:
  - implement after segregation leaf.

## Application Integration

- App type: console.
- User/caller surface: `skillskeeper checkout discard <skill-id> --workspace <path>`.
- Invocation route: explicit CLI command.
- Wiring owner/module: `skills_keeper.cli`.
- Observable result: segregation record discarded status, stdout status, exit code, unchanged library source, and unchanged restored active checkout.
- Integration validation: CLI route test with temporary workspace and segregation fixture.
- Incomplete status risk: helper-only discard behavior without the CLI route is incomplete.

App-type-specific proof:

- GUI: not applicable.
- Console: command, args, stdout/stderr, exit code, segregation status, and unchanged source assertions.
- API-service: not applicable.
- Mixed: not applicable.
- Library-only: not applicable.

## Reuse And Extraction Plan

- Existing code to reuse:
  - path resolution, `skill_identity`, and segregation record helpers.
- Current reuse readiness:
  - available after active-surface module exists.
- Extraction/wrapping needed:
  - discard helper should live in `skills_keeper.active_surface`.
- Additions to existing library/modules:
  - active-surface discard API.
- New reusable modules to expose:
  - none beyond planned active-surface module.
- One-off code justification, if any:
  - none

## Required DTOs / Functions / Components

- DTOs/models:
  - `SegregationRecoveryResult` - action, skill id, segregation path, status.
  - `SegregationRecordStatus` - active, localized, discarded, proposed.
- Functions/methods:
  - `find_segregation_record(workspace, skill_id) -> SegregationRecord`
  - `discard_segregated_checkout(workspace, skill_id) -> SegregationRecoveryResult`
- UI fields / visible data, if applicable:
  - not applicable
- UI elements / controls, if applicable:
  - not applicable
- UI components, if applicable:
  - not applicable

## Performance Contract

- Discard addresses one workspace and one skill id without scanning unrelated workspaces or global mirrors.

## Error And State Behavior

- Missing segregation record fails without mutating active skills, lockfile, or library source.
- Already resolved records report their existing status and do not create duplicate transitions.
- Discard does not delete library source.

## Test Strategy

- Unit tests:
  - record lookup, discard transition, already-resolved handling, and unchanged-source assertions.
- Service/DB tests:
  - temporary workspace with segregation record.
- GUI/controller tests, if applicable:
  - not applicable
- Integrated route tests:
  - CLI `checkout discard` smoke asserts stdout, exit code, segregation status, and unchanged library/active files.
- Production-data rule:
  - Tests must not require production datastore, live service, or real `~/.codex/skills`.

## Acceptance Criteria

- `checkout discard` records the user discard decision without mutating library source.
- `checkout discard` leaves the restored clean active checkout unchanged.
- Discard fails safely when the segregation record is missing.
- Repeated discard reports an already-resolved status without duplicate records.
- CLI tests prove the user-facing recovery route.

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
