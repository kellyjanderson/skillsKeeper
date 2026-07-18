# ACD: 2.0 Implementation Defaults

Date: 2026-07-17
Status: Drafting Specs
Canonical architecture targets:

- `project/architecture/skillskeeper-2.0-architecture-overview.md`
- `project/architecture/skill-library-graph.md`
- `project/architecture/project-checkouts-and-active-surface.md`
- `project/architecture/library-update-proposals.md`

Related:

- Release / plan / issue: `project/releases/2.0.0p.md`
- Parent ACD, if any: `none`

## Change Intent

Resolve planning-time defaults that were still open when implementation specs
began, without editing canonical architecture after the architecture phase.

## Current Architecture

The 2.0.0p architecture defines graph-indexed library checkout, active-surface
ownership, proposal-first library updates, and archive mirror removal. Several
implementation defaults remain open: graph cache dependency, checkout update
policy, overlay scope, and storage placement.

## Target Architecture

- JSON files are the canonical graph source for 2.0.0.
- Kuzu is an optional generated query cache, not a required runtime dependency.
- The first implementation ships deterministic in-process traversal and may add
  Kuzu behind the same cache boundary later.
- Checkouts default to pinned source hashes and update only through explicit
  `checkout update`.
- Overlays are out of scope for 2.0.0; dirty edits may be localized, proposed,
  discarded, or restored from segregation.
- Library, graph, proposal, checkout, and segregation state live under the
  existing SkillsKeeper datastore unless a command explicitly targets a
  temporary workspace fixture.

## Non-Goals

- Do not make Kuzu mandatory in 2.0.0.
- Do not implement automatic checkout updates as the default policy.
- Do not implement overlay composition in 2.0.0.
- Do not move the live 1.0.0 service runtime or production datastore.

## Canonical Document Impact

- Architecture docs to update on closure:
  - `project/architecture/skill-library-graph.md` - record the conformed cache fallback policy.
  - `project/architecture/project-checkouts-and-active-surface.md` - record pinned checkout defaults and overlay deferral.
  - `project/architecture/library-update-proposals.md` - record datastore placement for proposal artifacts.
- Specs or plans affected:
  - `project/specs/2.0.0p/*.spec.md` - use these defaults as draft prerequisites.

## Readiness Blocker Resolution

- Blocker being resolved:
  - open architecture questions in the 2.0.0p architecture source set.
- Source artifact:
  - `project/architecture/skillskeeper-2.0-architecture-overview.md`
  - `project/architecture/skills-library-management-architecture.md`
- Resolution provided by this ACD:
  - implementation defaults for cache, update policy, overlays, and storage.
- Follow-on artifact:
  - draft implementation specs under `project/specs/2.0.0p/`.
- Resolution status:
  - resolved for draft spec creation; must be reviewed independently.

## Compatibility And Migration Strategy

- All implementation work must remain compatible with the installed 1.0.0
  runtime separation.
- Tests must use temporary datastores and temporary workspaces.
- New state files must be additive and must not require migration of the live
  1.0.0 state file before the 2.0.0 implementation explicitly defines that
  migration.

## Application Integration Contract

- App type: console and background service
- User/caller surface: `skillskeeper library graph`, `skillskeeper checkout`,
  `skillskeeper library update/review/approve/archive-proposal`, `watch`, and
  `sync`.
- Invocation route: explicit CLI commands and background watcher reconciliation.
- Wiring owner/module: `skills_keeper.cli` command handlers plus extracted
  graph, checkout, proposal, and active-surface modules.
- Observable result: deterministic command output, datastore artifacts,
  checkout lockfiles, proposal records, segregation records, and preserved live
  service isolation.
- Integration validation: CLI smoke tests and temporary workspace watcher-style
  reconciliation tests.

## Specification Sources

- Use JSON graph source and in-process traversal for first graph/cache specs.
- Use explicit pinned checkout updates as the default checkout policy.
- Defer overlays from 2.0.0 implementation specs.
- Store graph, proposal, checkout, and segregation records under the datastore.
- Keep tests isolated from live 1.0.0 runtime and production datastore paths.

## Specification Conformance

- Parent specs created or affected:
  - `none`
- Canonical child specs:
  - `project/specs/2.0.0p/implemented/graph-manifest-schema-validation.spec.md` - graph source defaults.
  - `project/specs/2.0.0p/graph-traversal-api.spec.md` - graph traversal defaults.
  - `project/specs/2.0.0p/implemented/graph-cache-cli.spec.md` - generated cache defaults.
  - `project/specs/2.0.0p/checkout-lockfile-schema.spec.md` - lockfile defaults.
  - `project/specs/2.0.0p/checkout-skill-materialization.spec.md` - pinned checkout defaults.
  - `project/specs/2.0.0p/checkout-tree-materialization.spec.md` - pinned tree checkout defaults.
  - `project/specs/2.0.0p/checkout-status.spec.md` - read-only status defaults.
  - `project/specs/2.0.0p/checkout-update.spec.md` - explicit update defaults.
  - `project/specs/2.0.0p/checkout-segregated-localize.spec.md` - overlay deferral and generated-to-local recovery defaults.
  - `project/specs/2.0.0p/checkout-segregated-discard.spec.md` - overlay deferral and explicit discard recovery defaults.
  - `project/specs/2.0.0p/active-surface-ownership-policy.spec.md` - backup-only and fully managed policy defaults.
  - `project/specs/2.0.0p/active-surface-dirty-checkout-segregation.spec.md` - overlay deferral and segregation defaults.
  - `project/specs/2.0.0p/active-surface-fully-managed-local.spec.md` - fully managed local defaults.
  - `project/specs/2.0.0p/active-surface-sync-watch-route.spec.md` - route integration defaults.
  - `project/specs/2.0.0p/proposal-artifact-create.spec.md` - datastore proposal defaults.
  - `project/specs/2.0.0p/proposal-from-segregated-edit.spec.md` - proposal creation from segregated checkout defaults.
  - `project/specs/2.0.0p/proposal-review-impact.spec.md` - impact review defaults.
  - `project/specs/2.0.0p/proposal-approve.spec.md` - proposal approval defaults.
  - `project/specs/2.0.0p/proposal-archive.spec.md` - proposal archival defaults.
  - `project/specs/2.0.0p/implemented/global-archive-mirror-removal.spec.md` - mirror removal defaults.
- Paired test specs:
  - `project/specs/2.0.0p/tests/*.test-spec.md` - one paired active test spec per reviewed feature leaf.

## Conformance Checklist

- [ ] Implementation conforms to the target architecture.
- [ ] Parent specs are 100% represented by canonical child specs.
- [ ] Superseded parent specs are archived.
- [ ] Canonical child specs point to architecture or active ACD as primary ancestor.
- [ ] Paired test specs point to canonical child specs.
- [ ] Progression and indexes point to canonical child specs.
- [ ] Completed process scaffolding is removed from active canonical architecture docs.
- [ ] Canonical architecture docs describe the conformed architecture.

## Closure Criteria

- 2.0.0 implementation either conforms to these defaults or replaces them with
  a reviewed ACD.
- Canonical architecture is reconciled after implementation.
- Active specs no longer need this ACD as live authority.

## Closure Notes

- Canonical architecture updated:
  - `pending`
- Archived or removed scaffolding:
  - `pending`
- Follow-up ACDs:
  - `none`

## Change History

- 2026-07-17 - Initial draft. Reason: resolve open implementation defaults
  discovered during `do specs`.
