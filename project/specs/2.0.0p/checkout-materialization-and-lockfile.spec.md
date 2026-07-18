# Checkout Materialization And Lockfile Parent Specification

Date: 2026-07-17
Status: Superseded parent. Covered by reviewed child specs.
Primary ancestor: `project/architecture/project-checkouts-and-active-surface.md`
Architecture ancestor: `project/architecture/project-checkouts-and-active-surface.md`
Source artifact: `project/architecture/project-checkouts-and-active-surface.md`
Split provenance: `review specs request 20260717-190429`
Canonical status: `Superseded parent`
Prerequisites:

- `none` - parent is retained only as split coverage evidence.

## Work Units

Unit: Implementation Work Unit (IWU).
Definition: one independently deliverable, reviewable change set with its own verification surface. An IWU is intentionally abstract so the same unit can size software, documentation, tooling, service, research, design, and process projects.
Standard measures: count 1 IWU when the work has one primary outcome, one coherent responsibility boundary, one reviewable artifact or change set, one explicit verification method, declared inputs and outputs, and explicitly named unresolved assumptions or decisions. Split the work when any measure becomes plural, ambiguous, or unnamed.
Count: 5 IWU branch rollup. Not an active implementation leaf.
Basis: lockfile, skill checkout, tree checkout, status, and update each have separate routes or write contracts.

## Review Score

- Prior recorded score: creator draft did not include a numeric total.
- Adversarial rescore basis: parent was re-read as a branch spec; plural routes, models, writes, and verification surfaces require child leaves.
- Total: 95 branch rollup. Do not implement this parent directly.
- Split decision: superseded by child specs below.

## Child Specs

- `project/specs/2.0.0p/checkout-lockfile-schema.spec.md`
- `project/specs/2.0.0p/implemented/checkout-skill-materialization.spec.md`
- `project/specs/2.0.0p/implemented/checkout-tree-materialization.spec.md`
- `project/specs/2.0.0p/checkout-status.spec.md`
- `project/specs/2.0.0p/checkout-update.spec.md`

## Split Coverage

- Parent spec: `none`
- Parent coverage status: 100% covered by reviewed child specs.
- Parent responsibilities owned by children:

| Parent responsibility | Status | Child spec |
|---|---|---|
| Lockfile schema, hashes, and persistence | Covered | `project/specs/2.0.0p/checkout-lockfile-schema.spec.md` |
| Single skill checkout route | Covered | `project/specs/2.0.0p/implemented/checkout-skill-materialization.spec.md` |
| Tree checkout route | Covered | `project/specs/2.0.0p/implemented/checkout-tree-materialization.spec.md` |
| Read-only status route | Covered | `project/specs/2.0.0p/checkout-status.spec.md` |
| Explicit pinned update route | Covered | `project/specs/2.0.0p/checkout-update.spec.md` |

- Parent responsibilities still missing from children:
  - none

## Refinement History

| Request ledger | Latest pass | Active specs reviewed | New leaves created this round | Fixed-point status |
|---|---:|---|---|---|
| `project/spec-refinement-history/2.0.0p-20260717-190429.md` | 1 | `project/specs/2.0.0p/checkout-materialization-and-lockfile.spec.md` | child specs listed above | continue |

## Implementation Guidance

Do not implement this parent directly. Use the child specs as the active leaf
specifications. Keep this file only as split provenance until implementation
and post-implementation architecture reconciliation are complete.
