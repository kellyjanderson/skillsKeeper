# Checkout Segregated Localize And Discard Parent Specification

Date: 2026-07-17
Status: Superseded parent. Covered by reviewed child specs.
Primary ancestor: `project/architecture/project-checkouts-and-active-surface.md`
Architecture ancestor: `project/architecture/project-checkouts-and-active-surface.md`; `project/architecture/acd-active-surface-ownership-transition.md`; `project/architecture/acd-2.0-implementation-defaults.md`
Source artifact: `project/architecture/project-checkouts-and-active-surface.md`
Split provenance: `architecture coverage review 20260717-194042`
Canonical status: `Superseded parent`
Prerequisites:

- `none` - parent is retained only as split coverage evidence.

## Work Units

Unit: Implementation Work Unit (IWU).
Definition: one independently deliverable, reviewable change set with its own verification surface. An IWU is intentionally abstract so the same unit can size software, documentation, tooling, service, research, design, and process projects.
Standard measures: count 1 IWU when the work has one primary outcome, one coherent responsibility boundary, one reviewable artifact or change set, one explicit verification method, declared inputs and outputs, and explicitly named unresolved assumptions or decisions. Split the work when any measure becomes plural, ambiguous, or unnamed.
Count: 2 IWU branch rollup. Not an active implementation leaf.
Basis: localize and discard have distinct write behavior and recovery semantics.

## Review Score

- Prior recorded score: none for this review-created coverage parent.
- Adversarial rescore basis: recounted from architecture and ACD source; checked for missing `checkout localize` and `checkout discard` routes, destructive writes, lockfile mutation, and recovery output.
- Total: 27.5 branch rollup. Do not implement this parent directly.
- Split decision: split required because score is 25 or higher.

## Child Specs

- `project/specs/2.0.0p/checkout-segregated-localize.spec.md`
- `project/specs/2.0.0p/checkout-segregated-discard.spec.md`

## Split Coverage

- Parent spec: `none`
- Parent coverage status: 100% covered by reviewed child specs.
- Parent responsibilities owned by children:

| Parent responsibility | Status | Child spec |
|---|---|---|
| Localize preserved generated checkout edit as project-owned source | Covered | `project/specs/2.0.0p/checkout-segregated-localize.spec.md` |
| Discard preserved generated checkout edit without mutating source | Covered | `project/specs/2.0.0p/checkout-segregated-discard.spec.md` |

- Parent responsibilities still missing from children:
  - none

## Refinement History

| Request ledger | Latest pass | Active specs reviewed | New leaves created this round | Fixed-point status |
|---|---:|---|---|---|
| `project/spec-refinement-history/2.0.0p-architecture-crosscheck-20260717-194042.md` | 1 | `project/specs/2.0.0p/*` against `project/architecture/*` | child specs listed above | continue |

## Implementation Guidance

Do not implement this parent directly. Use the child specs for localize and
discard implementation.
