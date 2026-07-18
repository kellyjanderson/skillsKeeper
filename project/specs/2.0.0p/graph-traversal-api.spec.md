# Graph Traversal API Specification

Date: 2026-07-17
Status: Reviewed Draft
Primary ancestor: `project/architecture/skill-library-graph.md`
Architecture ancestor: `project/architecture/skill-library-graph.md; project/architecture/acd-2.0-implementation-defaults.md`
Source artifact: `project/architecture/skill-library-graph.md`
Split provenance: `project/specs/2.0.0p/graph-manifest-and-cache.spec.md`
Canonical status: `Canonical draft leaf`
Prerequisites:

- `project/specs/2.0.0p/implemented/graph-manifest-schema-validation.spec.md` - requires normalized valid graph input

## Work Units

Unit: Implementation Work Unit (IWU).
Definition: one independently deliverable, reviewable change set with its own verification surface. An IWU is intentionally abstract so the same unit can size software, documentation, tooling, service, research, design, and process projects.
Standard measures: count 1 IWU when the work has one primary outcome, one coherent responsibility boundary, one reviewable artifact or change set, one explicit verification method, declared inputs and outputs, and explicitly named unresolved assumptions or decisions. Split the work when any measure becomes plural, ambiguous, or unnamed.
Count: 1 IWU.
Basis: one traversal API contract for top-down resolution and bottom-up impact over validated graph data.

## Review Score

- Prior recorded score: none for this split child.
- Adversarial rescore basis: recounted from this leaf after splitting parent responsibilities; checked for hidden coupling, unrecorded routes, missing readiness fields, destructive writes, privacy-sensitive paths, and prerequisite order.
- Functions/methods: 3 x 2 = 6
- Data structures/models: 2 x 1 = 2
- Dependencies/services: 1 x 1 = 1
- Returns/outputs/signals: 1 x 1 = 1
- Existing reusable code reused as-is: 0 x 0.5 = 0
- Adding code to an existing library/module: 1 x 1 = 1
- Creating a new reusable library/module: 0 x 3 = 0
- Async/concurrency behavior: 0 x 3 = 0
- Destructive/write behavior: 0 x 3 = 0
- Security/privacy-sensitive behavior: 0 x 3 = 0
- Performance-sensitive behavior: 2 x 2 = 4
- Total: 15
- Split decision: below forced split threshold and one cohesive traversal responsibility.

## Source Field Carryover

- Source purpose:
  - Provide deterministic top-down checkout resolution and bottom-up impact traversal over the validated graph.
- Source responsibilities by category:
  - Functions/methods: resolve top down, resolve bottom up, detect traversal cycles.
  - Data structures/models: traversal result and graph path.
  - Dependencies/services: validated manifest from graph schema leaf.
  - Returns/outputs/signals: resolved skills, affected roots, traversal paths, conflicts.
  - Performance-sensitive behavior: bounded traversal.
- Source open questions / nuance discovered:
  - The traversal API is intentionally independent of Kuzu and cache storage.
- Source split/provenance notes:
  - Split from `project/specs/2.0.0p/graph-manifest-and-cache.spec.md` during review pass 1.

## Purpose

Provide deterministic top-down checkout resolution and bottom-up impact traversal over the validated graph.

## Scope

Owns:

- top-down root traversal
- bottom-up affected root traversal
- stable traversal result order
- conflict/replacement reporting when represented in graph edges

Does not own:

- manifest schema validation
- cache metadata persistence
- checkout copy operations

## Split Coverage

- Parent spec: `project/specs/2.0.0p/graph-manifest-and-cache.spec.md`
- Parent coverage status: covered by reviewed child specs.
- Parent responsibilities owned by this child:
  - top-down traversal, bottom-up traversal, conflict output, and stable ordering.
- Parent responsibilities still missing from children:
  - none

## Refinement History

| Request ledger | Latest pass | Active specs reviewed | New leaves created this round | Fixed-point status |
|---|---:|---|---|---|
| `project/spec-refinement-history/2.0.0p-20260717-190429.md` | 2 | `project/specs/2.0.0p/graph-traversal-api.spec.md` | `none` | reached |

