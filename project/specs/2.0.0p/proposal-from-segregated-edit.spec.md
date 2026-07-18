# Proposal From Segregated Edit Specification

Date: 2026-07-17
Status: Reviewed Draft
Primary ancestor: `project/architecture/library-update-proposals.md`
Architecture ancestor: `project/architecture/library-update-proposals.md`; `project/architecture/project-checkouts-and-active-surface.md`; `project/architecture/acd-active-surface-ownership-transition.md`; `project/architecture/acd-2.0-implementation-defaults.md`
Source artifact: `project/architecture/library-update-proposals.md`
Split provenance: `architecture coverage review 20260717-194042`
Canonical status: `Canonical draft leaf`
Prerequisites:

- `project/specs/2.0.0p/active-surface-dirty-checkout-segregation.spec.md` - provides preserved dirty checkout records.
- `project/specs/2.0.0p/proposal-artifact-create.spec.md` - provides proposal artifact creation.
- `project/specs/2.0.0p/proposal-review-impact.spec.md` - provides impact review for the resulting proposal.

## Work Units

Unit: Implementation Work Unit (IWU).
Definition: one independently deliverable, reviewable change set with its own verification surface. An IWU is intentionally abstract so the same unit can size software, documentation, tooling, service, research, design, and process projects.
Standard measures: count 1 IWU when the work has one primary outcome, one coherent responsibility boundary, one reviewable artifact or change set, one explicit verification method, declared inputs and outputs, and explicitly named unresolved assumptions or decisions. Split the work when any measure becomes plural, ambiguous, or unnamed.
Count: 1 IWU.
Basis: one adapter route converts a preserved dirty checkout into the existing proposal lifecycle.

## Review Score

- Prior recorded score: none for this review-created coverage leaf.
- Adversarial rescore basis: recounted from architecture and ACD source; checked for missing proposal source route, duplicate proposal logic, sensitive preserved content, and impact-review prerequisites.
- Functions/methods: 3 x 2 = 6
- Data structures/models: 2 x 1 = 2
- Dependencies/services: 3 x 1 = 3
- Returns/outputs/signals: 2 x 1 = 2
- UI surfaces/components: 0 x 2 = 0
- UI fields/elements: 0 x 1 = 0
- Existing reusable code reused as-is: 2 x 0.5 = 1
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
- Total: 23
- Split decision: score 16-24 retained because this leaf only adapts a segregated edit into the already-specified proposal lifecycle.

## Source Field Carryover

- Source purpose:
  - Architecture requires dirty checkout recovery choices to include proposing reusable library updates when an edit appears reusable.
- Source responsibilities by category:
  - Functions/methods: find segregation record, validate preserved skill, create proposal from preserved path, mark segregation record proposed.
  - Data structures/models: proposal source metadata and segregation recovery status.
  - Dependencies/services: active-surface segregation store, proposal store, graph impact review.
  - Returns/outputs/signals: proposal id/path, `review_required` status, segregation record proposed status.
  - UI surfaces/components: not applicable.
  - UI fields/elements: not applicable.
  - Reusable code plan: reuse proposal creation rather than duplicating proposal schema or diff logic.
  - Database queries/tables/migrations: none.
  - Async/concurrency behavior: not applicable.
  - Destructive/write behavior: writes proposal artifact and segregation status; does not mutate reusable source.
  - Security/privacy-sensitive behavior: preserved skill bodies are local user data.
  - Performance-sensitive behavior: bounded to one segregation record and normal proposal impact flow.
- Source open questions / nuance discovered:
  - Split and overlay recovery choices remain outside 2.0.0 implementation unless a later ACD accepts them.
- Source split/provenance notes:
  - Created during architecture/ACD cross-check because proposal creation from a segregated edit was implied by architecture but missing from active specs.

## Purpose

Let users turn a segregated dirty checkout into a normal library update proposal
without directly mutating reusable library source.

## Scope

Owns:

- `skillskeeper checkout propose-update <skill-id> --workspace <path>`
- proposal source metadata for `segregated-checkout`
- transition of a segregation record to proposed status
- reuse of existing proposal artifact creation and review impact flow

Does not own:

- proposal approval
- proposal review rendering beyond returning the normal proposal id/path
- localize or discard recovery commands
- overlay or split recovery commands

## Split Coverage

- Parent spec: `none`
- Parent coverage status: not applicable
- Parent responsibilities owned by this child:
  - proposal-from-segregated-edit recovery path implied by dirty checkout architecture.
- Parent responsibilities still missing from children:
  - none

## Refinement History

| Request ledger | Latest pass | Active specs reviewed | New leaves created this round | Fixed-point status |
|---|---:|---|---|---|
| `project/spec-refinement-history/2.0.0p-architecture-crosscheck-20260717-194042.md` | 2 | `project/specs/2.0.0p/proposal-from-segregated-edit.spec.md` | none | reached |

## Implementation Routing

- Primary modules/files:
  - `skills_keeper/active_surface.py` - segregation record lookup and proposed status update.
  - `skills_keeper/proposals.py` - proposal creation from preserved skill path.
  - `skills_keeper/cli.py` - `checkout propose-update` command handler.
