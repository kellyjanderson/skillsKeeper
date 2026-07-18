# SkillsKeeper

SkillsKeeper archives agent skills from registered workspaces into a private git-backed datastore and can mirror shared `~/Documents/Projects` skills into `~/.codex/skills` with a `keld-` namespace.

## Platform And Agent Intent

SkillsKeeper is currently developed and tested on macOS, and the 1.0.0 service
installer targets a per-user macOS LaunchAgent. The project is not intended to
be macOS-only. Contributions that add Linux service support, Windows service or
scheduled-task support, or other portable runtime paths are welcome.

SkillsKeeper is Codex-centric today because it manages Codex skill folders and
mirrors shared skills into `~/.codex/skills`. The project is not opposed to
supporting other agent platforms. Agent-specific integrations should keep clear
boundaries so Codex behavior remains stable while other platforms can add their
own discovery, naming, or runtime surfaces.

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
skillskeeper library graph rebuild
skillskeeper library graph status
skillskeeper checkout skill source-review --workspace /path/to/workspace
skillskeeper checkout tree research-writer --workspace /path/to/workspace
skillskeeper checkout status --workspace /path/to/workspace
skillskeeper datastore init --remote git@github.com:OWNER/PRIVATE-STORE.git
skillskeeper install --package dist/skillskeeper-1.0.0-py3-none-any.whl
skillskeeper install --package . --replace-runtime --no-load
skillskeeper install --package dist/skillskeeper-1.0.0-py3-none-any.whl \
  --datastore-path ~/Library/Application\ Support/SkillsKeeper/datastore \
  --migrate-datastore-from ~/Documents/Projects/skillsKeeper-datastore
