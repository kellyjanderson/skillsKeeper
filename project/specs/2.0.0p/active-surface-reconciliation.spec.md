# Active Surface Reconciliation Parent Specification

Date: 2026-07-17
Status: Superseded parent. Covered by reviewed child specs.
Primary ancestor: `project/architecture/acd-active-surface-ownership-transition.md`
Architecture ancestor: `project/architecture/acd-active-surface-ownership-transition.md`
Source artifact: `project/architecture/acd-active-surface-ownership-transition.md`
Split provenance: `review specs request 20260717-190429`
Canonical status: `Superseded parent`
Prerequisites:

- `none` - parent is retained only as split coverage evidence.

## Work Units

Unit: Implementation Work Unit (IWU).
Definition: one independently deliverable, reviewable change set with its own verification surface. An IWU is intentionally abstract so the same unit can size software, documentation, tooling, service, research, design, and process projects.
Standard measures: count 1 IWU when the work has one primary outcome, one coherent responsibility boundary, one reviewable artifact or change set, one explicit verification method, declared inputs and outputs, and explicitly named unresolved assumptions or decisions. Split the work when any measure becomes plural, ambiguous, or unnamed.
Count: 7 IWU branch rollup. Not an active implementation leaf.
Basis: ownership policy, dirty checkout segregation, fully managed local reconciliation, sync/watch integration, and explicit dirty-checkout recovery routes can fail independently.

## Review Score

- Prior recorded score: creator draft did not include a numeric total.
- Adversarial rescore basis: parent was re-read as a branch spec; plural routes, models, writes, and verification surfaces require child leaves.
- Total: 147 branch rollup. Do not implement this parent directly.
- Split decision: superseded by child specs below.

## Child Specs

- `project/specs/2.0.0p/active-surface-ownership-policy.spec.md`
- `project/specs/2.0.0p/active-surface-dirty-checkout-segregation.spec.md`
- `project/specs/2.0.0p/active-surface-fully-managed-local.spec.md`
- `project/specs/2.0.0p/active-surface-sync-watch-route.spec.md`
- `project/specs/2.0.0p/checkout-segregated-localize.spec.md`
- `project/specs/2.0.0p/checkout-segregated-discard.spec.md`
- `project/specs/2.0.0p/proposal-from-segregated-edit.spec.md`

## Split Coverage

- Parent spec: `none`
- Parent coverage status: 100% covered by reviewed child specs.
- Parent responsibilities owned by children:

| Parent responsibility | Status | Child spec |
|---|---|---|
| Ownership classification and manage-local policy | Covered | `project/specs/2.0.0p/active-surface-ownership-policy.spec.md` |
| Dirty generated checkout preservation and restoration | Covered | `project/specs/2.0.0p/active-surface-dirty-checkout-segregation.spec.md` |
| Fully managed local add/edit/delete reconciliation | Covered | `project/specs/2.0.0p/active-surface-fully-managed-local.spec.md` |
| Sync and watcher route integration with idempotence | Covered | `project/specs/2.0.0p/active-surface-sync-watch-route.spec.md` |
| Localize preserved generated checkout edits as project-owned local skills | Covered | `project/specs/2.0.0p/checkout-segregated-localize.spec.md` |
| Discard preserved generated checkout edits without mutating source | Covered | `project/specs/2.0.0p/checkout-segregated-discard.spec.md` |
| Propose reusable library updates from segregated edits | Covered | `project/specs/2.0.0p/proposal-from-segregated-edit.spec.md` |

- Parent responsibilities still missing from children:
  - none

## Refinement History

| Request ledger | Latest pass | Active specs reviewed | New leaves created this round | Fixed-point status |
|---|---:|---|---|---|
| `project/spec-refinement-history/2.0.0p-20260717-190429.md` | 1 | `project/specs/2.0.0p/active-surface-reconciliation.spec.md` | child specs listed above | continue |

## Implementation Guidance

Do not implement this parent directly. Use the child specs as the active leaf
specifications. Keep this file only as split provenance until implementation
and post-implementation architecture reconciliation are complete.
