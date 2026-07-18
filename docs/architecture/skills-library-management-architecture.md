# SkillsKeeper Skill Library Management Architecture

Status: Designed target architecture. Not implemented.

## Overview

SkillsKeeper will grow from a backup, archive, and mirror utility into a local
skill library manager. The target architecture keeps reusable library skills
under SkillsKeeper control, lets projects check out selected skills into their
active `.agents/skills` surface, and preserves project-owned skill work without
silently promoting local edits into reusable library doctrine.

The central invariant is:

```text
.agents/skills is an active Codex selection surface, not an uncontrolled working tree.
```

SkillsKeeper must therefore distinguish between project-owned skills, generated
library checkouts, global managed skills, and fully managed local skills before
deciding whether to back up, restore, segregate, archive, or mirror a change.

## Source Documents

- `docs/skills-library-checkouts/skillskeeper-library-checkout-design.md`
- `docs/skills-library-checkouts/skillskeeper-library-project-brief.md`
- `docs/skills-library-checkouts/2026-07-17-skill-library-checkouts.md`
- `docs/release-management-action-plan.md`

## Current Reality

Current SkillsKeeper behavior is backup-oriented:

- watched workspace skills are copied into a private git-backed datastore;
- shared Projects skills can be mirrored into `~/.codex/skills/keld-*`;
- `disable` reconciles some active surfaces by moving disabled workspace skills
  and pruning matching Codex mirrors;
- `archive` moves a current datastore copy into an archive path, but the
  current issue is that global skill archive does not delete the generated
  `~/.codex/skills/keld-*` mirror for the archived skill;
- the 1.0.0 installer runs the live service from a non-editable service runtime
  package so development checkout edits require an explicit release/install step
  before becoming live.

## Target Components

### Library Source Store

Owns canonical reusable skill source.

Responsibilities:

- store reusable skill directories;
- store canonical graph manifests;
- store proposal artifacts;
- retain history through the SkillsKeeper datastore;
- expose source hashes and versions for checkout lockfiles.

The library source store is authoritative for reusable skills. Project checkout
copies are never authoritative library source.

### Canonical Graph Manifest

Owns skill relationships.

Responsibilities:

- represent skills, indexes, professions, contexts, phases, and standards as
  graph nodes;
- represent relationships such as `includes`, `requires`, `recommends`,
  `extends`, `conflicts`, and `replaces`;
- remain reviewable, diffable, and versioned;
- validate against a JSON schema.

Initial shape:

```text
skills-library/
  graph/
    skill-graph.json
    skill-graph.schema.json
    index.kuzu/
```

The JSON graph manifest is canonical. Kuzu is a generated query cache.

### Graph Query Cache

Owns fast traversal, not source truth.

Responsibilities:

- rebuild from the canonical JSON manifest;
- record the manifest hash it was built from;
- answer top-down checkout traversal;
- answer bottom-up impact traversal;
- be disposable and rebuildable.

Commands must detect stale cache state before traversal. If the cache manifest
hash does not match the canonical manifest, SkillsKeeper should rebuild or
refuse traversal with a clear status depending on command mode.

### Checkout Engine

Owns project materialization of library skills.

Responsibilities:

- resolve skill, index, context, and profession checkout requests through the
  graph;
- copy clean library skills into project `.agents/skills`;
- write a checkout lockfile;
- update existing checkouts according to pinning/update policy;
- detect dirty library checkout copies;
- restore clean active checkouts after segregation.

Checkout copies are one-way consumers. Direct edits to checkout files are never
merged back into the library by ordinary sync.

### Checkout Lockfile

Owns intended active checkout state for one project.

Location:

```text
.agents/skillskeeper-checkout.lock.json
```

Responsibilities:

- record workspace path;
- record checked-out skill ids;
- record source versions and hashes;
- record materialized paths;
- record selected roots and graph paths;
- support status, update, dirty-check, and impact review.

### Segregation Store

Owns preservation of unmanaged or invalid active-surface changes.

Location:

```text
.agents/skillskeeper-segregated/
```

Responsibilities:

- preserve direct edits to library checkouts;
- preserve direct edits, additions, and deletions in fully managed local mode;
- record why the change was segregated;
- record the original active path and source metadata;
- support later localize, propose update, split, overlay, discard, or restore
  actions.

Segregation protects user work while keeping `.agents/skills` predictable.

### Library Proposal Store

Owns proposed reusable-skill updates.

Responsibilities:

