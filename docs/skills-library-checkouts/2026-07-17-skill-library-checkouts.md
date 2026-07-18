# Discussion Notes: Skill Library Checkouts

Date: 2026-07-17

## Context

- The skill-tree work is now isolated under `skill-tree-work/`.
- The current direction shifts from prompt-time routing first to a SkillsKeeper
  library expansion first.
- The user wants a well-organized skill library with cross-referencing indexes,
  portable individual skills, and profession-oriented skill trees.
- Example profession context: `research scientist`.

## Leaning

- Treat skill trees as convenience bundles over a cross-indexed skill library,
  not as the only storage or discovery model.
- Treat indexes as relationship graphs rather than flat catalogs. An index can
  express overlapping trees where each child skill may have multiple parents.
- Individual skills should remain portable across many consumers and contexts:
  writing, coding, applied science, research science, market work, product work,
  and other professions.
- A project should be able to check out one skill, an index, or a profession
  tree into its local `.agents/skills` folder.
- Project checkouts should be one-way materialized copies from the SkillsKeeper
  managed library into the project.
- Project-local edits to checked-out skills should not silently become source
  edits. Source updates should go through a controlled SkillsKeeper add/update
  path.
- SkillsKeeper should be draconian about changed library checkouts. Editing a
  library checkout in place is not allowed. If it happens, SkillsKeeper should
  segregate the changed copy so the work is not lost, restore or preserve the
  clean active checkout, and notify the user with the recovery path and the
  sanctioned ways to proceed.
- SkillsKeeper should automatically segregate changed library checkouts in a way
  that preserves intended Codex skill selection. The active `.agents/skills`
  folder should remain a clean selection surface, not a mixture of clean library
  checkouts, dirty library edits, forks, and unresolved local experiments.
- Updates to managed library skills should propagate into project checkouts.
- This model should reduce the number of global Codex skills because many skills
  become project checkouts rather than global mirrors.
- SkillsKeeper `watch` and checkout workflows should always deliver the
  SkillsKeeper skill/guidance into the active context. That can happen by making
  the SkillsKeeper skill global, by checking it out into participating projects,
  or both.
- The SkillsKeeper skill should explicitly tell agents and users that library
  checkout skills must not be edited directly in project `.agents/skills`.
- Changes to existing library skills should be two-step: first create a proposed
  change, then require direct user approval before the library skill changes.
- The approval interface should list every skill tree/index/root affected by the
  proposed library update, because a narrowly motivated project change may alter
  multiple related skill trees.
- The approval interface should likely be agentic first: the agent should guide
  the user through the proposed change, affected trees, project-specific risk,
  and safer alternatives before asking for explicit approval. Static CLI reports
  can remain the audit substrate, but should not be the whole experience.

## Index As Tree Graph

- The index may be the primary linking mechanism for skill trees.
- As a visualization, an index is a set of overlapping trees rather than one
  strict hierarchy.
- A parent-to-child traversal starts from a selected profession/context root,
  walks downward, and produces a single materialized skill tree for checkout.
- A child-to-parent traversal starts from a single reusable skill and walks
  upward, showing all profession/context roots and intermediate indexes that
  depend on it.
- This means a child skill can belong to multiple professions without copying or
  re-authoring the skill.
- Example: `research-data-requirements` could sit under `research-scientist`,
  `product-researcher`, `market-researcher`, `applied-scientist`, and perhaps
  `technical-writer` through different parent paths.

## Design Implications

- SkillsKeeper needs to distinguish project-owned skills from library checkout
  skills inside `.agents/skills`.
- Current watched-workspace behavior treats project skill folders as source
  material to preserve. Checkout folders need different metadata so SkillsKeeper
  knows they are generated/materialized consumers.
- Skill trees need a real linking mechanism. The index graph may own that
  mechanism by referencing skills, parent links, versions, constraints, and edge
  semantics rather than relying on prose.
