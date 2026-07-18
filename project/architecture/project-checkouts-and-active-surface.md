# Project Checkouts And Active Surface Architecture

Target release: 2.0.0
Architecture state: Designed target architecture. Not implemented.

## Overview

Project checkout architecture lets SkillsKeeper materialize reusable library
skills into a project's `.agents/skills` folder while preserving the rule that
generated checkouts are not source.

`.agents/skills` is an active Codex selection surface. SkillsKeeper must keep
that surface clean and intentional.

## Ownership Classes

| Class | Source of truth | Active location | Direct edits |
| --- | --- | --- | --- |
| Library skill | Library source store | Generated checkout copy | Segregated |
| Project-owned skill | Project folder | Project `.agents/skills` | Allowed by default |
| Fully managed local skill | SkillsKeeper-managed project state | Project `.agents/skills` | Segregated |
| Global managed skill | Shared Projects skills root | `~/.codex/skills/keld-*` mirror | Source managed through SkillsKeeper |

## Checkout Layout

```text
.agents/
  skills/
    research-data-requirements/
    evidence-quality-appraisal/
  skillskeeper-checkout.lock.json
  skillskeeper-segregated/
    dirty-library-checkouts/
    fully-managed-local/
    proposals/
```

## Checkout Lockfile

The lockfile records intended generated active state:

```json
{
  "version": 1,
  "workspace": "/path/to/project",
  "checkouts": [
    {
      "skill_id": "research-data-requirements",
      "source_version": "1.2.0",
      "source_hash": "sha256:...",
      "materialized_path": ".agents/skills/research-data-requirements",
      "selected_by": ["tree:research-scientist"],
      "edge_paths": [
        ["research-scientist", "basic-research", "research-data-requirements"]
      ]
    }
  ]
}
```

## Reconciliation Rules

- A clean library checkout may remain active.
- A dirty library checkout must be preserved outside `.agents/skills` and
  restored from source.
- A project-owned skill remains editable under backup-only mode.
- A fully managed local skill follows the same segregation discipline as a
  library checkout.
- Direct additions in fully managed mode are preserved as candidate project
  skills, not silently activated.

## Data Flow

### Checkout

1. Resolve graph root or skill id.
2. Copy clean library source into `.agents/skills`.
3. Record hashes and graph paths in lockfile.
4. Report materialized skills.

### Dirty Generated Checkout

1. Detect hash mismatch.
2. Preserve dirty copy under `.agents/skillskeeper-segregated/`.
3. Restore clean source copy.
4. Report recovery commands.

### Fully Managed Local Direct Change

1. Detect add, edit, or deletion.
2. Preserve changed content and metadata.
3. Restore accepted active state or keep absence according to policy.
4. Require explicit command to accept, update, archive, localize, or discard.

## App Integration Contract

App type: console and background service.

User/caller surface:

- `skillskeeper checkout skill <skill-id> --workspace <path>`
- `skillskeeper checkout tree <root-id> --workspace <path>`
- `skillskeeper checkout update --workspace <path>`
- `skillskeeper checkout status --workspace <path>`
- `skillskeeper checkout localize <skill-id> --workspace <path>`
- `skillskeeper checkout discard <skill-id> --workspace <path>`
- `skillskeeper manage-local --workspace <path> --fully-managed`
- `skillskeeper manage-local --workspace <path> --backup-only`

Invocation route:

- explicit CLI command;
- background watcher reconciliation.

Wiring owner/module:

- checkout module;
- active-surface reconciler module;
- CLI command handlers.

Observable result:

- active checkout folders;
- lockfile updates;
- segregation records;
- command output and service logs.

Integration validation:

- temporary workspace checkout smoke;
- dirty checkout segregation smoke;
- fully managed local add/edit/delete smoke;
- backup-only project-owned skill non-enforcement test.

## Specification Sources

- Define checkout lockfile schema.
- Implement checkout materialization.
- Implement checkout status/update.
- Implement dirty checkout detection and segregation.
- Implement fully managed local policy state.
- Implement watcher reconciliation route.

## Change History

- 2026-07-17: Created project checkout and active surface architecture for
  2.0.0p planning release.
