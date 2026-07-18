# Library Update Proposal Architecture

Target release: 2.0.0
Architecture state: Designed target architecture. Not implemented.

## Overview

Reusable library skill updates are proposal-first. SkillsKeeper must not mutate
an existing library skill directly when an update could affect multiple trees,
indexes, or projects.

The API owns proposal state and impact calculation. The agent or CLI review
surface owns explanation and user approval.

## Components

### Proposal Store

Stores:

- proposal id;
- target skill id;
- source of proposed change;
- proposed full skill content;
- proposed diff;
- affected roots and indexes;
- affected project checkouts;
- review status;
- timestamps.

### Impact Calculator

Uses bottom-up graph traversal plus checkout lockfiles to identify affected
roots and projects.

### Approval Applier

Applies exactly the approved proposal to reusable library source, then schedules
or performs checkout update reconciliation.

## Proposal States

- `review_required`
- `approved`
- `applied`
- `archived`
- `superseded`

## Data Flow

1. User or agent requests update to an existing library skill.
2. SkillsKeeper validates proposed skill content.
3. SkillsKeeper writes proposal artifacts.
4. Bottom-up traversal identifies affected graph roots.
5. Checkout lockfile scan identifies affected projects.
6. Command returns `review_required`.
7. Review output summarizes diff, impact, and project-specific risk.
8. Explicit approval applies the proposal.
9. Rejection archives the proposal without mutating source.

## App Integration Contract

App type: console and agent-assisted workflow.

User/caller surface:

- `skillskeeper library update <skill-id> --from <path>`
- `skillskeeper library review <proposal-id>`
- `skillskeeper library approve <proposal-id>`
- `skillskeeper library archive-proposal <proposal-id>`

Invocation route:

- explicit CLI command used directly by a user or by an agent following
  SkillsKeeper guidance.

Wiring owner/module:

- proposal module;
- graph impact module;
- checkout lockfile scanner;
- CLI command handlers.

Observable result:

- proposal artifact path;
- `review_required` status;
- affected roots and projects;
- approved source update or archived proposal.

Integration validation:

- proposal creation does not mutate source;
- approval applies exactly the proposed content;
- archive-proposal preserves proposal and leaves source unchanged;
- bottom-up impact appears in command output.

## Specification Sources

- Define proposal artifact schema and storage path.
- Implement update command as proposal creation.
- Implement review command.
- Implement approval command.
- Implement archive-proposal command.
- Integrate bottom-up graph traversal and checkout lockfile impact.

## Change History

- 2026-07-17: Created library update proposal architecture for 2.0.0p planning
  release.
