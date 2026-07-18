# ACD: Active Surface Ownership Transition

Target release: 2.0.0
ACD status: Proposed
Architecture state: Change to existing behavior. Not implemented.

## Summary

SkillsKeeper currently treats watched project skill folders primarily as backup
sources. The 2.0.0 architecture adds generated library checkouts and opt-in
fully managed local skills, which require ownership-aware reconciliation of
`.agents/skills` as an active Codex selection surface.

This is a change to existing sync/watch assumptions, so it is tracked as an
ACD while implementation moves into conformance.

## Existing Architecture

Current behavior:

- project `.agents/skills` folders are discoverable source material;
- sync/watch archives discovered skills into a private datastore;
- direct edits to project-owned skills are allowed;
- generated checkout ownership is not represented;
- fully managed local mode does not exist.

## Target Architecture

`.agents/skills` is classified by ownership before reconciliation:

- project-owned backup-only skills remain editable by default;
- library checkouts are generated active copies and direct edits are
  segregated;
- fully managed local skills are opt-in generated/managed active copies and
  direct add/edit/delete changes are segregated;
- global mirrors are generated under `~/.codex/skills/keld-*` and managed by
  the global mirror manager.

The active surface reconciler owns detection and repair for generated or fully
managed active copies. It must preserve user work outside the active selection
surface instead of silently discarding it.

## Affected Architecture Documents

- `project/architecture/project-checkouts-and-active-surface.md`
- `project/architecture/skillskeeper-2.0-architecture-overview.md`
- `project/architecture/skills-library-management-architecture.md`

## Conformance Plan

- Add checkout lockfile ownership metadata.
- Add project policy for backup-only versus fully managed local mode.
- Add segregation storage and metadata.
- Add dirty library checkout detection.
- Add fully managed local direct add/edit/delete detection.
- Update watch/sync reconciliation to branch by ownership class.
- Keep backup-only project-owned skill behavior unchanged unless a project opts
  into fully managed mode.

## Specification Sources

- Implement checkout lockfile schema.
- Implement active surface ownership classifier.
- Implement segregation metadata schema.
- Implement dirty library checkout reconciliation.
- Implement fully managed local reconciliation.
- Add tests proving backup-only project-owned skill edits are still allowed.
- Add watcher integration tests for generated checkout and fully managed local
  paths.

## Closure Criteria

- Generated library checkout edits are segregated and clean active copies are
  restored.
- Fully managed local direct changes are segregated.
- Backup-only local project skills remain editable and backed up.
- Canonical architecture is updated to describe conformed ownership-aware
  reconciliation.

## Change History

- 2026-07-17: Created ACD for the 2.0.0p planning branch.
