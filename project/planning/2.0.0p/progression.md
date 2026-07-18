# SkillsKeeper 2.0.0 Implementation Progression

Status: Active work progression
Working branch: `work`
Source planning release: `project/releases/2.0.0p.md`

## Source Documents

- Architecture:
  - `project/architecture/skillskeeper-2.0-architecture-overview.md`
  - `project/architecture/skill-library-graph.md`
  - `project/architecture/project-checkouts-and-active-surface.md`
  - `project/architecture/library-update-proposals.md`
- ACDs:
  - `project/architecture/acd-global-archive-mirror-removal.md`
  - `project/architecture/acd-active-surface-ownership-transition.md`
  - `project/architecture/acd-2.0-implementation-defaults.md`
- Final specs:
  - `project/specs/2.0.0p/README.md`
- Test specs:
  - `project/specs/2.0.0p/tests/`

## Completion Rule

Progression checkboxes are truth markers. Check helper implementation only when
helper behavior is implemented. Check route wiring only when the intended
user/caller route calls the behavior. Check route validation only when proof
through the real route has passed. Check status updates only after the
implementation and validation state is honestly reflected in durable project
artifacts.

When implementation discovers a prerequisite gap, leave the current item
unchecked and add an indented status note:

```md
  - Status: Missing prerequisite - <ACD/spec/progression item path>.
```

Do not mark the current item blocked when the next action is to define or
implement a prerequisite. If the prerequisite spec already exists but is not
implemented, pause the current item, ensure the prerequisite appears before it
in this progression, implement the prerequisite first, then return to the
paused item.

## Lane: Release Safety Baseline

### Global Archive Mirror Removal

Spec: `project/specs/2.0.0p/implemented/global-archive-mirror-removal.spec.md`
Test spec: `project/specs/2.0.0p/tests/implemented/global-archive-mirror-removal.test-spec.md`
Prerequisites: none
App type: console
User/caller surface: `skillskeeper archive <workspace> <source-kind> <identity>`

- [x] Implement helper/service behavior for global archive mirror removal.
- [x] Wire behavior into the archive console route.
- [x] Validate integrated archive route through temporary datastore and Codex mirror fixtures.
- [x] Update docs/progression/status after route validation.

## Lane: Graph Foundation

### Graph Manifest Schema Validation

Spec: `project/specs/2.0.0p/graph-manifest-schema-validation.spec.md`
Test spec: `project/specs/2.0.0p/tests/graph-manifest-schema-validation.test-spec.md`
Prerequisites: `project/architecture/acd-2.0-implementation-defaults.md`
App type: library-only with console error exposure
User/caller surface: graph validation consumed by `skillskeeper library graph rebuild` and `status`

- [ ] Implement helper/service behavior for graph manifest schema validation.
- [ ] Wire validation into the graph rebuild/status console consumers.
- [ ] Validate integrated graph validation route through module tests and CLI rebuild failure smoke.
- [ ] Update docs/progression/status after route validation.

### Graph Traversal API

Spec: `project/specs/2.0.0p/graph-traversal-api.spec.md`
Test spec: `project/specs/2.0.0p/tests/graph-traversal-api.test-spec.md`
Prerequisites: `project/specs/2.0.0p/graph-manifest-schema-validation.spec.md`
App type: library-only
User/caller surface: graph traversal APIs consumed by checkout and proposal modules

- [ ] Implement helper/service behavior for graph traversal APIs.
- [ ] Wire traversal into checkout and proposal consumer modules.
- [ ] Validate traversal through graph unit tests and consuming checkout/proposal route tests.
- [ ] Update docs/progression/status after route validation.

### Graph Cache CLI

Spec: `project/specs/2.0.0p/graph-cache-cli.spec.md`
Test spec: `project/specs/2.0.0p/tests/graph-cache-cli.test-spec.md`
Prerequisites: `project/specs/2.0.0p/graph-manifest-schema-validation.spec.md`
App type: console
User/caller surface: `skillskeeper library graph rebuild`; `skillskeeper library graph status`

