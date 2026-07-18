# Skill Library Management And Active Surface Fix Plan

Status: Designed. Not implemented.

## Safety Prerequisite

Do not edit `skills_keeper/` implementation files for this plan until the live
SkillsKeeper service is no longer an editable install from this checkout, or the
service is intentionally paused for live-instance development.

The current safe planning scope is planning artifacts under `project/`.

## Planning Basis

Architecture source:

- `project/architecture/skills-library-management-architecture.md`

Feature definition sources:

- `project/notes/skills-library-checkouts/skillskeeper-library-checkout-design.md`
- `project/notes/skills-library-checkouts/skillskeeper-library-project-brief.md`
- `project/notes/skills-library-checkouts/2026-07-17-skill-library-checkouts.md`

Issue source:

- Global archive behavior does not delete the generated Codex mirror for the
  archived global skill.

## Key Fix Decision

Resolve the concrete archive issue first:

- Managed global skill archive must remove the generated
  `~/.codex/skills/keld-<skill>` mirror for the archived skill.
- The mirror removal should be part of the archive transaction/reporting, not
  something left for a later manual `codex-sync`.

Keep related ownership boundaries explicit:

- Backup-only project-owned local skills: SkillsKeeper preserves history but
  does not actively archive or police the project source folder.
- Managed global skills: archive removes or marks inactive the shared source
  copy and prunes the generated `~/.codex/skills/keld-*` mirror.
- Library checkouts: use checkout discard/update semantics for project active
  copies; archive belongs to library source and must run through impact review.
- Fully managed local skills: archive removes the active project copy and
  preserves history/metadata through SkillsKeeper-managed storage.

This means the fully managed local feature should absorb the "local archive"
case. Current backup-only local management should not become archive-enforced.

## Work Items

### 1. Release Runtime Separation

- Implement release install separation from
  `project/planning/release-management-action-plan.md`.
- Move the live service away from editable source checkout operation.
- Verify LaunchAgent points at release runtime, not this checkout.

Validation:

- service executable path is outside the development checkout;
- `python -m pip show skillskeeper` in service runtime has no editable project
  location;
- service status still works.

### 2. Graph Foundation

- Add canonical graph manifest and JSON schema.
- Add graph validation.
- Add generated graph cache metadata with manifest hash.
- Add graph rebuild/status commands.
- Add deterministic top-down and bottom-up traversal tests.

Validation:

- sample graph validates;
- stale cache is detected;
- traversal output is stable across repeated runs.

### 3. Checkout Lockfile And Materialization

- Add checkout lockfile schema.
- Add checkout of one skill into a temporary workspace.
- Add checkout of one root/tree into a temporary workspace.
- Record selected graph paths, source hashes, and versions.
- Keep project-owned skills distinct from library checkout skills.

Validation:

- project `.agents/skills` contains expected clean checkout copies;
- lockfile explains every managed checkout;
- project-owned skills remain untouched.

### 4. Dirty Checkout Segregation

- Detect hash mismatch for checked-out library skills.
- Move or copy dirty checkout into `.agents/skillskeeper-segregated/`.
- Write segregation metadata.
- Restore clean checkout into `.agents/skills`.
- Print actionable recovery choices.

Validation:

- dirty edit is preserved outside active skill selection;
- active checkout returns to clean library hash;
- repeated reconciliation is idempotent.

### 5. Library Update Proposal Flow

- Change library update behavior so existing library skills are not directly
  mutated.
- Create proposal artifacts with diff and proposed skill text.
- Run bottom-up impact traversal.
- Return `review_required`.
- Implement review, approve, and archive-proposal commands.

Validation:

- update command does not alter library source before approval;
- proposal lists affected roots and checked-out projects;
- approval applies exactly the proposed change;
- rejected proposals are archived without source mutation.

### 6. Fully Managed Local Mode

- Add project policy for `backup-only` versus `fully-managed`.
- Keep `backup-only` as the default.
- In fully managed mode, detect direct additions, edits, and deletions under
  `.agents/skills`.
- Segregate unmanaged changes and preserve metadata.
- Require SkillsKeeper commands for add, update, archive, localize, or discard.

Validation:

- backup-only local skill edits continue to be backed up without enforcement;
- fully managed direct edit is segregated and active state is restored;
- fully managed direct addition is preserved as a proposed project skill;
- fully managed direct deletion is recorded and handled explicitly.

### 7. Global Archive Mirror-Removal Fix

- Update managed global archive handling so archiving a global skill deletes its
  generated Codex mirror:
  - identify the archived global skill identity;
  - compute the generated mirror path using the active Codex prefix, default
    `keld`;
  - remove `~/.codex/skills/keld-<skill>` when it exists;
  - leave unrelated mirrors untouched;
  - commit datastore changes;
  - report whether the mirror existed and whether it was removed.
- Decide whether global archive should also remove or move
  `~/Documents/Projects/.agents/skills/<skill>` in the same implementation.
  Mirror deletion is the confirmed bug; shared-source removal needs an explicit
  ownership decision before implementation.
- Keep backup-only local project skills out of this fix. Ordinary local deletion
  plus sync preserves history without SkillsKeeper actively archiving the
  project source folder.
- Defer fully managed local archive semantics to the fully managed local mode
  work item unless a concrete current bug is identified there.

Validation:

- archived managed global skill disappears from the Codex mirror path;
- archive output reports the mirror path and removal result;
- unrelated generated mirrors remain in place;
- backup-only local project folders are not touched by the global mirror fix;
- tests cover existing mirror, missing mirror, custom prefix, and unrelated
  mirror preservation.

### 8. SkillsKeeper Guidance Update

- Update the SkillsKeeper skill guidance after implementation exists.
- Explain managed library checkout rules.
- Explain fully managed local mode.
- Explain that global archive deletes generated Codex mirrors.
- Reinforce API-first management for library updates and proposals.

Validation:

- guidance is validated through SkillsKeeper after the release runtime is safely
  separated or intentionally used for live managed-skill updates.

## Open Decisions

- Whether global managed archive should delete the shared source folder or move
  it into a local disabled/archive folder before datastore commit.
- Whether fully managed local direct additions should become proposals by
  default or be segregated until the user names the intended action.
- Whether library source archive should be allowed before graph impact review is
  implemented.
