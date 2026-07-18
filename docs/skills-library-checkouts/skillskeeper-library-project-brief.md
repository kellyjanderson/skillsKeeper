# SkillsKeeper Library Project Brief

## Status

Implementation planning brief.

This brief packages the skill library, graph index, checkout, proposal-review,
fully managed local skills, and archive-removal work into a project shape that
can be copied into a dedicated SkillsKeeper change project.

## Source Documents

- [skillskeeper-library-checkout-design.md](skillskeeper-library-checkout-design.md)
  is the detailed design.
- [discussion-notes/2026-07-17-skill-library-checkouts.md](discussion-notes/2026-07-17-skill-library-checkouts.md)
  preserves the working discussion and rationale.
- [skill-tree-routing-concept.md](skill-tree-routing-concept.md)
  captures the earlier prompt-time routing idea that led to the library design.

## Objective

Extend SkillsKeeper so reusable skills can live in a managed library, be linked
through a graph index, and be checked out into projects as clean one-way active
skill copies.

The change should preserve today's project-local skill backup behavior by
default, while adding opt-in fully managed local skill folders for projects that
want strict control of `.agents/skills`.

## Product Position

The first practical version is a library expansion of SkillsKeeper, not a Codex
prompt-routing hook.

Skill trees become a convenience layer over a graph index:

- individual skills remain portable;
- professions and contexts select groups of skills;
- overlapping trees are allowed;
- one child may have many parents;
- top-down traversal answers checkout questions;
- bottom-up traversal answers impact-review questions.

## Canonical Data Model

Use a text manifest as source of truth:

```text
JSON manifest = canonical, reviewable, versioned state
Kuzu database = generated graph query cache
```

All updates write the JSON manifest first. Kuzu is rebuilt or refreshed from
the manifest and should not be treated as authoritative source.

## Core Workstreams

### 1. Graph Manifest And Kuzu Cache

Build the canonical graph model.

Initial deliverables:

- `skill-graph.json`
- `skill-graph.schema.json`
- generated `index.kuzu/`
- graph rebuild command
- graph status command
- deterministic top-down traversal
- deterministic bottom-up traversal

### 2. Library Checkout Engine

Materialize managed library skills into project `.agents/skills`.

Initial deliverables:

- individual skill checkout
- tree checkout
- checkout update
- checkout status
- checkout lockfile with skill ids, versions, hashes, and graph paths
- detection of direct edits to library checkout files
- segregation of dirty library checkout copies outside active skill selection
- restoration of clean active checkout copies

### 3. Library Update Proposal Flow

Make existing library skill updates two-step.

Initial deliverables:

- update API creates a proposal instead of mutating source;
- API returns `review_required`;
- response includes affected roots, indexes, trees, and checked-out projects;
- proposal includes proposed skill text or diff;
- approval API applies the proposal;
- archive API closes rejected proposals.

The agent-facing review should show the affected trees and give feedback on
whether the proposed change is generic enough for the library or should become
a project-local skill, split skill, or overlay.

### 4. Active Skill Surface Protection

Treat `.agents/skills` as an active Codex selection surface.

Library checkout edits are not allowed in place. If a user or agent edits a
library checkout directly, SkillsKeeper should preserve the changed copy in a
segregation area, restore the clean checkout, and notify the user how to
continue cleanly.

### 5. SkillsKeeper Guidance Delivery

Ensure projects using SkillsKeeper always receive the SkillsKeeper operating
guidance.

Acceptable delivery options:

- keep the SkillsKeeper skill global;
- check out the SkillsKeeper skill into participating projects;
- do both.

The guidance must explicitly state that library checkout skills should not be
edited directly.

### 6. Fully Managed Local Skills

Add an opt-in mode for fully managed local project skill folders.

Default local-only project skills keep today's backup/watch behavior. Fully
managed mode is enabled by a flag or project setting.

In fully managed mode, direct edits, additions, and deletions are segregated
outside `.agents/skills` until accepted through SkillsKeeper.

### 7. Global Archive Mirror-Removal Fix

Fix the existing global archive behavior so archiving a global skill removes
its generated `~/.codex/skills/keld-*` mirror while preserving archive history.
Fully managed local archive behavior is a related future ownership rule, not
the confirmed current bug.

## Suggested First Milestone

Build the graph substrate without mutating any project skill folders.

Completion target:

- sample JSON graph exists;
- schema validation passes;
- Kuzu cache rebuilds from JSON;
- top-down traversal from a profession returns resolved skill ids;
- bottom-up traversal from a skill returns affected roots;
- graph commands are deterministic and testable.

This creates the index foundation before checkout writes touch active skill
surfaces.

## Suggested CLI Surface

```sh
skillskeeper library graph rebuild
skillskeeper library graph status

skillskeeper checkout skill <skill-id> --workspace <path>
skillskeeper checkout tree <root-id> --workspace <path>
skillskeeper checkout update --workspace <path>
skillskeeper checkout status --workspace <path>

skillskeeper checkout localize <skill-id> --workspace <path> --name <new-skill-id>
skillskeeper checkout discard <skill-id> --workspace <path>

skillskeeper library update <skill-id> --from <path>
skillskeeper library review <proposal-id>
skillskeeper library approve <proposal-id>
skillskeeper library archive-proposal <proposal-id>

skillskeeper manage-local --workspace <path> --fully-managed
skillskeeper manage-local --workspace <path> --backup-only
```

## Acceptance Gates

- Project tree checkout creates active skills only from resolved graph skills.
- Checkout lockfile records source ids, versions, hashes, and graph paths.
- Direct edits to library checkout files are segregated and do not alter active
  Codex behavior.
- Existing library skill updates require proposal review and explicit approval.
- Review output lists affected trees before approval.
- Agent review flags project-specific changes before they enter the library.
- Default project-local skills continue to use backup/watch behavior.
- Fully managed local mode segregates direct edits, additions, and deletions.
- Archived global skills disappear from generated Codex mirrors.

## Open Decisions

- Whether the initial graph manifest is one JSON file or split node/edge files.
- Whether Kuzu rebuilds on every command or only when the manifest hash changes.
- How checkout policies handle optional and recommended skills.
- Whether project checkouts are auto-updated, pinned, or policy-driven.
- Whether overlays are supported in the first implementation.
- What notification channel is used for segregated changes.
- Whether fully managed local additions become project-skill proposals by
  default.
