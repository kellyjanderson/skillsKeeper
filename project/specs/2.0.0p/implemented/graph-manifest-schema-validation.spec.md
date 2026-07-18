# Graph Manifest Schema Validation Specification

Date: 2026-07-17
Status: Implemented
Primary ancestor: `project/architecture/skill-library-graph.md`
Architecture ancestor: `project/architecture/skill-library-graph.md; project/architecture/acd-2.0-implementation-defaults.md`
Source artifact: `project/architecture/skill-library-graph.md`
Split provenance: `project/specs/2.0.0p/graph-manifest-and-cache.spec.md`
Canonical status: `Implemented canonical leaf`
Prerequisites:

- `project/architecture/acd-2.0-implementation-defaults.md` - pins JSON as canonical graph source for 2.0.0

## Work Units

Unit: Implementation Work Unit (IWU).
Definition: one independently deliverable, reviewable change set with its own verification surface. An IWU is intentionally abstract so the same unit can size software, documentation, tooling, service, research, design, and process projects.
Standard measures: count 1 IWU when the work has one primary outcome, one coherent responsibility boundary, one reviewable artifact or change set, one explicit verification method, declared inputs and outputs, and explicitly named unresolved assumptions or decisions. Split the work when any measure becomes plural, ambiguous, or unnamed.
Count: 1 IWU.
Basis: one canonical manifest validation contract with deterministic normalized output.

## Review Score

- Prior recorded score: none for this split child.
- Adversarial rescore basis: recounted from this leaf after splitting parent responsibilities; checked for hidden coupling, unrecorded routes, missing readiness fields, destructive writes, privacy-sensitive paths, and prerequisite order.
- Functions/methods: 4 x 2 = 8
- Data structures/models: 3 x 1 = 3
- Dependencies/services: 1 x 1 = 1
- Returns/outputs/signals: 1 x 1 = 1
- Existing reusable code reused as-is: 0 x 0.5 = 0
- Adding code to an existing library/module: 0 x 1 = 0
- Creating a new reusable library/module: 1 x 3 = 3
- Async/concurrency behavior: 0 x 3 = 0
- Destructive/write behavior: 0 x 3 = 0
- Security/privacy-sensitive behavior: 1 x 3 = 3
- Performance-sensitive behavior: 1 x 2 = 2
- Total: 21
- Split decision: score 16-24 retained as one leaf because schema load, validation, normalization, and hash output are one cohesive graph-source contract.

## Source Field Carryover

- Source purpose:
  - Define and validate the JSON skill graph manifest so downstream graph operations have trusted normalized input.
- Source responsibilities by category:
  - Functions/methods: load manifest, validate nodes, validate edges, normalize ids, hash normalized content.
  - Data structures/models: manifest, node, edge, validation error.
  - Dependencies/services: JSON parser and local filesystem only.
  - Returns/outputs/signals: validation result, normalized manifest, manifest hash.
  - Destructive/write behavior: none.
  - Performance-sensitive behavior: bounded by manifest size.
- Source open questions / nuance discovered:
  - Kuzu remains outside this leaf; the manifest must be useful without it.
- Source split/provenance notes:
  - Split from `project/specs/2.0.0p/graph-manifest-and-cache.spec.md` during review pass 1.

## Purpose

Define and validate the JSON skill graph manifest so downstream graph operations have trusted normalized input.

## Scope

Owns:

- manifest schema file and schema-version rules
- validation errors for missing ids, unknown types, invalid edges, duplicate ids, and cycles where validation owns them
- stable normalization and manifest hash calculation

Does not own:

- cache metadata writes
- top-down or bottom-up traversal semantics
- CLI graph command output beyond validation errors

## Split Coverage

- Parent spec: `project/specs/2.0.0p/graph-manifest-and-cache.spec.md`
- Parent coverage status: covered by reviewed child specs.
- Parent responsibilities owned by this child:
  - graph manifest schema, validation, normalization, and manifest hash responsibilities.
- Parent responsibilities still missing from children:
  - none

## Refinement History

| Request ledger | Latest pass | Active specs reviewed | New leaves created this round | Fixed-point status |
|---|---:|---|---|---|
| `project/spec-refinement-history/2.0.0p-20260717-190429.md` | 2 | `project/specs/2.0.0p/graph-manifest-schema-validation.spec.md` | `none` | reached |

