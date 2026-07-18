# SkillsKeeper Library Checkout Design

## Status

Designed. Not implemented.

This document packages the proposed SkillsKeeper changes for skill library
management, graph-indexed skill trees, project-local checkouts, library update
review, and stricter active-skill surface protection.

## Purpose

SkillsKeeper should grow from a backup-and-mirror tool into a local skill
library manager.

The goal is to keep individual skills portable, organize them through a graph
index, let projects check out relevant skills locally, and preserve the existing
ability to back up project-owned local skills.

The central tension is that `.agents/skills` is both a folder and the active
Codex skill selection surface. SkillsKeeper should keep that surface clean:
skills present there should be intentionally selected, not accidental edits,
dirty library copies, or unresolved experiments.

## Design Goals

- Keep reusable skill source under SkillsKeeper control.
- Let projects check out individual skills, indexes, or profession trees.
- Preserve existing local project-skill backup behavior by default.
- Make fully managed local skill folders opt-in.
- Reduce global Codex skill bloat by making project checkouts the normal path.
- Use an index graph to express overlapping trees and many-parent skills.
- Make library updates proposal-first and agent-reviewed before approval.
- Prevent accidental project-specific changes from becoming reusable library
  doctrine.
- Preserve local work even when it violates a managed-surface rule.

## Non-Goals

- Do not replace Codex's native skill discovery system.
- Do not require a Codex hook for the library-update review path.
- Do not make project checkout copies authoritative library source.
- Do not silently merge local edits back into library skills.
- Do not make fully managed local skills the default for every project.

## Core Concepts

### Library Skill

A canonical reusable skill managed by SkillsKeeper.

Library skills are the source of truth for reusable behavior. They may be
checked out into many projects and referenced by many skill trees.

### Project-Owned Skill

A skill authored by a project for that project's local use.

Default behavior remains today's SkillsKeeper backup/watch model: project-owned
skills in `.agents/skills` are preserved, archived, and backed up, but direct
editing is allowed unless the project opts into fully managed mode.

### Library Checkout

A one-way materialized copy of a library skill into a project.

The checkout is active for Codex selection, but it is not source. Local edits to
a checkout are not allowed. SkillsKeeper should segregate direct local edits and
restore the clean checkout.

### Skill Tree

A traversal result from the index graph, usually rooted at a profession or
context such as `research-scientist`.

A skill tree is not necessarily a separate hand-authored hierarchy. It can be
the result of traversing the index graph from one selected parent downward.

### Index Graph

The primary relationship structure connecting skills, indexes, professions,
phases, and standards.

The index graph may contain overlapping trees. A child skill can have multiple
parents. Top-down traversal produces a checkout tree. Bottom-up traversal shows
which roots, trees, and projects are affected by a skill change.

### Segregated Change

A local change moved out of the active skill selection surface because it
violates a managed rule.

Segregation preserves the user's work, restores or preserves the intended
active skill state, and tells the user how to proceed cleanly.

### Library Update Proposal

A proposed change to an existing library skill.

The proposal is a reviewable artifact. It does not mutate the library until the
user approves it after seeing affected trees and the agent's generic-vs-local
assessment.

## Graph Store Model

Use a two-layer graph model:

```text
JSON manifest = canonical source of truth
Kuzu database = generated query cache
```

Kuzu is a good fit because it is embedded, graph-native, queryable through
Cypher-style queries, and can run from Python without a server. The JSON
manifest remains canonical because it is reviewable, diffable, and suitable for
SkillsKeeper history.

Kuzu should not be the canonical writer. Updates write JSON first. SkillsKeeper
then reloads or rebuilds Kuzu from the manifest.

References:

