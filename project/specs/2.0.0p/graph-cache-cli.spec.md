# Graph Cache CLI Specification

Date: 2026-07-17
Status: Reviewed Draft
Primary ancestor: `project/architecture/skill-library-graph.md`
Architecture ancestor: `project/architecture/skill-library-graph.md; project/architecture/acd-2.0-implementation-defaults.md`
Source artifact: `project/architecture/skill-library-graph.md`
Split provenance: `project/specs/2.0.0p/graph-manifest-and-cache.spec.md`
Canonical status: `Canonical draft leaf`
Prerequisites:

- `project/specs/2.0.0p/graph-manifest-schema-validation.spec.md` - cache rebuild validates manifest before writing

## Work Units

Unit: Implementation Work Unit (IWU).
Definition: one independently deliverable, reviewable change set with its own verification surface. An IWU is intentionally abstract so the same unit can size software, documentation, tooling, service, research, design, and process projects.
Standard measures: count 1 IWU when the work has one primary outcome, one coherent responsibility boundary, one reviewable artifact or change set, one explicit verification method, declared inputs and outputs, and explicitly named unresolved assumptions or decisions. Split the work when any measure becomes plural, ambiguous, or unnamed.
Count: 1 IWU.
Basis: one CLI-backed cache metadata lifecycle for rebuild and status.

## Review Score

- Prior recorded score: none for this split child.
- Adversarial rescore basis: recounted from this leaf after splitting parent responsibilities; checked for hidden coupling, unrecorded routes, missing readiness fields, destructive writes, privacy-sensitive paths, and prerequisite order.
- Functions/methods: 2 x 2 = 4
- Data structures/models: 1 x 1 = 1
- Dependencies/services: 1 x 1 = 1
- Returns/outputs/signals: 1 x 1 = 1
- Existing reusable code reused as-is: 0 x 0.5 = 0
- Adding code to an existing library/module: 1 x 1 = 1
- Creating a new reusable library/module: 0 x 3 = 0
- Async/concurrency behavior: 0 x 3 = 0
- Destructive/write behavior: 1 x 3 = 3
- Security/privacy-sensitive behavior: 0 x 3 = 0
- Performance-sensitive behavior: 1 x 2 = 2
- Total: 13
- Split decision: below forced split threshold and one cache-status command group.

## Source Field Carryover

- Source purpose:
  - Expose graph cache rebuild and status commands that write and report generated cache metadata.
- Source responsibilities by category:
  - Functions/methods: rebuild cache, read cache metadata, compare manifest hash, report status.
  - Data structures/models: cache metadata and status result.
  - Dependencies/services: validated manifest and manifest hash.
  - Returns/outputs/signals: stdout status, exit code, cache metadata file.
  - Destructive/write behavior: writes generated cache metadata.
- Source open questions / nuance discovered:
  - Cache is generated metadata first; Kuzu can later live behind the same boundary.
- Source split/provenance notes:
  - Split from `project/specs/2.0.0p/graph-manifest-and-cache.spec.md` during review pass 1.

## Purpose

Expose graph cache rebuild and status commands that write and report generated cache metadata.

## Scope

Owns:

- cache metadata schema
- fresh/stale/missing/invalid status calculation
- `library graph rebuild` and `library graph status` command behavior

Does not own:

- canonical manifest validation rules beyond calling validation
- traversal API behavior
- Kuzu dependency installation

## Split Coverage

- Parent spec: `project/specs/2.0.0p/graph-manifest-and-cache.spec.md`
- Parent coverage status: covered by reviewed child specs.
- Parent responsibilities owned by this child:
  - cache metadata, stale detection, rebuild command, and status command responsibilities.
- Parent responsibilities still missing from children:
  - none

## Refinement History

| Request ledger | Latest pass | Active specs reviewed | New leaves created this round | Fixed-point status |
|---|---:|---|---|---|
| `project/spec-refinement-history/2.0.0p-20260717-190429.md` | 2 | `project/specs/2.0.0p/graph-cache-cli.spec.md` | `none` | reached |

## Implementation Routing