- record proposed diffs and proposed full skill text;
- record proposal source, such as explicit update request or segregated edit;
- run bottom-up graph impact traversal;
- list affected roots, indexes, skill trees, and checked-out projects;
- require explicit approval before changing library source;
- archive rejected proposals without applying them.

The API owns proposal state. Agents own the user-facing review explanation.

### Active Surface Reconciler

Owns enforcement across active delivery locations.

Responsibilities:

- keep `.agents/skills` consistent with checkout lockfiles and fully managed
  local policy;
- keep `~/.codex/skills/keld-*` consistent with global managed source;
- delete generated Codex mirrors when managed global skills are archived;
- avoid mutating backup-only project-owned skills.

This component resolves the confirmed archive issue by making generated Codex
mirror deletion part of managed global archive semantics instead of treating
datastore movement as enough.

## Data Ownership

| Surface | Owner | Mutability |
| --- | --- | --- |
| Library skill source | SkillsKeeper library source store | Managed through proposal/approval |
| Graph manifest JSON | SkillsKeeper library source store | Managed through graph commands |
| Kuzu cache | SkillsKeeper graph query cache | Generated only |
| Project `.agents/skills` library checkout | Checkout engine | Generated active copy |
| Project `.agents/skills` project-owned skill | Project | Backup-only by default |
| Fully managed local skill | SkillsKeeper active surface reconciler | Managed by explicit commands |
| `~/.codex/skills/keld-*` | SkillsKeeper global mirror | Generated mirror |
| Datastore archive history | SkillsKeeper datastore | Append-forward git history |
| Segregated changes | SkillsKeeper segregation store | Preserved pending user decision |

## App Integration Contract

App type: console and background service.

User/caller surfaces:

- `skillskeeper library graph rebuild`
- `skillskeeper library graph status`
- `skillskeeper checkout skill <skill-id> --workspace <path>`
- `skillskeeper checkout tree <root-id> --workspace <path>`
- `skillskeeper checkout update --workspace <path>`
- `skillskeeper checkout status --workspace <path>`
- `skillskeeper checkout localize <skill-id> --workspace <path>`
- `skillskeeper checkout discard <skill-id> --workspace <path>`
- `skillskeeper library update <skill-id> --from <path>`
- `skillskeeper library review <proposal-id>`
- `skillskeeper library approve <proposal-id>`
- `skillskeeper library archive-proposal <proposal-id>`
- `skillskeeper manage-local --workspace <path> --fully-managed`
- `skillskeeper manage-local --workspace <path> --backup-only`

Invocation routes:

- explicit CLI commands;
- `watch` reconciliation for dirty checkout and fully managed local detection;
- `sync` reconciliation for backup snapshots and active surface repair.

Wiring owner/module:

- CLI parser and command handlers in `skills_keeper/cli.py` initially;
- extracted modules should own graph, checkout, proposal, and active-surface
  logic before implementation grows large.

Observable result:

- graph status output;
- checkout lockfile changes;
- active `.agents/skills` materialization;
- segregated copies with metadata;
- proposal records and review output;
- Codex mirror pruning for managed global archive operations.

Integration validation:

- unit tests for graph traversal, lockfile resolution, proposal state, and
  active-surface reconciliation;
- temporary workspace smoke tests for checkout, dirty-edit segregation,
  proposal review, archive removal, and fully managed local mode;
- no live-instance tests against a running service unless that service is
  intentionally selected for live validation.

## Core Flows

### Top-Down Checkout

1. User requests checkout of a skill, index, context, or profession root.
2. SkillsKeeper validates and hashes the graph manifest.
3. SkillsKeeper rebuilds or verifies the graph query cache.
4. The checkout engine resolves skills, versions, policies, conflicts, and graph
   paths.
5. SkillsKeeper copies clean library skill source into project `.agents/skills`.
6. SkillsKeeper writes or updates the checkout lockfile.

### Dirty Library Checkout Segregation

1. SkillsKeeper compares checkout lockfile hashes to active checkout files.
2. A dirty checkout is copied or moved into `.agents/skillskeeper-segregated/`.
3. SkillsKeeper writes segregation metadata.
4. SkillsKeeper restores the clean checkout from library source.
5. SkillsKeeper notifies through command output, service logs, and later a
   richer notification channel.
6. User chooses localize, propose update, split, overlay, discard, or restore.

### Library Update Proposal