## Implementation Routing

- Primary modules/files:
  - `skills_keeper/graph.py` - manifest models, validation, normalization, hash helpers
- Supporting modules/files:
  - `skills_keeper/cli.py` - thin command wiring and existing error handling.
- GUI/QML files, if applicable:
  - `not applicable`
- Reusable library/module files:
  - `skills_keeper/graph.py` - manifest models, validation, normalization, hash helpers
- Tests:
  - `tests/test_graph.py` - manifest schema and validation tests

## Chosen Defaults / Parameters

- graph source file name defaults to `skill-graph.json`
- schema file name defaults to `skill-graph.schema.json`
- node ids are normalized with SkillsKeeper slug rules
- validation must not write cache files

## Data Ownership

- Source of truth: datastore graph manifest JSON.
- Read ownership: graph module.
- Write ownership: graph authoring or future import routes; this leaf reads and validates only.
- Derived/cache data: normalized manifest and hash are derived from JSON source.
- Privacy/logging constraints: report ids, status, and paths only; do not print full skill bodies.

## Dependencies And Routes

- Domain/service dependencies:
  - `skills_keeper.graph`, standard `json`, local path helpers.
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
  - `project/architecture/acd-2.0-implementation-defaults.md` - pins JSON as canonical graph source for 2.0.0
- Progression handling:
  - implement before traversal, cache, checkout, and proposal impact leaves.

## Application Integration

- App type: library-only with console error exposure.
- User/caller surface: graph validation consumed by `skillskeeper library graph rebuild` and `status`.
- Invocation route: module call from graph command handlers.
- Wiring owner/module: `skills_keeper.graph`.
- Observable result: validation errors, normalized ids, and manifest hash.
- Integration validation: module tests plus CLI rebuild failure smoke for invalid fixtures.
- Incomplete status risk: helper-only implementation without this route proof is incomplete.

App-type-specific proof:

- GUI: not applicable.
- Console: command, args, stdout/stderr, exit code, and file side effects where the leaf has a CLI route.
- API-service: not applicable.
- Mixed: separate proof for console and watcher-style route when named.
- Library-only: consuming module proof is required when there is no direct CLI route.

## Reuse And Extraction Plan

- Existing code to reuse:
  - `skill_identity` slug behavior from `skills_keeper.cli` or extracted helper.
- Current reuse readiness:
  - reuse as-is initially; extract if graph module import direction becomes awkward.
- Extraction/wrapping needed:
  - optional shared `skills_keeper/ids.py`.
- Additions to existing library/modules:
  - new graph module validation APIs.
- New reusable modules to expose:
  - `skills_keeper.graph`.
- One-off code justification, if any:
  - none

## Required DTOs / Functions / Components

- DTOs/models:
  - `GraphManifest` - schema version, nodes, edges
  - `GraphNode` - id, type, skill metadata
  - `GraphEdge` - source, target, relationship
  - `GraphValidationError` - path and message
- Functions/methods:
  - `load_manifest(path) -> GraphManifest`
  - `validate_manifest(manifest) -> list[GraphValidationError]`
  - `normalize_manifest(manifest) -> GraphManifest`
  - `manifest_hash(manifest) -> str`
- UI fields / visible data, if applicable:
  - not applicable
- UI elements / controls, if applicable:
  - not applicable
- UI components, if applicable:
  - not applicable

## Performance Contract

- Validation is linear in nodes plus edges and must terminate on cycles.

## Error And State Behavior

- Invalid manifests return all practical validation errors and prevent cache writes.

## Test Strategy

- Unit tests:
  - valid, duplicate, missing target, unknown type, bad relationship, and deterministic hash cases.
- Service/DB tests:
  - temporary datastore manifest load with no production paths.
- GUI/controller tests, if applicable:
  - not applicable
- Integrated route tests:
  - CLI rebuild failure proves validation errors reach the command route.
- Production-data rule:
  - Tests must not require the user's production database, live service, or real Codex skills root.

## Acceptance Criteria

- Valid fixture produces stable normalized ids and hash.
- Invalid fixture reports actionable validation errors.
- No cache metadata is written when validation fails.
- Cycle or recursive relationship mistakes terminate with a clear error.

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
