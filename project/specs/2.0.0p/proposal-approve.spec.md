# Proposal Approve Specification

Date: 2026-07-17
Status: Reviewed Draft
Primary ancestor: `project/architecture/library-update-proposals.md`
Architecture ancestor: `project/architecture/library-update-proposals.md`
Source artifact: `project/architecture/library-update-proposals.md`
Split provenance: `project/specs/2.0.0p/library-update-proposals.spec.md`
Canonical status: `Canonical draft leaf`
Prerequisites:

- `project/specs/2.0.0p/proposal-artifact-create.spec.md` - approval applies an existing proposal

## Work Units

Unit: Implementation Work Unit (IWU).
Definition: one independently deliverable, reviewable change set with its own verification surface. An IWU is intentionally abstract so the same unit can size software, documentation, tooling, service, research, design, and process projects.
Standard measures: count 1 IWU when the work has one primary outcome, one coherent responsibility boundary, one reviewable artifact or change set, one explicit verification method, declared inputs and outputs, and explicitly named unresolved assumptions or decisions. Split the work when any measure becomes plural, ambiguous, or unnamed.
Count: 1 IWU.
Basis: one destructive approval command applying reviewed proposal content exactly.

## Review Score

- Prior recorded score: none for this split child.
- Adversarial rescore basis: recounted from this leaf after splitting parent responsibilities; checked for hidden coupling, unrecorded routes, missing readiness fields, destructive writes, privacy-sensitive paths, and prerequisite order.
- Functions/methods: 3 x 2 = 6
- Data structures/models: 1 x 1 = 1
- Dependencies/services: 3 x 1 = 3
- Returns/outputs/signals: 1 x 1 = 1
- Existing reusable code reused as-is: 0 x 0.5 = 0
- Adding code to an existing library/module: 1 x 1 = 1
- Creating a new reusable library/module: 0 x 3 = 0
- Async/concurrency behavior: 0 x 3 = 0
- Destructive/write behavior: 1 x 3 = 3
- Security/privacy-sensitive behavior: 1 x 3 = 3
- Performance-sensitive behavior: 0 x 2 = 0
- Total: 18
- Split decision: score 16-24 retained because approval is one mutation route with validation guards.

## Source Field Carryover

- Source purpose:
  - Apply an approved library update proposal to reusable source and record the applied state.
- Source responsibilities by category:
  - Functions/methods, data structures, dependencies, outputs, write behavior, privacy, and performance are narrowed in the detailed sections below.
- Source open questions / nuance discovered:
  - No additional architecture gap remains after linked ACD defaults and parent architecture are applied.
- Source split/provenance notes:
  - Split from `project/specs/2.0.0p/library-update-proposals.spec.md` during review pass 1.

## Purpose

Apply an approved library update proposal to reusable source and record the applied state.

## Scope

Owns:

- `library approve` command
- status guard for approval
- source replacement and post-validation
- applied status transition

Does not own:

- proposal creation
- review output
- archive-proposal command

## Split Coverage

- Parent spec: `project/specs/2.0.0p/library-update-proposals.spec.md`
- Parent coverage status: covered by reviewed child specs.
- Parent responsibilities owned by this child:
  - proposal approval mutation and applied state transition.
- Parent responsibilities still missing from children:
  - none

## Refinement History

| Request ledger | Latest pass | Active specs reviewed | New leaves created this round | Fixed-point status |
|---|---:|---|---|---|
| `project/spec-refinement-history/2.0.0p-20260717-190429.md` | 2 | `project/specs/2.0.0p/proposal-approve.spec.md` | `none` | reached |

## Implementation Routing

- Primary modules/files:
  - `skills_keeper/proposals.py` - approval lifecycle
- Supporting modules/files:
  - `skills_keeper/cli.py` - thin command wiring and existing error handling.
- GUI/QML files, if applicable:
  - `not applicable`
- Reusable library/module files:
  - `skills_keeper/proposals.py` - approval lifecycle
- Tests:
  - `tests/test_proposals.py` - proposal approval tests

## Chosen Defaults / Parameters

- only review_required or approved proposal can be applied according to final state model
- approval validates after replacement
- failed validation preserves failure evidence

## Data Ownership

- Source of truth: proposal artifact until applied; library source after applied.
- Read ownership: proposal approval command.
- Write ownership: approval command writes reusable library source and proposal status.
- Derived/cache data: apply result derives from proposal record and validation.
- Privacy/logging constraints: report ids, status, and paths only; do not print full skill bodies.

## Dependencies And Routes

- Domain/service dependencies:
  - `skills_keeper/proposals.py` and related SkillsKeeper helpers.
- Database dependencies:
  - none unless explicitly named as datastore files.
- GUI route, if applicable:
  - not applicable
- Background/concurrency route, if applicable:
  - not applicable; proposal approval is an explicit command.

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
  - `project/specs/2.0.0p/proposal-artifact-create.spec.md` - approval applies an existing proposal
- Progression handling:
  - implement after proposal create; review output may be implemented before public use.

## Application Integration

- App type: console.
- User/caller surface: `skillskeeper library approve <proposal-id>`.
- Invocation route: explicit CLI command.
- Wiring owner/module: `skills_keeper.proposals`.
- Observable result: updated reusable library source, applied proposal status, validation result, stdout, and exit code.
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
  - feature API in `skills_keeper/proposals.py` plus thin CLI wiring when applicable.
- New reusable modules to expose:
  - `skills_keeper/proposals.py` if it does not already exist.
- One-off code justification, if any:
  - none

## Required DTOs / Functions / Components

- DTOs/models:
  - `ApplyResult` - target path, status, validation result
- Functions/methods:
  - `approve_proposal(proposal_id) -> ApplyResult`
  - `apply_proposed_content(record) -> ApplyResult`
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
  - proposal approval tests.
- Service/DB tests:
  - temporary datastore/workspace fixtures only.
- GUI/controller tests, if applicable:
  - not applicable
- Integrated route tests:
  - CLI or consumer route smoke asserts observable result and side effects.
- Production-data rule:
  - Tests must not require the user's production database, live service, or real Codex skills root.

## Acceptance Criteria

- Approval applies proposed content exactly.
- Proposal status becomes applied.
- Invalid status cannot be approved.
- Validation failure is reported with recovery evidence.

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