- [Kuzu documentation](https://kuzudb.github.io/docs/)
- [Kuzu Python API](https://kuzudb.github.io/docs/client-apis/python/)
- [Kuzu JSON import](https://kuzudb.github.io/docs/import/copy-from-json/)

## Canonical JSON Shape

A first implementation can use one file:

```text
skills-library/
  graph/
    skill-graph.json
    skill-graph.schema.json
    index.kuzu/                  # generated
```

Example:

```json
{
  "version": 1,
  "nodes": [
    {
      "id": "research-scientist",
      "kind": "profession",
      "title": "Research Scientist"
    },
    {
      "id": "basic-research",
      "kind": "index",
      "title": "Basic Research"
    },
    {
      "id": "research-data-requirements",
      "kind": "skill",
      "title": "Research Data Requirements",
      "source": "skills/research-data-requirements"
    }
  ],
  "edges": [
    {
      "from": "research-scientist",
      "to": "basic-research",
      "type": "includes",
      "policy": "core"
    },
    {
      "from": "basic-research",
      "to": "research-data-requirements",
      "type": "requires",
      "policy": "core"
    }
  ]
}
```

Later, the manifest may split into `nodes.json`, `edges.json`, `trees.json`,
and generated JSONL/CSV import tables if that improves review and Kuzu import.

## Graph Traversals

### Top-Down Checkout

Starting point: profession, context, index, or skill.

Question answered:

```text
What skills should this project check out for this role/context?
```

Example:

```text
research-scientist
  -> basic-research
  -> evidence-discipline
  -> dataset-workflow
  -> research-data-requirements
```

Output:

- resolved skill ids
- selected edge paths
- policies included or excluded
- conflicts
- optional skills
- versions and source hashes

### Bottom-Up Impact

Starting point: library skill.

Question answered:

```text
Which roots, indexes, trees, and project checkouts are affected by this change?
```

Example:

```text
research-data-requirements
  <- basic-research
  <- research-scientist
  <- product-researcher
  <- market-researcher
```

This traversal is required for library update review.

## Project Checkout Layout

```text
.agents/
  skills/
    research-data-requirements/          # clean active checkout
    evidence-quality-appraisal/          # clean active checkout
  skillskeeper-checkout.lock.json
  skillskeeper-segregated/
    dirty-library-checkouts/
    fully-managed-local/
    proposals/
```

The lockfile records what SkillsKeeper intended to materialize:

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
      "selected_by": [
        "tree:research-scientist"
      ],
      "edge_paths": [
        ["research-scientist", "basic-research", "research-data-requirements"]
      ]
    }
  ]
}
```

## Active Skill Surface Rule

`.agents/skills` is the active Codex skill selection surface.

SkillsKeeper should keep it clean:

- clean library checkouts may be present;
- project-owned skills may be present;
- approved forks may be present;
- unresolved dirty edits should not remain there;
- dirty library checkout edits should not change Codex behavior;
- fully managed local additions/edits/deletions should be segregated until
  accepted through SkillsKeeper.

## Library Checkout Edit Policy

Be draconian.

Library checkout files are not editable in place.

If a user or agent edits a library checkout directly:

1. Detect the hash mismatch.
2. Preserve the changed local copy in a segregation area.
3. Restore the clean library checkout into `.agents/skills`.
4. Notify the user.
5. Require an explicit SkillsKeeper command for the next step.

Notification should include:

- edited library skill id;
- statement that local edits to library checkouts are not allowed;
- path to the segregated copy;
- clean options:
  - localize as a namespaced project-owned skill;
  - split into a new skill;
  - create an overlay if supported;
  - propose a library update;
  - discard the change.

Example:

```text
SkillsKeeper: local edit to library skill "research-data-requirements" was segregated.

Library checkout skills cannot be edited in place because .agents/skills is
the active Codex skill selection surface.

Your changes were preserved at:
.agents/skillskeeper-segregated/dirty-library-checkouts/research-data-requirements/

Use SkillsKeeper to continue:
  skillskeeper checkout localize research-data-requirements --name project-research-data-requirements
  skillskeeper library update research-data-requirements --from-segregated ...
  skillskeeper checkout discard research-data-requirements
