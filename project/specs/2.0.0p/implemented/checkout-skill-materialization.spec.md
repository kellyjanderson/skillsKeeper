# Checkout Skill Materialization Specification

Date: 2026-07-17
Status: Implemented
Primary ancestor: `project/architecture/project-checkouts-and-active-surface.md`
Architecture ancestor: `project/architecture/project-checkouts-and-active-surface.md; project/architecture/acd-2.0-implementation-defaults.md`
Source artifact: `project/architecture/project-checkouts-and-active-surface.md`
Split provenance: `project/specs/2.0.0p/checkout-materialization-and-lockfile.spec.md`
Canonical status: `Implemented canonical leaf`
Prerequisites:

- `project/specs/2.0.0p/checkout-lockfile-schema.spec.md` - materialization records entries in the lockfile
- `project/specs/2.0.0p/graph-traversal-api.spec.md` - skill id resolution uses graph metadata

## Work Units

Unit: Implementation Work Unit (IWU).
Definition: one independently deliverable, reviewable change set with its own verification surface. An IWU is intentionally abstract so the same unit can size software, documentation, tooling, service, research, design, and process projects.
Standard measures: count 1 IWU when the work has one primary outcome, one coherent responsibility boundary, one reviewable artifact or change set, one explicit verification method, declared inputs and outputs, and explicitly named unresolved assumptions or decisions. Split the work when any measure becomes plural, ambiguous, or unnamed.
Count: 1 IWU.
Basis: one CLI route materializes one skill and records one lockfile entry.

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
- Performance-sensitive behavior: 1 x 2 = 2
- Total: 20
- Split decision: score 16-24 retained because this leaf has one user-facing route and one write contract.

## Source Field Carryover

- Source purpose:
  - Materialize one reusable library skill into a project active surface with a recorded generated ownership entry.
- Source responsibilities by category:
  - Functions/methods, data structures, dependencies, outputs, write behavior, privacy, and performance are narrowed in the detailed sections below.
- Source open questions / nuance discovered:
  - No additional architecture gap remains after linked ACD defaults and parent architecture are applied.
- Source split/provenance notes:
  - Split from `project/specs/2.0.0p/checkout-materialization-and-lockfile.spec.md` during review pass 1.

## Purpose

Materialize one reusable library skill into a project active surface with a recorded generated ownership entry.

## Scope

Owns:

- `checkout skill` command behavior
- single-skill materialization
- lockfile entry creation for generated checkout ownership

Does not own:

- tree traversal checkout
- checkout update policy
- dirty generated edit recovery

## Split Coverage

- Parent spec: `project/specs/2.0.0p/checkout-materialization-and-lockfile.spec.md`
- Parent coverage status: covered by reviewed child specs.
- Parent responsibilities owned by this child:
  - single-skill checkout materialization and generated ownership recording.
- Parent responsibilities still missing from children:
  - none

## Refinement History

| Request ledger | Latest pass | Active specs reviewed | New leaves created this round | Fixed-point status |
|---|---:|---|---|---|
| `project/spec-refinement-history/2.0.0p-20260717-190429.md` | 2 | `project/specs/2.0.0p/checkout-skill-materialization.spec.md` | `none` | reached |

## Implementation Routing

- Primary modules/files:
  - `skills_keeper/checkout.py` - single-skill checkout operation
- Supporting modules/files:
  - `skills_keeper/cli.py` - thin command wiring and existing error handling.
- GUI/QML files, if applicable:
  - `not applicable`
- Reusable library/module files:
  - `skills_keeper/checkout.py` - single-skill checkout operation
- Tests:
  - `tests/test_checkout.py` - single-skill checkout CLI tests

## Chosen Defaults / Parameters

- folder name defaults to normalized skill id
- existing dirty target fails before replacement
- command creates `.agents/skills` if missing

## Data Ownership

- Source of truth: library source skill plus checkout lockfile.
- Read ownership: checkout command.
- Write ownership: checkout command writes active copy and lockfile.
- Derived/cache data: active copy derives from library source.
- Privacy/logging constraints: report ids, status, and paths only; do not print full skill bodies.

## Dependencies And Routes

- Domain/service dependencies:
  - `skills_keeper/checkout.py` and related SkillsKeeper helpers.
- Database dependencies:
  - none unless explicitly named as datastore files.
- GUI route, if applicable:
  - not applicable
- Background/concurrency route, if applicable:
  - not applicable; watcher may observe the completed active-folder write after the command returns.

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
  - `project/specs/2.0.0p/checkout-lockfile-schema.spec.md` - materialization records entries in the lockfile
  - `project/specs/2.0.0p/graph-traversal-api.spec.md` - skill id resolution uses graph metadata
- Progression handling:
  - implement after graph traversal and lockfile schema.

## Application Integration

- App type: console.
- User/caller surface: `skillskeeper checkout skill <skill-id> --workspace <path>`.
- Invocation route: explicit CLI command.
- Wiring owner/module: `skills_keeper.checkout`.
- Observable result: one generated active skill folder, one generated lockfile entry, stdout summary, and exit code.
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
  - feature API in `skills_keeper/checkout.py` plus thin CLI wiring when applicable.
- New reusable modules to expose:
  - `skills_keeper/checkout.py` if it does not already exist.
- One-off code justification, if any:
  - none

## Required DTOs / Functions / Components

- DTOs/models:
  - `CheckoutResult` - materialized paths, lockfile updates, warnings
- Functions/methods:
  - `checkout_skill(workspace, skill_id) -> CheckoutResult`
  - `materialize_skill(source, target) -> Path`
  - `record_checkout_entry(lockfile, entry) -> CheckoutLockfile`
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
  - single-skill checkout CLI tests.
- Service/DB tests:
  - temporary datastore/workspace fixtures only.
- GUI/controller tests, if applicable:
  - not applicable
- Integrated route tests:
  - CLI or consumer route smoke asserts observable result and side effects.
- Production-data rule:
  - Tests must not require the user's production database, live service, or real Codex skills root.

## Acceptance Criteria

- One skill checkout creates expected active folder.
- Lockfile records generated ownership and source hash.
- Dirty existing target is not overwritten.
- Invalid source does not leave partial active copy.

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
