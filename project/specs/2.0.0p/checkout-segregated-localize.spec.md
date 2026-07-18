# Checkout Segregated Localize Specification

Date: 2026-07-17
Status: Reviewed Draft
Primary ancestor: `project/architecture/project-checkouts-and-active-surface.md`
Architecture ancestor: `project/architecture/project-checkouts-and-active-surface.md`; `project/architecture/acd-active-surface-ownership-transition.md`; `project/architecture/acd-2.0-implementation-defaults.md`
Source artifact: `project/architecture/project-checkouts-and-active-surface.md`
Split provenance: `project/specs/2.0.0p/checkout-segregated-localize-discard.spec.md`
Canonical status: `Canonical draft leaf`
Prerequisites:

- `project/specs/2.0.0p/active-surface-dirty-checkout-segregation.spec.md` - localize operates on a preserved dirty checkout record.
- `project/specs/2.0.0p/checkout-lockfile-schema.spec.md` - localize updates generated checkout ownership.

## Work Units

Unit: Implementation Work Unit (IWU).
Definition: one independently deliverable, reviewable change set with its own verification surface. An IWU is intentionally abstract so the same unit can size software, documentation, tooling, service, research, design, and process projects.
Standard measures: count 1 IWU when the work has one primary outcome, one coherent responsibility boundary, one reviewable artifact or change set, one explicit verification method, declared inputs and outputs, and explicitly named unresolved assumptions or decisions. Split the work when any measure becomes plural, ambiguous, or unnamed.
Count: 1 IWU.
Basis: one command converts one preserved generated checkout edit into project-owned local source.

## Review Score

- Prior recorded score: split from parent score 27.5.
- Adversarial rescore basis: recounted from the localize-only route; checked for hidden discard/proposal responsibilities, lockfile mutation, active-surface writes, privacy, and route proof.
- Functions/methods: 3 x 2 = 6
- Data structures/models: 2 x 1 = 2
- Dependencies/services: 3 x 1 = 3
- Returns/outputs/signals: 2 x 1 = 2
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
- Total: 22.5
- Split decision: score 16-24 retained because localize is one cohesive recovery route with explicit write and verification boundaries.

## Source Field Carryover

- Source purpose:
  - Architecture names `checkout localize` as a recovery action after dirty generated checkout segregation.
- Source responsibilities by category:
  - Functions/methods: find segregation record, validate preserved skill, write active project-owned skill, update lockfile ownership.
  - Data structures/models: segregation record status and localize result.
  - Dependencies/services: active-surface segregation store, checkout lockfile, skill validation.
  - Returns/outputs/signals: localized active path, lockfile status, stdout, exit code.
  - UI surfaces/components: not applicable.
  - UI fields/elements: not applicable.
  - Reusable code plan: active-surface recovery helper consumed by CLI.
  - Database queries/tables/migrations: none.
  - Async/concurrency behavior: not applicable.
  - Destructive/write behavior: writes active project-owned skill and lockfile state.
  - Security/privacy-sensitive behavior: preserved skill body is local user data.
  - Performance-sensitive behavior: one workspace and one skill id.
- Source open questions / nuance discovered:
  - Overlay remains deferred by `project/architecture/acd-2.0-implementation-defaults.md`.
- Source split/provenance notes:
  - Split from the localize/discard parent during architecture cross-check review.

## Purpose

Convert a preserved dirty generated checkout edit into a project-owned local
skill so future generated-checkout reconciliation does not overwrite it.

## Scope

Owns:

- `skillskeeper checkout localize <skill-id> --workspace <path>`
- validation of the preserved skill before restoring it
- active `.agents/skills/<skill-id>` write for the localized project-owned copy
- checkout lockfile update so the skill is no longer treated as generated
- segregation record transition to localized

Does not own:

- discard recovery
- proposal creation from the preserved edit
- overlay composition

## Split Coverage

- Parent spec: `project/specs/2.0.0p/checkout-segregated-localize-discard.spec.md`
- Parent coverage status: covered by reviewed child specs.
- Parent responsibilities owned by this child:
  - localize recovery command and generated-to-project-owned ownership transition.
- Parent responsibilities still missing from children:
  - none

## Refinement History

| Request ledger | Latest pass | Active specs reviewed | New leaves created this round | Fixed-point status |
|---|---:|---|---|---|
| `project/spec-refinement-history/2.0.0p-architecture-crosscheck-20260717-194042.md` | 2 | `project/specs/2.0.0p/checkout-segregated-localize.spec.md` | none | reached |

## Implementation Routing

- Primary modules/files:
  - `skills_keeper/active_surface.py` - segregation record lookup and localize action.
  - `skills_keeper/checkout.py` - lockfile generated-entry removal or ownership conversion.
  - `skills_keeper/cli.py` - `checkout localize` command handler.
