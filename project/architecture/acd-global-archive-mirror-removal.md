# ACD: Global Archive Mirror Removal

Target release: 2.0.0
ACD status: Proposed
Architecture state: Change to existing behavior. Not implemented.

## Summary

Global skill archive must delete the generated Codex mirror for the archived
global skill. Today, `archive` moves a datastore active copy but does not remove
the generated `~/.codex/skills/keld-<skill>` mirror, so the archived skill can
remain active in Codex discovery.

## Existing Architecture

Current SkillsKeeper architecture has separate behaviors:

- `codex-sync` generates mirrors from shared Projects skills into
  `~/.codex/skills/keld-*`;
- `disable` prunes matching generated mirrors as part of reconciliation;
- `archive` moves an active datastore copy to archive history, but does not
  own generated mirror pruning.

## Target Architecture

Managed global archive owns generated mirror removal.

When a managed global skill is archived:

1. SkillsKeeper resolves the managed global skill identity.
2. SkillsKeeper moves or records archive history in the datastore.
3. SkillsKeeper computes the generated mirror path using the active Codex
   prefix, default `keld`.
4. SkillsKeeper deletes `~/.codex/skills/keld-<skill>` when it exists.
5. SkillsKeeper reports the archive path, mirror path, and mirror removal
   result.

Backup-only local project skills are outside this ACD.

## Affected Architecture Documents

- `project/architecture/skillskeeper-2.0-architecture-overview.md`
- `project/architecture/skills-library-management-architecture.md`

## Conformance Plan

- Add archive route ownership classification.
- Add generated mirror path calculation to archive handling.
- Add mirror deletion after successful managed global archive.
- Add output fields for mirror path and removal result.
- Preserve unrelated generated mirrors.
- Keep backup-only local project folders untouched.

## Specification Sources

- Implement managed global archive mirror deletion.
- Add tests for existing mirror removal.
- Add tests for missing mirror reporting.
- Add tests for custom Codex prefix.
- Add tests that unrelated mirrors remain untouched.
- Add tests that backup-only local archive behavior is not changed by this ACD.

## Closure Criteria

- Tests prove archived managed global skills disappear from generated Codex
  mirrors.
- Command output reports mirror deletion state.
- Documentation distinguishes managed global archive from backup-only local
  behavior.
- Canonical architecture is updated to describe the conformed archive behavior.

## Change History

- 2026-07-17: Created ACD for the 2.0.0p planning branch.