- Primary modules/files:
  - `skills_keeper/graph.py` - cache metadata and status helpers
  - `skills_keeper/cli.py` - graph subcommand parser and output
- Supporting modules/files:
  - `skills_keeper/cli.py` - thin command wiring and existing error handling.
- GUI/QML files, if applicable:
  - `not applicable`
- Reusable library/module files:
  - `skills_keeper/graph.py` - cache metadata and status helpers
  - `skills_keeper/cli.py` - graph subcommand parser and output
- Tests:
  - `tests/test_graph.py` - cache and CLI command tests

## Chosen Defaults / Parameters

- cache metadata path under datastore graph cache directory
- freshness uses manifest hash and schema version
- status reports stale without mutating files
- rebuild writes only after validation succeeds

## Data Ownership

- Source of truth: manifest JSON and generated cache metadata.
- Read ownership: graph cache helpers and CLI handlers.
- Write ownership: graph rebuild command.
- Derived/cache data: cache metadata derives from manifest hash and schema version.
- Privacy/logging constraints: report ids, status, and paths only; do not print full skill bodies.

## Dependencies And Routes

- Domain/service dependencies:
  - `skills_keeper.graph`, `skills_keeper.cli`.
- Database dependencies:
  - none unless explicitly named as datastore files.
- GUI route, if applicable:
  - not applicable
- Background/concurrency route, if applicable:
  - not applicable for first implementation.

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
  - `project/specs/2.0.0p/graph-manifest-schema-validation.spec.md` - cache rebuild validates manifest before writing
- Progression handling:
  - implement after manifest validation.

## Application Integration

- App type: console.
- User/caller surface: `skillskeeper library graph rebuild`; `skillskeeper library graph status`.
- Invocation route: explicit CLI command.
- Wiring owner/module: `skills_keeper.cli`.
- Observable result: stdout status, exit code, cache metadata file.
- Integration validation: CLI smoke tests with temporary datastore fixtures.
- Incomplete status risk: helper-only implementation without this route proof is incomplete.

App-type-specific proof:

- GUI: not applicable.
- Console: command, args, stdout/stderr, exit code, and file side effects where the leaf has a CLI route.
- API-service: not applicable.
- Mixed: separate proof for console and watcher-style route when named.
- Library-only: consuming module proof is required when there is no direct CLI route.

## Reuse And Extraction Plan

- Existing code to reuse:
  - `datastore_path` and `KeeperError` from current CLI.
- Current reuse readiness:
  - reuse as-is initially.
- Extraction/wrapping needed:
  - optional path helper extraction.
- Additions to existing library/modules:
  - graph subcommands in CLI parser.
- New reusable modules to expose:
  - none beyond `skills_keeper.graph`.
- One-off code justification, if any:
  - none

## Required DTOs / Functions / Components

- DTOs/models:
  - `CacheMetadata` - manifest path, hash, schema version, generated timestamp
  - `CacheStatus` - fresh, stale, missing, invalid
- Functions/methods:
  - `write_cache_metadata(datastore, manifest) -> CacheMetadata`
  - `read_cache_metadata(datastore) -> CacheMetadata | None`
  - `graph_cache_status(datastore) -> CacheStatus`
  - `command_library_graph(args) -> int`
- UI fields / visible data, if applicable:
  - not applicable
- UI elements / controls, if applicable:
  - not applicable
- UI components, if applicable:
  - not applicable

## Performance Contract

- Status reads manifest metadata and cache metadata without scanning skill folders.

## Error And State Behavior

- Invalid manifest prevents cache writes; missing cache is reported clearly.

## Test Strategy

- Unit tests:
  - fresh, stale, missing, invalid metadata cases.
- Service/DB tests:
  - temp datastore cache metadata writes.
- GUI/controller tests, if applicable:
  - not applicable
- Integrated route tests:
  - CLI rebuild/status asserts output and exit codes.
- Production-data rule:
  - Tests must not require the user's production database, live service, or real Codex skills root.

## Acceptance Criteria

- Rebuild writes cache metadata after validation.
- Status reports fresh when hash matches.
- Status reports stale when manifest changes.
- Invalid manifest leaves previous cache untouched.

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
