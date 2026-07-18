# SkillsKeeper 2.0.0p Architecture Overview

Target release: 2.0.0
Architecture state: Designed target architecture. Not implemented.

## Overview

SkillsKeeper 2.0.0 moves the product from a backup-and-mirror utility toward a
local skill library manager. The new architecture keeps reusable skill source
under SkillsKeeper control, lets projects check out clean active copies, and
adds review gates before project-specific edits can become reusable library
behavior.

The architectural center is an ownership-aware active skill model:

```text
Reusable library source -> project checkout copy -> active Codex selection
Project-owned local source -> backup snapshot -> optional fully managed mode
Global managed source -> generated Codex mirror
```

## Relationship To Existing Architecture

This document supersedes the broad planning note in
`project/architecture/skills-library-management-architecture.md` for the
2.0.0p planning release. The older document remains useful as source context.

Changes to existing behavior are routed through ACDs:

- `project/architecture/acd-global-archive-mirror-removal.md`
- `project/architecture/acd-active-surface-ownership-transition.md`

## Components

| Component | Responsibility |
| --- | --- |
| Library source store | Canonical reusable skill directories and metadata |
| Graph manifest | Reviewable skill/index/profession relationship source |
| Graph query cache | Generated traversal cache for checkout and impact review |
| Checkout engine | Materializes clean library skills into projects |
| Checkout lockfile | Records intended project checkout state |
| Active surface reconciler | Keeps generated active surfaces consistent with ownership |
| Segregation store | Preserves invalid or dirty active-surface changes |
| Proposal store | Records and reviews library update proposals |
| Global mirror manager | Mirrors global managed skills into Codex and prunes generated mirrors |

## Core Data Flows

### Library Checkout

1. User requests a skill, index, or tree checkout.
2. SkillsKeeper validates graph source and cache freshness.
3. Checkout engine resolves skill ids and graph paths.
4. SkillsKeeper writes clean active copies to project `.agents/skills`.
5. SkillsKeeper records source hashes and selected paths in the checkout
   lockfile.

### Dirty Active Surface Reconciliation

1. SkillsKeeper compares lockfile state to active `.agents/skills` contents.
2. Dirty generated checkouts are preserved in a segregation store.
3. Clean generated checkout copies are restored.
4. User receives next actions: discard, localize, split, overlay, or propose a
   library update.

### Library Update Proposal

1. A reusable skill update request creates a proposal, not a direct mutation.
2. Bottom-up graph traversal identifies affected roots and project checkouts.
3. Review output distinguishes reusable changes from project-specific changes.
4. User approval applies the proposal; rejection archives it.

## App Integration Contract

App type: console and background service.

User/caller surface:

- `skillskeeper library graph ...`
- `skillskeeper checkout ...`
- `skillskeeper library update/review/approve/archive-proposal ...`
- `skillskeeper manage-local ...`
- existing `skillskeeper sync`, `watch`, `codex-sync`, and `archive` routes
  where ownership-aware reconciliation applies.

Invocation route:

- direct CLI commands;
- background `watch` reconciliation;
- manual `sync` reconciliation.

Wiring owner/module:

- CLI command handlers should remain thin.
- New graph, checkout, proposal, and active-surface behavior should be extracted
  into focused modules before implementation grows materially.

Observable result:

- graph traversal output;
- checkout lockfiles;
- active skill copies;
- segregation records;
- proposal records;
- pruned generated Codex mirrors for archived global skills.

Integration validation:

- unit tests for each module boundary;
- temporary workspace smoke tests for checkout, dirty reconciliation, proposal
  review, and archive mirror pruning;
- service smoke tests only when live service mutation is intentionally in scope.

## Specification Sources

- Define module boundaries for graph, checkout, proposal, active-surface, and
  global mirror management.
- Define CLI command contracts for graph, checkout, proposal, and managed-local
  routes.
- Define lockfile, segregation metadata, proposal metadata, and graph manifest
  schemas.
- Define migration/conformance behavior for existing global archive semantics.
- Define validation route for background watcher reconciliation.

## Open Questions

- Should Kuzu be required for 2.0.0, or should graph traversal start with a
  zero-dependency JSON/SQLite implementation?
- Should checkouts default to pinned or auto-updated versions?
- Should overlays be first-class in 2.0.0 or remain a future conversion path?
- Should library data live inside the existing datastore or under a separate
  library root?

## Change History

- 2026-07-17: Created 2.0.0p architecture overview and routed existing behavior
  changes through ACDs.