- [ ] Implement helper/service behavior for graph cache rebuild/status.
- [ ] Wire behavior into the `library graph rebuild` and `library graph status` console routes.
- [ ] Validate integrated graph cache routes through temporary datastore fixtures.
- [ ] Update docs/progression/status after route validation.

## Lane: Checkout Foundation

### Checkout Lockfile Schema

Spec: `project/specs/2.0.0p/checkout-lockfile-schema.spec.md`
Test spec: `project/specs/2.0.0p/tests/checkout-lockfile-schema.test-spec.md`
Prerequisites: `project/specs/2.0.0p/graph-manifest-schema-validation.spec.md`
App type: library-only with console consumption
User/caller surface: lockfile consumed by `checkout status`, `checkout update`, `sync`, and `watch`

- [ ] Implement helper/service behavior for checkout lockfile schema.
- [ ] Wire lockfile helpers into checkout and reconciliation consumer modules.
- [ ] Validate lockfile round-trip through route-level temporary fixture tests.
- [ ] Update docs/progression/status after route validation.

### Checkout Skill Materialization

Spec: `project/specs/2.0.0p/checkout-skill-materialization.spec.md`
Test spec: `project/specs/2.0.0p/tests/checkout-skill-materialization.test-spec.md`
Prerequisites: `project/specs/2.0.0p/checkout-lockfile-schema.spec.md`; `project/specs/2.0.0p/graph-traversal-api.spec.md`
App type: console
User/caller surface: `skillskeeper checkout skill <skill-id> --workspace <path>`

- [ ] Implement helper/service behavior for single-skill checkout materialization.
- [ ] Wire behavior into the `checkout skill` console route.
- [ ] Validate integrated checkout skill route through temporary datastore/workspace fixtures.
- [ ] Update docs/progression/status after route validation.

### Checkout Tree Materialization

Spec: `project/specs/2.0.0p/checkout-tree-materialization.spec.md`
Test spec: `project/specs/2.0.0p/tests/checkout-tree-materialization.test-spec.md`
Prerequisites: `project/specs/2.0.0p/checkout-lockfile-schema.spec.md`; `project/specs/2.0.0p/graph-traversal-api.spec.md`
App type: console
User/caller surface: `skillskeeper checkout tree <root-id> --workspace <path>`

- [ ] Implement helper/service behavior for tree checkout materialization.
- [ ] Wire behavior into the `checkout tree` console route.
- [ ] Validate integrated checkout tree route through temporary datastore/workspace fixtures.
- [ ] Update docs/progression/status after route validation.

### Checkout Status

Spec: `project/specs/2.0.0p/checkout-status.spec.md`
Test spec: `project/specs/2.0.0p/tests/checkout-status.test-spec.md`
Prerequisites: `project/specs/2.0.0p/checkout-lockfile-schema.spec.md`
App type: console
User/caller surface: `skillskeeper checkout status --workspace <path>`

- [ ] Implement helper/service behavior for checkout status classification.
- [ ] Wire behavior into the `checkout status` console route.
- [ ] Validate integrated checkout status route with clean, dirty, missing, and stale fixtures.
- [ ] Update docs/progression/status after route validation.

### Checkout Update

Spec: `project/specs/2.0.0p/checkout-update.spec.md`
Test spec: `project/specs/2.0.0p/tests/checkout-update.test-spec.md`
Prerequisites: `project/specs/2.0.0p/checkout-lockfile-schema.spec.md`; `project/specs/2.0.0p/checkout-status.spec.md`
App type: console
User/caller surface: `skillskeeper checkout update --workspace <path>`

- [ ] Implement helper/service behavior for explicit checkout update.
- [ ] Wire behavior into the `checkout update` console route.
- [ ] Validate integrated checkout update route with updated, skipped, and failed entry fixtures.
- [ ] Update docs/progression/status after route validation.

## Lane: Library Update Proposals

### Proposal Artifact Create

Spec: `project/specs/2.0.0p/proposal-artifact-create.spec.md`
Test spec: `project/specs/2.0.0p/tests/proposal-artifact-create.test-spec.md`
Prerequisites: `project/specs/2.0.0p/graph-manifest-schema-validation.spec.md`
App type: console
User/caller surface: `skillskeeper library update <skill-id> --from <path>`

