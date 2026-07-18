# SkillsKeeper Releases

Status: Designed

This directory is for version-level release definitions and release checklists.
Release documents describe the intent and scope of a version; they should link
to implementation plans, specifications, and tests instead of becoming a second
implementation checklist.

## Initial Release Management Milestone

The first release-management milestone should make SkillsKeeper installable as a
stable user-scoped release while the source checkout remains free for active
development.

Expected outcomes:

- release executable installed outside the source checkout;
- LaunchAgent targets the release executable;
- state, datastore, logs, and service files use documented user-scoped paths;
- initial migration script can move or copy dev-instance data safely;
- rollback and preflight behavior are documented and tested.

Related plan:

- `project/planning/release-management-action-plan.md`

