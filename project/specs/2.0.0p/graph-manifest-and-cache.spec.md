# Graph Manifest And Cache Parent Specification

Date: 2026-07-17
Status: Superseded parent. Covered by reviewed child specs.
Primary ancestor: `project/architecture/skill-library-graph.md`
Architecture ancestor: `project/architecture/skill-library-graph.md`
Source artifact: `project/architecture/skill-library-graph.md`
Split provenance: `review specs request 20260717-190429`
Canonical status: `Superseded parent`
Prerequisites:

- `none` - parent is retained only as split coverage evidence.

## Work Units

Unit: Implementation Work Unit (IWU).
Definition: one independently deliverable, reviewable change set with its own verification surface. An IWU is intentionally abstract so the same unit can size software, documentation, tooling, service, research, design, and process projects.
Standard measures: count 1 IWU when the work has one primary outcome, one coherent responsibility boundary, one reviewable artifact or change set, one explicit verification method, declared inputs and outputs, and explicitly named unresolved assumptions or decisions. Split the work when any measure becomes plural, ambiguous, or unnamed.
Count: 3 IWU branch rollup. Not an active implementation leaf.
Basis: schema validation, traversal, and cache CLI are independently deliverable contracts.

## Review Score

- Prior recorded score: creator draft did not include a numeric total.
- Adversarial rescore basis: parent was re-read as a branch spec; plural routes, models, writes, and verification surfaces require child leaves.
- Total: 49 branch rollup. Do not implement this parent directly.
- Split decision: superseded by child specs below.

## Child Specs

- `project/specs/2.0.0p/implemented/graph-manifest-schema-validation.spec.md`
- `project/specs/2.0.0p/graph-traversal-api.spec.md`
- `project/specs/2.0.0p/implemented/graph-cache-cli.spec.md`

## Split Coverage

- Parent spec: `none`
- Parent coverage status: 100% covered by reviewed child specs.
- Parent responsibilities owned by children:

| Parent responsibility | Status | Child spec |
|---|---|---|
| Manifest schema, validation, normalization, and hash output | Covered | `project/specs/2.0.0p/implemented/graph-manifest-schema-validation.spec.md` |
| Top-down and bottom-up traversal API | Covered | `project/specs/2.0.0p/graph-traversal-api.spec.md` |
| Cache metadata, rebuild command, and status command | Covered | `project/specs/2.0.0p/implemented/graph-cache-cli.spec.md` |

- Parent responsibilities still missing from children:
  - none

## Refinement History

| Request ledger | Latest pass | Active specs reviewed | New leaves created this round | Fixed-point status |
|---|---:|---|---|---|
| `project/spec-refinement-history/2.0.0p-20260717-190429.md` | 1 | `project/specs/2.0.0p/graph-manifest-and-cache.spec.md` | child specs listed above | continue |

## Implementation Guidance

Do not implement this parent directly. Use the child specs as the active leaf
specifications. Keep this file only as split provenance until implementation
and post-implementation architecture reconciliation are complete.