- Supporting modules/files:
  - `skills_keeper/checkout.py` - skill id and workspace lockfile context.
- GUI/QML files, if applicable:
  - `not applicable`
- Reusable library/module files:
  - `skills_keeper/proposals.py` - source-aware proposal creation reused by CLI and future agent integrations.
- Tests:
  - `tests/test_proposals.py` - proposal-from-segregated-edit lifecycle.
  - `tests/test_active_surface.py` - segregation status transition.

## Chosen Defaults / Parameters

- Command name is `skillskeeper checkout propose-update <skill-id> --workspace <path>` for 2.0.0.
- Proposal source metadata includes `source_kind: segregated-checkout`, workspace path, original active path, preserved path, and segregation timestamp.
- The command returns `review_required` and does not mutate reusable source.
- Missing or invalid segregation records fail without proposal creation.

## Data Ownership

- Source of truth: segregation record and proposal artifact.
- Read ownership: active-surface recovery helpers read segregation metadata; proposal module reads preserved skill content.
- Write ownership: proposal module writes proposal artifact; active-surface module marks segregation record proposed.
- Derived/cache data: proposal diff and impact can be recomputed from proposal artifact, graph, and checkout lockfiles.
- Privacy/logging constraints: command output may name proposal and preserved paths, not full skill bodies.

## Dependencies And Routes

- Domain/service dependencies:
  - `skills_keeper.active_surface`
  - `skills_keeper.proposals`
  - `skills_keeper.checkout`
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
  - existing validation and path helpers.
- Missing prerequisite architecture:
  - none
- Missing prerequisite specifications:
  - none
- Unimplemented prerequisite specifications:
  - `project/specs/2.0.0p/active-surface-dirty-checkout-segregation.spec.md`
  - `project/specs/2.0.0p/proposal-artifact-create.spec.md`
  - `project/specs/2.0.0p/proposal-review-impact.spec.md`
- Progression handling:
  - implement after segregation and base proposal creation.

## Application Integration

- App type: console.
- User/caller surface: `skillskeeper checkout propose-update <skill-id> --workspace <path>`.
- Invocation route: explicit CLI command.
- Wiring owner/module: `skills_keeper.cli`.
- Observable result: proposal id/path, `review_required` status, segregation record proposed status, stdout summary, and exit code.
- Integration validation: CLI route test with temporary workspace, segregation record, proposal store, graph, and checkout fixtures.
- Incomplete status risk: creating proposals only from arbitrary paths leaves the architecture's segregated-edit recovery route incomplete.

App-type-specific proof:

- GUI: not applicable.
- Console: command, args, stdout/stderr, exit code, proposal artifact, and segregation status.
- API-service: not applicable.
- Mixed: not applicable.
- Library-only: not applicable.

## Reuse And Extraction Plan

- Existing code to reuse:
  - `create_update_proposal`, proposal id/path helpers, `validate_skill_dir`, and segregation record lookup.
- Current reuse readiness:
  - available after base proposal and active-surface leaves exist.
- Extraction/wrapping needed:
  - proposal creation must accept source metadata rather than hard-code command-origin metadata.
- Additions to existing library/modules:
  - source-aware proposal creation and segregation proposed-state helper.
- New reusable modules to expose:
  - none beyond planned active-surface and proposal modules.
- One-off code justification, if any:
  - none

## Required DTOs / Functions / Components

- DTOs/models:
  - `ProposalSourceMetadata` - source kind, workspace, original path, preserved path, segregation timestamp.
  - `SegregationRecordStatus` - active, localized, discarded, proposed.
- Functions/methods:
  - `create_proposal_from_segregated_edit(workspace, skill_id) -> ProposalRecord`
  - `mark_segregation_proposed(record, proposal_id) -> SegregationRecord`
  - `proposal_source_metadata_from_segregation(record) -> ProposalSourceMetadata`
- UI fields / visible data, if applicable:
  - not applicable
- UI elements / controls, if applicable:
  - not applicable
- UI components, if applicable:
  - not applicable

## Performance Contract

- Command operates on one segregation record and then delegates impact calculation to the reviewed proposal impact path.

## Error And State Behavior

- Missing segregation record fails before proposal creation.
- Invalid preserved skill fails before proposal creation and keeps the segregation record active.
- Proposal creation failure does not mark the segregation record proposed.
- Re-running after a successful proposal reports the existing proposal or fails with an already-proposed status without creating duplicates.

## Test Strategy

- Unit tests:
  - source metadata construction, proposed status transition, duplicate proposal guard.
- Service/DB tests:
  - temporary workspace segregation record plus temporary proposal store.
- GUI/controller tests, if applicable:
  - not applicable
- Integrated route tests:
  - CLI `checkout propose-update` smoke asserts stdout, exit code, proposal artifact, and segregation status.
- Production-data rule:
  - Tests must not require production datastore, live service, or real `~/.codex/skills`.

## Acceptance Criteria

- `checkout propose-update` creates a normal `review_required` proposal from a segregated dirty checkout.
- Proposal metadata records the segregated source path and workspace context.
- Reusable library source is unchanged until the normal approval command runs.
- Segregation record is marked proposed only after proposal creation succeeds.
- Duplicate command invocation does not create duplicate active proposals.

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
