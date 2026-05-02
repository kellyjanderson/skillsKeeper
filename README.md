# SkillsKeeper

SkillsKeeper archives agent skills from registered workspaces into a private git-backed datastore and can mirror shared `~/Documents/Projects` skills into `~/.codex/skills` with a `keld-` namespace.

## Core Commands

```sh
skillskeeper register /path/to/workspace
skillskeeper sync
skillskeeper watch
skillskeeper codex-sync
skillskeeper datastore init --remote git@github.com:OWNER/PRIVATE-STORE.git
```

`watch` uses `watchdog`, which registers platform filesystem event handlers such as macOS FSEvents instead of polling.

## What Gets Archived

For each registered workspace, SkillsKeeper copies skill directories from:

* `.agents/skills/*/SKILL.md`
* `.agents/*/SKILL.md`

Generated runtime state files are skipped. Each sync commits changes to the datastore repo so lost skills can be restored later.

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

