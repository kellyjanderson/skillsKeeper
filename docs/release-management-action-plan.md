# SkillsKeeper Release Management Action Plan

Status: Implemented for the 1.0.0 release installer; library-management work
remains separate future work.

This plan prepares SkillsKeeper for active development while keeping a
functional installed release available beside the development checkout. The
1.0.0 installer now owns the release runtime path, non-editable package install,
LaunchAgent writing, and datastore migration option.

## Current State

- The package is defined in `pyproject.toml` as `skillskeeper` version `1.0.0`.
- The console entry point is `skillskeeper = "skills_keeper.cli:main"`.
- `skillskeeper install` writes state to
  `~/Library/Application Support/SkillsKeeper/state.json`, can migrate or
  initialize the configured datastore, installs SkillsKeeper non-editably into
  the service runtime venv, and installs a LaunchAgent at
  `~/Library/LaunchAgents/com.kellyjanderson.skillskeeper.plist`.
- The LaunchAgent runs:

  ```text
  ~/Library/Application Support/SkillsKeeper/service-runtime/.venv/bin/skillskeeper
  ```
- No repo-local instance data was found under common names such as `state.json`,
  `datastore`, `registered`, `archived`, `.skillskeeper*`, or LaunchAgent plists
  in this checkout during this planning pass.
- If a sibling datastore directory exists near a development checkout, it should
  be treated as instance data and preserved outside the source checkout.

## Release Goals

1. Keep the development checkout free for active feature work.
2. Install a stable released SkillsKeeper executable into a dedicated release
   location.
3. Run the LaunchAgent against the release executable, not against the
   development checkout.
4. Migrate any instance data out of the source checkout before release-managed
   operation begins.
5. Make release install, rollback, and migration validation explicit enough that
   a failed install does not risk active skill archives.

## Proposed Runtime Layout

Use user-scoped paths so the tool remains personal and does not require system
administrator installation:

```text
~/Library/Application Support/SkillsKeeper/service-runtime/.venv/
~/Library/Application Support/SkillsKeeper/state.json
~/Library/Application Support/SkillsKeeper/datastore/
~/Library/Logs/SkillsKeeper/
~/Library/LaunchAgents/com.kellyjanderson.skillskeeper.plist
```

The release executable lives in the service runtime venv while state, logs, and
datastore remain version-independent. Future rollback can be added by retaining
multiple runtime roots; 1.0.0 uses a single replaceable service runtime.

## Work Plan

### 1. Define Release Installation Contract

- Add a documented installer contract for release installs.
- Choose the install source modes and names explicitly:
  - released package or built wheel for normal installs;
  - source checkout only when intentionally requested for development testing.
- Ensure source-vs-destination wording is unambiguous. Prefer names such as
  `--from-local-source` for development installs if a local-source path is
  needed.
- Add `skillskeeper install --runtime-root <path>` for the release runtime.
- Update the LaunchAgent writer so it targets the service runtime
  `bin/skillskeeper` instead of the invoking command.

Acceptance:

- `skillskeeper install` installs a release-managed executable without
  depending on the source checkout.
- `skillskeeper service status` reports a service whose program path resolves
  through the service runtime venv path.
- Existing state and datastore paths are unchanged unless the user opts into a
  migration.

### 2. Add Initial Migration Script

Create an idempotent migration command or script:

```text
scripts/migrate_dev_instance.py
```

The 1.0.0 installer also includes the first-class migration flags:

```text
skillskeeper install --migrate-datastore-from <path> --datastore-path <path>
```

The migration should:

- scan the development checkout for known instance-data paths;
- scan one level above the checkout for the existing sibling datastore pattern;
- copy stateful datastore data to the canonical Application Support layout;
- preserve git history for datastore directories;
- never delete source data;
- write a migration manifest with source path, destination path, timestamp, and
  action taken;
- support `--dry-run` and make it the recommended first command;
- refuse to overwrite non-empty destination data unless `--replace-datastore`
  is explicitly chosen.

Candidate data to detect:

```text
state.json
datastore/
skillsKeeper-datastore/
registered/
archived/
.skillskeeper-source.json
.skillskeeper-disabled/
*.plist
```

Acceptance:

- Dry run prints every detected source and planned destination.
- Running the migration twice is safe and produces no duplicate datastore data.
- Migration preserves datastore `.git` metadata when moving or copying a full
  datastore.
- Migration tests cover empty checkout, checkout-local datastore, sibling
  datastore, existing destination, and invalid JSON state.

### 3. Separate Development And Release Commands

- Add README guidance for three workflows:
  - development checkout test run;
  - release install;
  - release rollback.
- Add a command or script for building a local release artifact:

```text
python3 -m pip wheel --no-deps --wheel-dir dist .
```

- Add a local smoke command that resolves the executable path before writing the
  LaunchAgent.
- Ensure release docs explain that `pip install -e .` is development-only and
  should not be the service runtime.

Acceptance:

- A developer can run tests from the checkout without changing the installed
  service.
- A user can upgrade the installed release without changing source branches.
- Rollback instructions include stopping service, reinstalling the desired
  package into the service runtime, and restarting service.

### 4. Harden State And Service Safety

- Add a pre-install backup of existing `state.json` and LaunchAgent plist.
- Add a service preflight that verifies:
  - executable exists;
  - executable returns `skillskeeper --help`;
  - state path is readable or creatable;
  - datastore path is a git repository or can be initialized.
- Add install output that names the exact executable, state path, datastore, and
  plist path.
- Add a no-service mode for preparing a release install without loading launchd.

Acceptance:

- Failed install leaves the previous LaunchAgent and state recoverable.
- `--no-load` installs files without starting or restarting the service.
- Preflight failures return nonzero and do not replace the active service plist.

### 5. Add Release Documentation Surfaces

- Create `docs/releases/README.md` to describe release definitions and release
  notes.
- Add one initial release definition for the install/migration milestone.
- Keep release definitions separate from progression checklists.
- Add a release checklist that includes:
  - version bump;
  - tests;
  - migration dry run;
  - install smoke;
  - service smoke;
  - rollback smoke;
  - README update.

Acceptance:

- Release intent is documented before implementation starts.
- Future feature documentation can link to the release definition instead of
  overloading the README.

### 6. Verification Plan

Automated checks:

```sh
python3 -m unittest
python3 -m pip wheel --no-deps --wheel-dir dist .
python3 -m pip install --target <temp-release-root> dist/*.whl
<temp-release-root>/bin/skillskeeper --help
```

Manual smoke checks:

```sh
skillskeeper install --package dist/skillskeeper-1.0.0-py3-none-any.whl --no-load
skillskeeper service status
```

Do not run destructive migration modes during ordinary CI or docs validation.

## Implementation Order

1. Add release docs and release checklist.
2. Add migration discovery logic with dry-run-only behavior.
3. Add migration copy behavior with manifest output.
4. Add runtime-root install support.
5. Update LaunchAgent generation to use the service runtime executable.
6. Add preflight protections.
7. Update README examples and run full verification.

## Open Decisions

- Whether the migration entry point should start as a standalone script or a
  first-class `skillskeeper migrate` subcommand.
- Whether release installs should build from local wheel artifacts only, or also
  support installing directly from a tagged GitHub release.
- Whether `~/.local/share/skillskeeper` is the final release-root default, or
  whether the app should keep all non-service files under
  `~/Library/Application Support/SkillsKeeper`.
- Whether an existing development datastore should become the canonical
  datastore or be migrated into Application Support.