skillskeeper service status
skillskeeper skill validate /path/to/skill
skillskeeper skill add /path/to/skill --workspace /path/to/workspace
skillskeeper skill add /path/to/skill --global
skillskeeper skill update /path/to/skill --global
skillskeeper skill directive add skill-name --global --title "Directive title" --body "Directive text"
skillskeeper skill directive remove skill-name --global --title "Directive title"
skillskeeper skill disable specifications-core
skillskeeper skill disable specifications-core --workspace ~/Documents/Projects/example
skillskeeper skill disable specifications-core --no-push
```

`watch` uses `watchdog`, which registers platform filesystem event handlers such as macOS FSEvents instead of polling.

## What Gets Archived

For each registered workspace, SkillsKeeper copies skill directories from:

* `.agents/skills/*/SKILL.md`
* `.agents/*/SKILL.md`

Generated runtime state files are skipped. Each sync commits changes to the datastore repo so lost skills can be restored later.

## Skill Library Graph

`skillskeeper library graph rebuild` validates the datastore graph manifest and
prints its schema version, node count, edge count, stable manifest hash, and
cache metadata path. A successful rebuild writes generated cache metadata under
the datastore graph cache directory:

```text
<datastore>/skills-library/graph/index.kuzu/cache-metadata.json
```

`skillskeeper library graph status` reports `fresh`, `stale`, `missing`, or
`invalid` by comparing cache metadata against the current manifest hash and
schema version. The default manifest path is:

```text
<datastore>/skills-library/graph/skill-graph.json
```

## Checkout Skills

`skillskeeper checkout skill <skill-id> --workspace <path>` materializes one
reusable library skill from the datastore into the workspace active skill
surface:

```text
<workspace>/.agents/skills/<skill-id>
```

The command records generated ownership and the source hash in:

```text
<workspace>/.agents/skillskeeper-lock.json
```

Existing active targets with local changes are not overwritten.

`skillskeeper checkout tree <root-id> --workspace <path>` expands a graph root
and materializes every resolved skill in stable traversal order. The lockfile
records the selected root and each generated checkout entry.

`skillskeeper checkout status --workspace <path>` is read-only. It reports
clean, dirty, missing, and stale generated checkout entries without mutating
active skill files.

## Add / Validate Skills

Validate one or more skill directories or `SKILL.md` files:

```sh
skillskeeper skill validate /path/to/skill
skillskeeper skill validate /path/to/skill-a /path/to/skill-b/SKILL.md
```

Validation checks for:

* a `SKILL.md` file;
* required frontmatter delimiters;
* required `name` and `description` metadata;
* a non-empty skill body;
* optional `agents/openai.yaml` basics.

Add a skill to the caller's workspace, validating before and after install:

```sh
cd /path/to/workspace
skillskeeper skill add /path/to/source-skill
```

That installs into:

```text
<workspace>/.agents/skills/<skill-name>
```

If the workspace is not registered yet, SkillsKeeper registers it by default so future `sync` and `watch` runs preserve the skill. Pass `--no-register` only when you intentionally do not want that workspace watched.

Add a skill to the shared Projects skills set:

```sh
skillskeeper skill add /path/to/source-skill --global
```

That installs into:

```text
~/Documents/Projects/.agents/skills/<skill-name>
```

and mirrors to:

```text
~/.codex/skills/keld-<skill-name>
```

Use `--name <skill-name>` to rename the installed skill. `skill add` is create-only and fails if the target skill already exists. Use `skill update` to intentionally replace an existing managed skill.

Update an existing skill from a source directory, validating before and after replacement:

```sh
skillskeeper skill update /path/to/source-skill --workspace /path/to/workspace
skillskeeper skill update /path/to/source-skill --global
```

`skill update` requires the target skill to already exist and runs `sync` after a successful replacement.

Append a titled directive to an existing skill:

```sh
skillskeeper skill directive add skill-name --global --title "Directive title" --body "Directive text"
skillskeeper skill directive add skill-name --workspace /path/to/workspace --title "Directive title" --body-file directive.md
```

Directives are stored in `SKILL.md` under a `SkillsKeeper Directives` section with stable marker comments. Titles must be unique per skill.

Remove a titled directive:

```sh
skillskeeper skill directive remove skill-name --global --title "Directive title"
skillskeeper skill directive remove skill-name --workspace /path/to/workspace --title "Directive title"
```

Directive add/remove validates the skill afterward and runs `sync` so the private datastore and Codex mirror are reconciled immediately.

If a skill was present in the datastore but is no longer present locally, it is moved to:

```text
archived/missing-from-workspace/<timestamp>/...
```

To intentionally archive an active skill:

```sh
skillskeeper archive /path/to/workspace agents-skills skill-name
skillskeeper archive /path/to/workspace agents-local skill-name
```

When archiving a managed global skill from `~/Documents/Projects`, the matching
generated Codex mirror is removed from `~/.codex/skills` and the command prints
the mirror path plus `removed`, `missing`, or `skipped` status. Use
`--codex-prefix` if the generated mirror uses a prefix other than `keld`.

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

Disable commands reconcile active copies immediately. By default, datastore cleanup is committed and pushed when a datastore remote exists; pass `--no-push` to keep the cleanup local.

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

`skillskeeper install` is the first-class user install path on macOS. It
creates or updates a service runtime virtual environment, installs SkillsKeeper
non-editably into that runtime, writes state, and installs a user LaunchAgent.
Linux and Windows service installers are intentionally open contribution areas.

The default service runtime is:

```text
~/Library/Application Support/SkillsKeeper/service-runtime/.venv
```

The LaunchAgent runs:

```text
~/Library/Application Support/SkillsKeeper/service-runtime/.venv/bin/skillskeeper
```

State is written under:

```text
~/Library/Application Support/SkillsKeeper/state.json
```

and the user LaunchAgent is:

```text
~/Library/LaunchAgents/com.kellyjanderson.skillskeeper.plist
```

Install a release wheel:

```sh
skillskeeper install --package dist/skillskeeper-1.0.0-py3-none-any.whl
```

Install from a source checkout into the service runtime without making the
service editable from that checkout:

```sh
skillskeeper install --package . --replace-runtime
```

Prepare files without loading launchd:

```sh
skillskeeper install --package . --replace-runtime --no-load
```

Migrate an existing development datastore into Application Support during
install:

```sh
skillskeeper install \
  --package dist/skillskeeper-1.0.0-py3-none-any.whl \
  --datastore-path ~/Library/Application\ Support/SkillsKeeper/datastore \
  --migrate-datastore-from ~/Documents/Projects/skillsKeeper-datastore
```

If the destination datastore already exists, pass `--replace-datastore` only
after confirming replacement is intended.

The installer backs up an existing `state.json` and LaunchAgent plist before
rewriting them. It can infer watched folders from `.skillskeeper-source.json`
manifests in the datastore.

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