- A lockfile or checkout manifest is likely needed so a project records exactly
  which skills/tree/index versions were materialized.
- Traversal direction matters:
  - top-down traversal answers "what skills should this profession/context
    check out?"
  - bottom-up traversal answers "which trees depend on this skill and what will
    break or improve if it changes?"
- The graph datastore should probably have a reviewable JSON source of truth
  plus a generated query store. A binary graph database alone would make index
  review, merges, and SkillsKeeper history harder to inspect.
- Candidate implementation direction:
  - canonical source: JSON graph manifests in the SkillsKeeper datastore;
  - generated query store: embedded graph database for traversal, impact
    analysis, and visualization;
  - checkout lockfile: records resolved skills, edge path, versions, and hashes
    materialized into a project.
- Kuzu looks like a promising embedded graph query layer because it is local,
  Python-usable, and graph-native without requiring a server. SQLite adjacency
  tables with recursive CTEs remain the lowest-dependency fallback.
- Kuzu should be treated as a generated query cache, not the canonical writer.
  Updates should write the JSON manifest first, then reload or rebuild the Kuzu
  store from the manifest. Kuzu can persist its own imported graph tables, but
  it will not automatically stay linked to the JSON manifest unless SkillsKeeper
  implements that reload/checksum behavior.
- Prefer JSON over YAML for the first implementation. JSON simplifies the stack:
  SkillsKeeper can validate the same canonical document it imports, avoid
  YAML-specific parser behavior, and pass normalized JSON or derived JSONL/CSV
  directly into Kuzu.
- For the first implementation, prefer a manifest hash in Kuzu metadata:
  commands check whether the Kuzu index matches the current manifest hash and
  rebuild before traversal when stale.
- Dirty checked-out library skills should be moved or copied into a segregation
  area outside `.agents/skills`, such as `.agents/skillskeeper-segregated/`.
  SkillsKeeper can then restore the clean library checkout into `.agents/skills`
  so Codex continues to select the intended canonical skill.
- The notification should be explicit and user-actionable:
  - name the edited library skill;
  - say local edits to library checkouts are not allowed;
  - point to the segregated copy;
  - explain the clean paths: create a namespaced project-local skill, create an
    overlay if supported, or use SkillsKeeper to update/propose an update to the
    library skill.
- The segregation area should preserve enough metadata to support later choices:
  integrate upstream, split into a new skill, localize as a project-owned skill,
  convert to an overlay, or discard/restore.
- Possible segregation layout:
  ```text
  .agents/
    skills/
      research-data-requirements/          # clean active library checkout
    skillskeeper-checkout.lock.json
    skillskeeper-segregated/
      dirty-library-checkouts/
        research-data-requirements/
          SKILL.md                         # changed local copy
          skillskeeper-segregation.json
      overlays/
      forks/
  ```
- This keeps Codex behavior predictable: only finalized checkout/fork/overlay
  decisions should affect active skill discovery.
- The first implementation can skip clever merge behavior. The safe behavior is:
  detect edit, segregate, notify, restore clean checkout, and require an
  explicit command for any sanctioned conversion or library update.
- Library update proposals should include:
  - the target library skill;
  - the proposed diff;
  - the source of the proposal, such as a segregated local edit or explicit
    library-edit command;
  - bottom-up graph traversal showing affected professions, indexes, and skill
    trees;
  - any checked-out projects that would receive the update;
  - suggested alternatives when the change appears project-specific, such as a
    namespaced project-local skill or overlay.
- Approval should be an explicit second action, not implied by generating the
  proposal. This is a deliberate brake against mixing project-specific concerns
  into reusable library skills.
- Agentic approval flow should ask the reviewing agent to:
  - summarize the change in reusable-skill terms;
  - identify which parts are project-specific versus generally reusable;
  - show affected trees and project checkouts from bottom-up graph traversal;
  - recommend approve, revise, localize, split, overlay, or reject;
  - require the user to explicitly choose before applying the library update.