```

## Library Update Workflow

Existing library skill updates are two-step.

The update API must not mutate the library skill directly. It records a proposal
and returns `review_required`.

Workflow:

1. User asks the agent to update library skill `x`.
2. Agent uses the SkillsKeeper skill/guidance.
3. Agent calls the SkillsKeeper library update API.
4. API records a proposal and returns `review_required`.
5. API includes affected skill trees, indexes, roots, and checked-out projects.
6. Agent tells the user review is required.
7. Agent shows the proposed skill text or diff.
8. Agent gives feedback on whether the change is appropriately generic or
   project-specific.
9. User approves or rejects.
10. Agent calls the approval API or archives the proposal.

Example API result:

```json
{
  "status": "review_required",
  "proposal_id": "libupd_20260717_001",
  "skill_id": "research-data-requirements",
  "affected_roots": [
    "research-scientist",
    "product-researcher",
    "market-researcher"
  ],
  "affected_projects": [
    "/path/to/project"
  ],
  "proposed_diff_path": ".../proposals/libupd_20260717_001/diff.patch",
  "proposed_skill_path": ".../proposals/libupd_20260717_001/SKILL.md"
}
```

## Agentic Review Requirements

The review interface should be agentic first.

The API owns proposal state, affected-tree calculation, approval, and archival.
The agent owns the user-facing review explanation.

The agent should:

- summarize the proposed change in reusable-skill terms;
- identify project-specific content versus generally reusable content;
- show affected trees from bottom-up traversal;
- show affected project checkouts;
- recommend approve, revise, localize, split, overlay, or reject;
- ask for explicit user approval before applying.

This review is intended to prevent narrow project concerns from becoming global
skill behavior by accident.

## SkillsKeeper Skill Availability

SkillsKeeper `watch` and checkout workflows should always deliver the
SkillsKeeper skill/guidance into active contexts.

Options:

- keep the SkillsKeeper skill global;
- check out the SkillsKeeper skill into participating projects;
- do both.

The SkillsKeeper skill should explicitly say:

- manage skills through SkillsKeeper APIs;
- do not edit generated mirrors;
- do not edit library checkout skills directly;
- use proposal/approval for existing library skill updates;
- use namespaced project-local skills or overlays for project-specific changes.

## Fully Managed Local Skills

The current default for ordinary local-only project skills should remain the
existing backup/watch behavior.

Fully managed local skill folders are opt-in.

In fully managed mode:

- direct edits are disallowed;
- direct additions are disallowed;
- direct deletions are disallowed;
- direct changes are segregated outside `.agents/skills`;
- users must use SkillsKeeper commands to add, update, archive, localize, or
  discard changes.

This mode brings local project skills under the same active-surface discipline
as library checkouts.

## Global Archive Mirror Bug

Separate current issue:

SkillsKeeper global archive behavior does not delete the generated Codex mirror
for the archived global skill.

Desired behavior:

- archive preserves history;
- archiving a global skill removes `~/.codex/skills/keld-<skill>` when present;
- archive output reports whether the generated mirror existed and was removed;
- unrelated generated mirrors remain untouched.

Local active-removal semantics should be handled by the opt-in fully managed
local skills feature. Current backup-only local management should continue to
preserve project-owned local skills rather than actively archiving them.

## Command Sketch

```sh
skillskeeper library graph rebuild
skillskeeper library graph status

skillskeeper checkout skill research-data-requirements --workspace /path/project
skillskeeper checkout tree research-scientist --workspace /path/project
skillskeeper checkout update --workspace /path/project
skillskeeper checkout status --workspace /path/project

skillskeeper checkout localize research-data-requirements --workspace /path/project --name project-research-data-requirements
skillskeeper checkout discard research-data-requirements --workspace /path/project

skillskeeper library update research-data-requirements --from /path/source
skillskeeper library review libupd_20260717_001
skillskeeper library approve libupd_20260717_001
skillskeeper library archive-proposal libupd_20260717_001

skillskeeper manage-local --workspace /path/project --fully-managed
skillskeeper manage-local --workspace /path/project --backup-only
```

## Minimum Viable Implementation

1. Add canonical JSON graph manifest and schema.
2. Add Kuzu rebuild from JSON graph.
3. Add top-down and bottom-up traversal commands.
4. Add project checkout lockfile.
5. Add checkout materialization into `.agents/skills`.
6. Add dirty library checkout detection and segregation.
7. Add API-led library update proposals returning `review_required`.
8. Add agentic review output guidance to the SkillsKeeper skill.
9. Add approval/archive proposal commands.
10. Add global archive mirror-removal fix.
11. Add opt-in fully managed local skills mode.

## Acceptance Criteria

- A project can check out a profession tree into `.agents/skills`.
- The checkout records source ids, hashes, versions, and graph paths.
- A changed library checkout is segregated and the clean checkout remains active.
- A library update cannot be applied without a proposal and explicit approval.
- Review output shows affected trees and project checkouts.
- Existing local project skills still use backup/watch behavior unless fully
  managed mode is enabled.
- Fully managed local mode segregates direct edits/additions/deletions.
- Archived global skills are removed from generated Codex mirrors.

## Open Questions

- Should the graph manifest start as one file or split node/edge files?
- Should Kuzu be rebuilt on every graph command or cached with manifest hash?
- Should tree checkout include optional/recommended edges by default?
- Should checkout updates be automatic, pinned, or policy-driven per project?
- How should overlays be represented if implemented?
- What notification backend should SkillsKeeper use on macOS?
- Should fully managed local direct additions become proposed project skills?