- [ ] Implement helper/service behavior for proposal artifact creation.
- [ ] Wire behavior into the `library update` console route.
- [ ] Validate integrated proposal creation route through temporary datastore/library fixtures.
- [ ] Update docs/progression/status after route validation.

### Proposal Review Impact

Spec: `project/specs/2.0.0p/proposal-review-impact.spec.md`
Test spec: `project/specs/2.0.0p/tests/proposal-review-impact.test-spec.md`
Prerequisites: `project/specs/2.0.0p/proposal-artifact-create.spec.md`; `project/specs/2.0.0p/graph-traversal-api.spec.md`; `project/specs/2.0.0p/checkout-lockfile-schema.spec.md`
App type: console
User/caller surface: `skillskeeper library review <proposal-id>`

- [ ] Implement helper/service behavior for proposal review and impact reporting.
- [ ] Wire behavior into the `library review` console route.
- [ ] Validate integrated review route with graph and checkout impact fixtures.
- [ ] Update docs/progression/status after route validation.

### Proposal Approve

Spec: `project/specs/2.0.0p/proposal-approve.spec.md`
Test spec: `project/specs/2.0.0p/tests/proposal-approve.test-spec.md`
Prerequisites: `project/specs/2.0.0p/proposal-artifact-create.spec.md`
App type: console
User/caller surface: `skillskeeper library approve <proposal-id>`

- [ ] Implement helper/service behavior for proposal approval.
- [ ] Wire behavior into the `library approve` console route.
- [ ] Validate integrated approval route through proposal, validation, and source mutation fixtures.
- [ ] Update docs/progression/status after route validation.

### Proposal Archive

Spec: `project/specs/2.0.0p/proposal-archive.spec.md`
Test spec: `project/specs/2.0.0p/tests/proposal-archive.test-spec.md`
Prerequisites: `project/specs/2.0.0p/proposal-artifact-create.spec.md`
App type: console
User/caller surface: `skillskeeper library archive-proposal <proposal-id>`

- [ ] Implement helper/service behavior for proposal archival.
- [ ] Wire behavior into the `library archive-proposal` console route.
- [ ] Validate integrated archive-proposal route through proposal artifact fixtures.
- [ ] Update docs/progression/status after route validation.

## Lane: Active Surface Ownership

### Active Surface Ownership Policy

Spec: `project/specs/2.0.0p/active-surface-ownership-policy.spec.md`
Test spec: `project/specs/2.0.0p/tests/active-surface-ownership-policy.test-spec.md`
Prerequisites: `project/specs/2.0.0p/checkout-lockfile-schema.spec.md`
App type: console and library-only
User/caller surface: `skillskeeper manage-local --workspace <path> --fully-managed|--backup-only` and classifier consumers

- [ ] Implement helper/service behavior for active-surface ownership policy.
- [ ] Wire behavior into the `manage-local` console route and classifier consumers.
- [ ] Validate integrated policy route and classifier consumers through temporary workspace fixtures.
- [ ] Update docs/progression/status after route validation.

### Active Surface Dirty Checkout Segregation

Spec: `project/specs/2.0.0p/active-surface-dirty-checkout-segregation.spec.md`
Test spec: `project/specs/2.0.0p/tests/active-surface-dirty-checkout-segregation.test-spec.md`
Prerequisites: `project/specs/2.0.0p/active-surface-ownership-policy.spec.md`; `project/specs/2.0.0p/checkout-skill-materialization.spec.md`
App type: library-only with mixed route consumer
User/caller surface: reconciler consumed by `sync` and `watch`

- [ ] Implement helper/service behavior for dirty generated checkout segregation.
- [ ] Wire segregation into the sync/watch reconciliation consumers.
- [ ] Validate integrated reconciliation route with dirty generated checkout fixtures.
- [ ] Update docs/progression/status after route validation.

### Active Surface Fully Managed Local