## Implementation Routing

- Primary modules/files:
  - `skills_keeper/graph.py` - traversal functions and result DTOs
- Supporting modules/files:
  - `skills_keeper/cli.py` - thin command wiring and existing error handling.
- GUI/QML files, if applicable:
  - `not applicable`
- Reusable library/module files:
  - `skills_keeper/graph.py` - traversal functions and result DTOs
- Tests:
  - `tests/test_graph.py` - traversal result and cycle tests

## Chosen Defaults / Parameters

- traversal starts from explicit node id
- edge traversal is deterministic by relationship policy and declaration order
- cycles are reported and do not recurse forever

## Data Ownership

- Source of truth: validated graph manifest.
- Read ownership: graph traversal functions.
- Write ownership: none; traversal is read-only.
- Derived/cache data: traversal result can be recomputed from manifest.
- Privacy/logging constraints: report ids, status, and paths only; do not print full skill bodies.

## Dependencies And Routes

- Domain/service dependencies:
  - `skills_keeper.graph` validated manifest DTOs.
- Database dependencies:
  - none unless explicitly named as datastore files.
- GUI route, if applicable:
  - not applicable
- Background/concurrency route, if applicable:
  - not applicable.

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
  - `project/specs/2.0.0p/implemented/graph-manifest-schema-validation.spec.md` - requires normalized valid graph input
- Progression handling:
  - implement after manifest validation and before checkout/proposal leaves.

## Application Integration

- App type: library-only.
- User/caller surface: graph traversal APIs consumed by checkout and proposal modules.
- Invocation route: module call.
- Wiring owner/module: `skills_keeper.graph`.
- Observable result: TraversalResult containing skill ids, path metadata, conflicts, and affected roots.
- Integration validation: consumer tests from checkout and proposal routes plus graph unit tests.
- Incomplete status risk: helper-only implementation without this route proof is incomplete.

App-type-specific proof:

- GUI: not applicable.
- Console: command, args, stdout/stderr, exit code, and file side effects where the leaf has a CLI route.
- API-service: not applicable.
- Mixed: separate proof for console and watcher-style route when named.
- Library-only: consuming module proof is required when there is no direct CLI route.

## Reuse And Extraction Plan

- Existing code to reuse:
  - validated manifest DTOs from the graph module.
- Current reuse readiness:
  - available after schema-validation leaf.
- Extraction/wrapping needed:
  - none.
- Additions to existing library/modules:
  - traversal APIs in graph module.
- New reusable modules to expose:
  - none beyond `skills_keeper.graph`.
- One-off code justification, if any:
  - none

## Required DTOs / Functions / Components

- DTOs/models:
  - `TraversalResult` - resolved ids, paths, conflicts
  - `TraversalPath` - edge sequence from root to skill
- Functions/methods:
  - `resolve_top_down(manifest, root_id) -> TraversalResult`
  - `resolve_bottom_up(manifest, skill_id) -> TraversalResult`
  - `detect_traversal_cycle(manifest, start_id) -> list[str]`
- UI fields / visible data, if applicable:
  - not applicable
- UI elements / controls, if applicable:
  - not applicable
- UI components, if applicable:
  - not applicable

## Performance Contract

- Traversal is linear in reachable nodes plus edges and guards visited nodes.

## Error And State Behavior

- Missing root, unsupported relationship, and cycle errors are explicit and deterministic.

## Test Strategy

- Unit tests:
  - top-down, bottom-up, conflict, missing root, and cycle cases.
- Service/DB tests:
  - not applicable beyond temp manifest fixtures.
- GUI/controller tests, if applicable:
  - not applicable
- Integrated route tests:
  - checkout and proposal acceptance tests prove consumer integration.
- Production-data rule:
  - Tests must not require the user's production database, live service, or real Codex skills root.

## Acceptance Criteria

- Top-down traversal resolves expected skills in stable order.
- Bottom-up traversal reports affected roots for a skill.
- Cycles terminate with clear diagnostics.
- Traversal returns path metadata for review output.

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