1. User or agent requests a library skill update.
2. The update API writes a proposal instead of mutating library source.
3. Bottom-up traversal computes affected roots and projects.
4. API returns `review_required` with proposal and impact paths.
5. Agent summarizes reusable intent, project-specific risk, and alternatives.
6. User approves or rejects.
7. Approval applies the proposal to library source, refreshes graph/cache data
   as needed, and prepares checkout updates.

### Fully Managed Local Mode

1. Project opts into fully managed local skills.
2. SkillsKeeper records the policy in project metadata or state.
3. Direct additions, edits, and deletions under `.agents/skills` are detected.
4. Changes are segregated outside the active surface.
5. SkillsKeeper restores the accepted active state or leaves a managed absence
   according to policy.
6. User applies changes through explicit SkillsKeeper commands.

### Managed Global Archive

1. User requests archive of a managed global skill.
2. SkillsKeeper identifies the generated mirror path for the skill and active
   Codex prefix, defaulting to `~/.codex/skills/keld-<skill>`.
3. SkillsKeeper records archive history in the datastore.
4. SkillsKeeper deletes the generated mirror when present.
5. SkillsKeeper reports the archive path, mirror path, and mirror removal
   result.

Backup-only local project skills do not use this managed global archive path.
If a user removes one from the project, ordinary backup sync preserves the
disappearance in datastore history without SkillsKeeper claiming source
authority over the local project folder. Fully managed local archive semantics
belong to the fully managed local mode feature, not to the confirmed global
mirror bug.

## Cross-Domain Decisions

- JSON is the canonical graph format for the first implementation.
- Kuzu is a generated cache; SQLite recursive traversal remains a fallback if
  dependency risk blocks the first milestone.
- Checkout copies must be normal directories for Codex compatibility unless a
  future compatibility test approves symlinks.
- The first segregation behavior should avoid merge intelligence: preserve,
  restore clean active state, notify, and require an explicit next command.
- Library updates are proposal-first for all existing library skills in the
  first managed implementation. Conditional bypass rules can come later if they
  prove necessary.
- Fully managed local mode is opt-in. Backup-only local skills remain the
  default so SkillsKeeper does not unexpectedly police ordinary project work.
- Global archive must delete generated Codex mirrors for archived global skills.
- Broader archive active-removal semantics apply only to managed sources and
  generated delivery surfaces.

## Specification Sources

### Graph Manifest And Cache

- Define `skill-graph.json` and `skill-graph.schema.json`.
- Implement manifest validation and stable normalization.
- Implement cache metadata with manifest hash.
- Implement rebuild/status commands.
- Implement top-down and bottom-up traversal APIs.

### Checkout Materialization

- Define checkout lockfile schema.
- Implement skill checkout and tree checkout.
- Implement update and status commands.
- Implement deterministic materialization and hash recording.
- Validate active `.agents/skills` output through temporary workspaces.

### Segregation And Active Surface Reconciliation

- Implement dirty library checkout detection.
- Implement segregation metadata and storage layout.
- Restore clean active checkouts after dirty edits.
- Add command/service notifications.
- Add fully managed local policy and direct change detection.

### Library Proposal Review

- Implement proposal creation for library updates.
- Include diff, proposed skill text, source path, affected roots, and affected
  projects.
- Implement review, approve, and archive-proposal commands.
- Update SkillsKeeper guidance to require API-led proposal review.

### Global Archive Mirror-Removal Fix

- Delete the generated `~/.codex/skills/keld-<skill>` mirror when archiving a
  managed global skill.
- Report whether the mirror existed and was removed.
- Preserve unrelated generated mirrors.
- Decide separately whether the shared source folder is removed, moved, or kept
  marked inactive.
- Keep backup-only local project-owned skills outside this fix.
- Update tests for global archive mirror deletion.

### Release Runtime Separation Prerequisite

- Keep release install separation intact so implementation changes in
  `skills_keeper/` do not directly alter the live SkillsKeeper service.

## Open Questions

- Should the first graph manifest be one file or split node and edge files?
- Should Kuzu be mandatory in the first release, or should traversal start with
  a zero-dependency SQLite/JSON implementation?
- Should checkout updates be automatic, pinned, or policy-driven by workspace?
- Should overlays exist in the first implementation or remain a documented
  future conversion path?
- Should graph and proposal data live inside the existing datastore root or a
  distinct `skills-library/` root inside it?
- What is the first notification channel beyond CLI output and LaunchAgent logs?

## Change History

- 2026-07-17: Created target architecture from skill-library checkout design,
  project brief, and discussion notes; kept status as Designed because the code
  does not yet conform.
