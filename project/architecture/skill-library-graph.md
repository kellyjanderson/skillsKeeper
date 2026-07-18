# Skill Library Graph Architecture

Target release: 2.0.0
Architecture state: Designed target architecture. Not implemented.

## Overview

The skill library graph records reusable skill relationships as reviewable data.
It lets SkillsKeeper answer two questions:

- top down: what should this project check out for a role, index, or context?
- bottom up: what roots and project checkouts are affected by a skill change?

## Components

### Canonical Graph Manifest

The manifest is the source of truth. It should be JSON for the first
implementation so validation, review, and import remain simple.

Initial layout:

```text
skills-library/
  graph/
    skill-graph.json
    skill-graph.schema.json
    index.kuzu/
```

Node kinds:

- `skill`
- `index`
- `profession`
- `context`
- `phase`
- `standard`

Edge types:

- `includes`
- `requires`
- `recommends`
- `extends`
- `conflicts`
- `replaces`

### Generated Query Cache

The graph query cache is generated from the manifest. Kuzu is the preferred
target if the dependency remains acceptable; a JSON/SQLite traversal layer is
the fallback.

The cache must record:

- manifest path;
- manifest hash;
- schema version;
- generated timestamp.

## Relationships

The graph is not a strict tree. A child skill can have multiple parents, and
multiple profession/context roots can include the same skill through different
paths.

Traversal must therefore preserve edge paths rather than only returning a flat
set of skill ids.

## Data Flow

### Rebuild

1. Load and validate JSON manifest.
2. Normalize nodes and edges.
3. Calculate manifest hash.
4. Rebuild generated cache.
5. Write cache metadata.

### Status

1. Load manifest hash.
2. Load cache metadata.
3. Report fresh, stale, missing, or invalid.

### Top-Down Traversal

1. Start at a skill, index, profession, or context root.
2. Traverse allowed edges.
3. Return resolved skills, selected policies, conflicts, and edge paths.

### Bottom-Up Traversal

1. Start at a reusable library skill.
2. Traverse parent edges.
3. Return affected roots, indexes, trees, and checked-out projects.

## App Integration Contract

App type: console.

User/caller surface:

- `skillskeeper library graph rebuild`
- `skillskeeper library graph status`
- graph traversal APIs consumed by checkout and proposal commands.

Invocation route:

- explicit CLI command;
- implicit freshness check by checkout and proposal commands.

Wiring owner/module:

- new graph module behind thin CLI handlers.

Observable result:

- deterministic traversal output;
- cache status;
- stale-cache error or rebuild.

Integration validation:

- schema validation tests;
- stable traversal output tests;
- stale cache detection tests;
- command smoke tests through CLI parser.

## Specification Sources

- Create graph manifest schema.
- Implement graph validation.
- Implement cache metadata and stale detection.
- Implement top-down traversal.
- Implement bottom-up traversal.
- Add CLI command routing and output format tests.

## Change History

- 2026-07-17: Created graph architecture for 2.0.0p planning release.