- Supporting modules/files:
  - `skills_keeper/cli.py` - existing validation, path resolution, and command error handling until helpers are extracted.
- GUI/QML files, if applicable:
  - `not applicable`
- Reusable library/module files:
  - `skills_keeper/active_surface.py` - reusable localize recovery API.
- Tests:
  - `tests/test_active_surface.py` - localize recovery tests.
  - `tests/test_checkout.py` - lockfile ownership regression tests.

## Chosen Defaults / Parameters

- Segregation records are addressed by skill id plus workspace.
- Localize validates the preserved skill before writing it back.
- Localize removes the generated checkout entry unless implementation chooses a reviewed project-owned ownership marker.
- Localize does not mutate library source.
- Localize does not perform overlay merge.

## Data Ownership

- Source of truth: segregation record and checkout lockfile.
- Read ownership: active-surface localize helper reads segregation metadata and lockfile state.
- Write ownership: localize command writes active project skill, segregation status, and lockfile ownership state.
- Derived/cache data: none; localize result is a durable user choice.
- Privacy/logging constraints: command output may name paths and statuses, not full skill bodies.

## Dependencies And Routes

- Domain/service dependencies:
  - `skills_keeper.active_surface`
  - `skills_keeper.checkout`
  - skill validation helpers
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
  - existing path, validation, and copy helpers.
- Missing prerequisite architecture:
  - none
- Missing prerequisite specifications:
  - none
- Unimplemented prerequisite specifications:
  - `project/specs/2.0.0p/active-surface-dirty-checkout-segregation.spec.md`
  - `project/specs/2.0.0p/checkout-lockfile-schema.spec.md`
- Progression handling:
  - implement after segregation and lockfile leaves.

## Application Integration

- App type: console.
- User/caller surface: `skillskeeper checkout localize <skill-id> --workspace <path>`.
- Invocation route: explicit CLI command.
- Wiring owner/module: `skills_keeper.cli`.
- Observable result: active project-owned skill restored, generated checkout ownership removed or converted, segregation record localized, stdout status, and exit code.
- Integration validation: CLI route test with temporary workspace, lockfile, and segregation fixtures.
- Incomplete status risk: helper-only localize behavior without the CLI route is incomplete.

App-type-specific proof:

- GUI: not applicable.
- Console: command, args, stdout/stderr, exit code, active folder side effects, lockfile side effects, and segregation status.
- API-service: not applicable.
- Mixed: not applicable.
- Library-only: not applicable.

## Reuse And Extraction Plan

- Existing code to reuse:
  - `validate_skill_dir`, `copy_tree_clean`, `skill_identity`, path resolution, and lockfile helpers.
- Current reuse readiness:
  - available after checkout and active-surface modules exist.
- Extraction/wrapping needed:
  - localize helper should live in `skills_keeper.active_surface` rather than CLI command body.
- Additions to existing library/modules:
  - active-surface localize API and checkout lockfile ownership helper.
- New reusable modules to expose:
  - none beyond planned active-surface and checkout modules.
- One-off code justification, if any:
  - none

## Required DTOs / Functions / Components

- DTOs/models:
  - `SegregationRecoveryResult` - action, skill id, active path, segregation path, lockfile status.
  - `SegregationRecordStatus` - active, localized, discarded, proposed.
- Functions/methods:
  - `find_segregation_record(workspace, skill_id) -> SegregationRecord`
  - `localize_segregated_checkout(workspace, skill_id) -> SegregationRecoveryResult`
  - `remove_checkout_entry(workspace, skill_id) -> CheckoutLockfile`
- UI fields / visible data, if applicable:
  - not applicable
- UI elements / controls, if applicable:
  - not applicable
- UI components, if applicable:
  - not applicable

## Performance Contract

- Localize addresses one workspace and one skill id without scanning unrelated workspaces or global mirrors.

## Error And State Behavior

- Missing segregation record fails without mutating active skills or lockfile.
- Invalid preserved skill fails localize and keeps the preserved copy available.
- Lockfile update failure leaves the preserved copy and reports recovery state.
- Localize does not delete library source.

## Test Strategy

- Unit tests:
  - record lookup, localize state transition, invalid preserved skill, and lockfile conversion.
- Service/DB tests:
  - temporary workspace with generated checkout, lockfile, and segregation record.
- GUI/controller tests, if applicable:
  - not applicable
- Integrated route tests:
  - CLI `checkout localize` smoke asserts stdout, exit code, active files, lockfile state, and segregation status.
- Production-data rule:
  - Tests must not require production datastore, live service, or real `~/.codex/skills`.

## Acceptance Criteria

- `checkout localize` restores the preserved skill as project-owned local source.
- `checkout localize` prevents future generated-checkout reconciliation from overwriting the localized skill.
- Localize fails safely when the segregation record is missing or invalid.
- Localize does not mutate reusable library source.
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