- A Codex hook is not required for the library-update review feature if the API
  itself refuses direct mutation and returns `review_required`. Hooks may remain
  useful later as bypass protection, but the feature should be designed around
  SkillsKeeper's API as the guard.
- The core proposal workflow should be API-led and agent-presented:
  1. User asks the agent to update library skill `x`.
  2. The agent uses the SkillsKeeper skill guidance, which directs it to use the
     SkillsKeeper API rather than editing files by hand.
  3. The agent calls the library skill update API.
  4. The API records a proposed update and returns `review_required`, including
     affected skill trees/index roots that include the skill.
  5. The agent replies that the update was submitted and requires review.
  6. The agent prints or summarizes the affected trees, the proposed skill text
     or diff, and its own assessment of whether the change is appropriately
     generic or appears project-specific.
  7. If the user approves, the agent calls the approval API.
  8. If the user does not approve, the proposal is archived rather than applied.
- In this model, the agentic review is the user-facing review surface; the API
  owns proposal state, affected-tree calculation, approval, and archival.

## Separate SkillsKeeper Follow-Ups

- Global archive mirror bug: when a global skill is archived, SkillsKeeper
  should delete its generated `~/.codex/skills/keld-*` mirror. That mirror
  removal is the concrete current issue; preserved history should remain
  recoverable.
- Fully managed local skills folder feature: the current default for ordinary
  local-only project skills should remain the existing backup/watch behavior.
  A project should be able to opt into a fully managed local `.agents/skills`
  folder using an explicit parameter/flag.
- In fully managed mode, direct edits, additions, and deletions are disallowed.
- Fully managed local folder enforcement should use the segregation process:
  any direct edit/add/delete is moved out of the active selection surface,
  preserved in a SkillsKeeper-managed segregation area, and surfaced to the user
  with instructions to use SkillsKeeper commands to add, update, archive,
  localize, or discard the change.
- This mode would make project skill management consistent with library
  checkout management: `.agents/skills` remains an intentional active Codex
  selection surface, not an uncontrolled editing area.

## Open Questions

- What is the canonical source location for the library: the existing
  SkillsKeeper datastore, a new `skills-library/` root, or both?
- Should tree checkout materialize every skill directly under `.agents/skills`,
  or preserve a hidden manifest plus symlinks?
- Should updates be automatic, opt-in, or controlled by pinned versions?
- How should local project customizations be represented: overlay directives,
  forks, or update proposals back to the library?
- What identifiers should links use: skill name, namespace/name, content hash,
  semantic version, or a combination?
- What edge types should the index support: requires, recommends, extends,
  conflicts, replaces, optional, profession-core, phase, or evidence-standard?
- Should the JSON manifest be one combined graph file, separate `nodes.json` and
  `edges.json` files, or JSONL files optimized for Kuzu import?
- Should the first prototype use SQLite recursive traversal for zero dependency,
  then add Kuzu once the graph schema stabilizes, or start with Kuzu immediately
  to force graph-native modeling?
- Should dirty checkout segregation happen immediately on `sync`, continuously
  in `watch`, or only when a checkout/update command runs?
- Should SkillsKeeper restore the clean library checkout automatically after
  segregating a dirty local edit, or should it leave the skill absent from
  `.agents/skills` until the user chooses?
- What notification backend should SkillsKeeper use on macOS: LaunchAgent log
  plus notification center, terminal warning on next command, or both?
- Should SkillsKeeper enforce the two-step proposal/approval flow for all
  library updates, or only for updates to skills that have more than one parent
  or checked-out consumer?
- What is the minimum viable agentic approval surface: a generated review note,
  an interactive `skillskeeper library review <proposal>` command, a Codex task
  template, or a plugin/app UI later?
- For fully managed local skills folders, should direct additions be segregated
  as proposed project skills, while direct edits to known managed skills are
  segregated as proposed updates?
