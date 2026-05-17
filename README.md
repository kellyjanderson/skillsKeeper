# SkillsKeeper

SkillsKeeper archives agent skills from registered workspaces into a private git-backed datastore and can mirror shared `~/Documents/Projects` skills into `~/.codex/skills` with a `keld-` namespace.

## Safety Model

SkillsKeeper is non-destructive by default:

* `sync` and `watch` never rewrite git history.
* if a previously archived active skill disappears from a workspace, SkillsKeeper moves the active datastore copy from `registered/...` to `archived/missing-from-workspace/<timestamp>/...`.
* intentional removal from the current active set requires an explicit command.
* even `delete-current` only deletes from the current tree and commits that change forward; old versions remain recoverable through git history.

## Core Commands

```sh
skillskeeper register /path/to/workspace
skillskeeper infer --datastore ~/Documents/Projects/skillsKeeper-datastore
skillskeeper sync
skillskeeper watch
skillskeeper codex-sync
skillskeeper datastore init --remote git@github.com:OWNER/PRIVATE-STORE.git
skillskeeper install --datastore-path ~/Documents/Projects/skillsKeeper-datastore
skillskeeper service status
skillskeeper skill disable specifications-core
skillskeeper skill disable specifications-core --workspace ~/Documents/Projects/example
```

`watch` uses `watchdog`, which registers platform filesystem event handlers such as macOS FSEvents instead of polling.

## What Gets Archived

For each registered workspace, SkillsKeeper copies skill directories from:

* `.agents/skills/*/SKILL.md`
* `.agents/*/SKILL.md`

Generated runtime state files are skipped. Each sync commits changes to the datastore repo so lost skills can be restored later.

If a skill was present in the datastore but is no longer present locally, it is moved to:

```text
archived/missing-from-workspace/<timestamp>/...
```

To intentionally archive an active skill:

```sh
skillskeeper archive /path/to/workspace agents-skills skill-name
skillskeeper archive /path/to/workspace agents-local skill-name
```

To intentionally remove a skill from the current active datastore set:

```sh
skillskeeper delete-current /path/to/workspace agents-skills skill-name --confirm delete-current
```

That command does not rewrite history.

## Enable / Disable

Skill enablement is stored in:

```text
~/Library/Application Support/SkillsKeeper/state.json
```

Disable a skill globally:

```sh
skillskeeper skill disable specifications-core
```

Disable a skill for one watched workspace only:

```sh
skillskeeper skill disable specifications-core --workspace ~/Documents/Projects/example
```

Enable it again with the matching command:

```sh
skillskeeper skill enable specifications-core
skillskeeper skill enable specifications-core --workspace ~/Documents/Projects/example
```

Global disable wins over workspace settings. Disabled skills are not copied into the active datastore tree or Codex mirror. If a disabled skill was already active, it is moved to `archived/disabled/<timestamp>/...` in the datastore and removed from the current Codex mirror.

For watched workspaces, disabled runtime skills are also moved out of:

```text
.agents/skills/<skill-name>
```

and into:

```text
.agents/.skillskeeper-disabled/<timestamp>/<skill-name>
```

This keeps the current skill set clean without destroying the local copy.

## Install

`skillskeeper install` writes state under:

```text
~/Library/Application Support/SkillsKeeper/state.json
```

and installs a user LaunchAgent:

```text
~/Library/LaunchAgents/com.kellyjanderson.skillskeeper.plist
```

The installer can infer watched folders from `.skillskeeper-source.json` manifests in the datastore:

```sh
skillskeeper install \
  --datastore-path ~/Documents/Projects/skillsKeeper-datastore
```

Logs are written under:

```text
~/Library/Logs/SkillsKeeper
```

## Shared Projects Skills

`skillskeeper codex-sync` copies skills from:

```text
~/Documents/Projects/.agents/skills
```

into:

```text
~/.codex/skills/keld-<skill-name>
```

The copied `SKILL.md` metadata name is rewritten to `keld-<skill-name>` so Codex sees a stable namespaced skill.