Spec: `project/specs/2.0.0p/active-surface-fully-managed-local.spec.md`
Test spec: `project/specs/2.0.0p/tests/active-surface-fully-managed-local.test-spec.md`
Prerequisites: `project/specs/2.0.0p/active-surface-ownership-policy.spec.md`
App type: library-only with mixed route consumer
User/caller surface: reconciler consumed by `sync` and `watch` for fully managed workspaces

- [ ] Implement helper/service behavior for fully managed local reconciliation.
- [ ] Wire fully managed reconciliation into the sync/watch consumers.
- [ ] Validate integrated reconciliation route with add/edit/delete fixtures.
- [ ] Update docs/progression/status after route validation.

### Active Surface Sync Watch Route

Spec: `project/specs/2.0.0p/active-surface-sync-watch-route.spec.md`
Test spec: `project/specs/2.0.0p/tests/active-surface-sync-watch-route.test-spec.md`
Prerequisites: `project/specs/2.0.0p/active-surface-dirty-checkout-segregation.spec.md`; `project/specs/2.0.0p/active-surface-fully-managed-local.spec.md`
App type: mixed console and background service
User/caller surface: `skillskeeper sync`; `skillskeeper watch`

- [ ] Implement helper/service behavior for sync/watch active-surface reconciliation.
- [ ] Wire behavior into the `sync` command and watcher trigger.
- [ ] Validate integrated sync and watcher-style reconciliation routes.
- [ ] Update docs/progression/status after route validation.

## Lane: Segregated Checkout Recovery

### Checkout Segregated Localize

Spec: `project/specs/2.0.0p/checkout-segregated-localize.spec.md`
Test spec: `project/specs/2.0.0p/tests/checkout-segregated-localize.test-spec.md`
Prerequisites: `project/specs/2.0.0p/active-surface-dirty-checkout-segregation.spec.md`; `project/specs/2.0.0p/checkout-lockfile-schema.spec.md`
App type: console
User/caller surface: `skillskeeper checkout localize <skill-id> --workspace <path>`

- [ ] Implement helper/service behavior for segregated checkout localize.
- [ ] Wire behavior into the `checkout localize` console route.
- [ ] Validate integrated localize route through temporary workspace, lockfile, and segregation fixtures.
- [ ] Update docs/progression/status after route validation.

### Checkout Segregated Discard

Spec: `project/specs/2.0.0p/checkout-segregated-discard.spec.md`
Test spec: `project/specs/2.0.0p/tests/checkout-segregated-discard.test-spec.md`
Prerequisites: `project/specs/2.0.0p/active-surface-dirty-checkout-segregation.spec.md`
App type: console
User/caller surface: `skillskeeper checkout discard <skill-id> --workspace <path>`

- [ ] Implement helper/service behavior for segregated checkout discard.
- [ ] Wire behavior into the `checkout discard` console route.
- [ ] Validate integrated discard route through temporary workspace and segregation fixtures.
- [ ] Update docs/progression/status after route validation.

### Proposal From Segregated Edit

Spec: `project/specs/2.0.0p/proposal-from-segregated-edit.spec.md`
Test spec: `project/specs/2.0.0p/tests/proposal-from-segregated-edit.test-spec.md`
Prerequisites: `project/specs/2.0.0p/active-surface-dirty-checkout-segregation.spec.md`; `project/specs/2.0.0p/proposal-artifact-create.spec.md`; `project/specs/2.0.0p/proposal-review-impact.spec.md`
App type: console
User/caller surface: `skillskeeper checkout propose-update <skill-id> --workspace <path>`

- [ ] Implement helper/service behavior for proposal creation from segregated edits.
- [ ] Wire behavior into the `checkout propose-update` console route.
- [ ] Validate integrated propose-update route through segregation, proposal, graph, and checkout fixtures.
- [ ] Update docs/progression/status after route validation.

## Specification Canonicalization

- [x] Split parent or umbrella specs into child specs.
- [x] Verify 100% parent responsibility coverage.
- [x] Move uncovered responsibilities into children and re-verify.
- [x] Mark children canonical after coverage reaches 100%.
- [x] Archive superseded parent specs.
- [x] Update indexes and progression links to canonical children.
- [ ] Remove completed process scaffolding from active architecture documents after 2.0.0 implementation conformance.
