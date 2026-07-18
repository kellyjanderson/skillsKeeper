from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

from skills_keeper import cli


class SkillsKeeperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def make_skill(
        self,
        root: Path,
        name: str,
        body: str = "# Skill\n",
        metadata_name: str | None = None,
    ) -> Path:
        skill_dir = root / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {metadata_name or name}\ndescription: Test skill.\n---\n\n{body}",
            encoding="utf-8",
        )
        return skill_dir

    def test_discovers_runtime_and_local_skills(self) -> None:
        workspace = self.root / "app"
        self.make_skill(workspace / ".agents" / "skills", "runtime-skill")
        self.make_skill(workspace / ".agents", "local-skill")

        sources = cli.discover_skill_sources(workspace)

        self.assertEqual([source.identity for source in sources], ["runtime-skill", "local-skill"])
        self.assertEqual([source.source_kind for source in sources], ["agents-skills", "agents-local"])

    def test_archive_workspace_copies_skill_and_manifest(self) -> None:
        workspace = self.root / "app"
        datastore = self.root / "store"
        self.make_skill(workspace / ".agents" / "skills", "runtime-skill")

        count = cli.archive_workspace(datastore, workspace)

        self.assertEqual(count, 1)
        archived = datastore / "registered" / cli.workspace_key(workspace) / "agents-skills" / "runtime-skill"
        self.assertTrue((archived / "SKILL.md").exists())
        self.assertTrue((archived / ".skillskeeper-source.json").exists())

    def test_archive_workspace_moves_missing_active_skill_to_archive(self) -> None:
        workspace = self.root / "app"
        datastore = self.root / "store"
        skill = self.make_skill(workspace / ".agents" / "skills", "runtime-skill")
        cli.archive_workspace(datastore, workspace)
        self.assertTrue(
            datastore.joinpath(
                "registered",
                cli.workspace_key(workspace),
                "agents-skills",
                "runtime-skill",
                "SKILL.md",
            ).exists()
        )

        for path in sorted(skill.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        skill.rmdir()
        count = cli.archive_workspace(datastore, workspace)

        self.assertEqual(count, 0)
        self.assertFalse(
            datastore.joinpath(
                "registered",
                cli.workspace_key(workspace),
                "agents-skills",
                "runtime-skill",
            ).exists()
        )
        archived = list(datastore.glob("archived/missing-from-workspace/*/*/agents-skills/runtime-skill/SKILL.md"))
        self.assertEqual(len(archived), 1)

    def test_infer_workspaces_from_datastore_manifest(self) -> None:
        workspace = self.root / "app"
        datastore = self.root / "store"
        self.make_skill(workspace / ".agents" / "skills", "runtime-skill")
        cli.archive_workspace(datastore, workspace)

        inferred = cli.infer_workspaces_from_datastore(datastore)

        self.assertEqual(inferred, [workspace.resolve()])

    def test_merge_registered_workspaces_adds_only_new_paths(self) -> None:
        app = (self.root / "app").resolve()
        other = (self.root / "other").resolve()
        state = {"version": 1, "workspaces": [{"path": str(app)}]}

        merged, added = cli.merge_registered_workspaces(state, [app, other])

        self.assertEqual(added, 1)
        self.assertEqual([item["path"] for item in merged["workspaces"]], [str(app), str(other)])

    def test_global_disable_archives_active_skill_and_skips_recopy(self) -> None:
        workspace = self.root / "app"
        datastore = self.root / "store"
        self.make_skill(workspace / ".agents" / "skills", "specifications-core")
        cli.archive_workspace(datastore, workspace)
        state = {"version": 1, "skill_flags": {"global": {}, "workspaces": {}}}
        cli.set_skill_enabled(state, "specifications-core", False)

        count = cli.archive_workspace(datastore, workspace, state=state)

        self.assertEqual(count, 0)
        self.assertFalse(
            datastore.joinpath(
                "registered",
                cli.workspace_key(workspace),
                "agents-skills",
                "specifications-core",
            ).exists()
        )
        archived = list(datastore.glob("archived/disabled/*/*/agents-skills/specifications-core/SKILL.md"))
        self.assertEqual(len(archived), 1)

    def test_workspace_disable_only_applies_to_that_workspace(self) -> None:
        first = self.root / "first"
        second = self.root / "second"
        state = {"version": 1, "skill_flags": {"global": {}, "workspaces": {}}}
        cli.set_skill_enabled(state, "specifications-core", False, workspace=first)

        self.assertFalse(cli.skill_enabled(state, first, "specifications-core"))
        self.assertTrue(cli.skill_enabled(state, second, "specifications-core"))

    def test_codex_sync_prunes_globally_disabled_project_skill(self) -> None:
        state = {"version": 1, "skill_flags": {"global": {}, "workspaces": {}}}
        cli.set_skill_enabled(state, "specifications-core", False)
        self.assertIn("specifications-core", cli.disabled_skill_keys(state, self.root))

    def test_disabled_workspace_skill_dir_moves_to_local_disabled_archive(self) -> None:
        workspace = self.root / "app"
        self.make_skill(workspace / ".agents" / "skills", "specifications-core")
        state = {"version": 1, "skill_flags": {"global": {}, "workspaces": {}}}
        cli.set_skill_enabled(state, "specifications-core", False)

        moved = cli.move_disabled_workspace_skill_dirs(state, workspace)

        self.assertEqual(moved, 1)
        self.assertFalse((workspace / ".agents" / "skills" / "specifications-core").exists())
        archived = list(
            (workspace / ".agents" / ".skillskeeper-disabled").glob("*/specifications-core/SKILL.md")
        )
        self.assertEqual(len(archived), 1)

    def test_disabled_workspace_skill_dir_matches_frontmatter_identity(self) -> None:
        workspace = self.root / "app"
        self.make_skill(
            workspace / ".agents" / "skills",
            "folder-name",
            metadata_name="frontmatter-name",
        )
        state = {"version": 1, "skill_flags": {"global": {}, "workspaces": {}}}
        cli.set_skill_enabled(state, "frontmatter-name", False)

        moved = cli.move_disabled_workspace_skill_dirs(state, workspace)

        self.assertEqual(moved, 1)
        self.assertFalse((workspace / ".agents" / "skills" / "folder-name").exists())
        archived = list(
            (workspace / ".agents" / ".skillskeeper-disabled").glob("*/folder-name/SKILL.md")
        )
        self.assertEqual(len(archived), 1)

    def test_skill_disable_command_reconciles_active_copies_immediately(self) -> None:
        old_paths = (
            cli.STATE_PATH,
            cli.DEFAULT_DATASTORE,
            cli.PROJECTS_SKILLS,
            cli.CODEX_SKILLS,
            cli.git_commit_all,
        )
        try:
            workspace = (self.root / "app").resolve()
            datastore = self.root / "store"
            projects_root = self.root / "Projects"
            projects_skills = projects_root / ".agents" / "skills"
            codex_skills = self.root / "codex-skills"
            self.make_skill(workspace / ".agents" / "skills", "specifications-core")
            self.make_skill(projects_skills, "specifications-core")
            cli.archive_workspace(datastore, workspace)
            cli.copy_tree_clean(
                projects_skills / "specifications-core",
                codex_skills / "keld-specifications-core",
            )
            state_path = self.root / "state.json"
            cli.STATE_PATH = state_path
            cli.DEFAULT_DATASTORE = datastore
            cli.PROJECTS_SKILLS = projects_skills
            cli.CODEX_SKILLS = codex_skills
            cli.git_commit_all = lambda _path, _message: False
            cli.write_state(
                {
                    "version": 1,
                    "datastore": str(datastore),
                    "workspaces": [{"path": str(workspace)}],
                    "skill_flags": {"global": {}, "workspaces": {}},
                }
            )

            with redirect_stdout(StringIO()):
                result = cli.command_skill_flag(
                    SimpleNamespace(
                        workspace=None,
                        skill_command="disable",
                        identity="specifications-core",
                        no_push=True,
                        codex_prefix="keld",
                    )
                )

            self.assertEqual(result, 0)
            self.assertFalse(
                datastore.joinpath(
                    "registered",
                    cli.workspace_key(workspace),
                    "agents-skills",
                    "specifications-core",
                ).exists()
            )
            self.assertFalse((workspace / ".agents" / "skills" / "specifications-core").exists())
            self.assertFalse((codex_skills / "keld-specifications-core").exists())
        finally:
            (
                cli.STATE_PATH,
                cli.DEFAULT_DATASTORE,
                cli.PROJECTS_SKILLS,
                cli.CODEX_SKILLS,
                cli.git_commit_all,
            ) = old_paths

    def test_install_honors_datastore_path_before_initializing_repo(self) -> None:
        old_paths = (cli.STATE_PATH, cli.DEFAULT_DATASTORE, cli.PLIST_PATH, cli.LOG_DIR)
        try:
            cli.STATE_PATH = self.root / "state.json"
            cli.DEFAULT_DATASTORE = self.root / "default-store"
            cli.PLIST_PATH = self.root / "LaunchAgents" / "skillskeeper.plist"
            cli.LOG_DIR = self.root / "Logs"
            explicit_store = self.root / "explicit-store"
            runtime_root = self.root / "runtime"
            service_bin = runtime_root / ".venv" / "bin" / "skillskeeper"
            service_bin.parent.mkdir(parents=True)
            service_bin.write_text("#!/bin/sh\n", encoding="utf-8")

            with redirect_stdout(StringIO()):
                result = cli.command_install(
                    SimpleNamespace(
                        package=None,
                        runtime_root=str(runtime_root),
                        runtime_python=str(Path("/usr/bin/python3")),
                        replace_runtime=False,
                        skip_runtime_install=True,
                        datastore_path=str(explicit_store),
                        datastore_remote=None,
                        migrate_datastore_from=None,
                        replace_datastore=False,
                        debounce=1.0,
                        no_push=True,
                        load=False,
                    )
                )

            self.assertEqual(result, 0)
            self.assertFalse((self.root / "default-store" / ".git").exists())
            self.assertTrue((explicit_store / ".git").exists())
        finally:
            cli.STATE_PATH, cli.DEFAULT_DATASTORE, cli.PLIST_PATH, cli.LOG_DIR = old_paths

    def test_install_writes_launch_agent_to_service_runtime_executable(self) -> None:
        old_paths = (cli.STATE_PATH, cli.DEFAULT_DATASTORE, cli.PLIST_PATH, cli.LOG_DIR)
        try:
            cli.STATE_PATH = self.root / "state.json"
            cli.DEFAULT_DATASTORE = self.root / "store"
            cli.PLIST_PATH = self.root / "LaunchAgents" / "skillskeeper.plist"
            cli.LOG_DIR = self.root / "Logs"
            runtime_root = self.root / "runtime"
            service_bin = runtime_root / ".venv" / "bin" / "skillskeeper"
            service_bin.parent.mkdir(parents=True)
            service_bin.write_text("#!/bin/sh\n", encoding="utf-8")

            with redirect_stdout(StringIO()):
                result = cli.command_install(
                    SimpleNamespace(
                        package=None,
                        runtime_root=str(runtime_root),
                        runtime_python=str(Path("/usr/bin/python3")),
                        replace_runtime=False,
                        skip_runtime_install=True,
                        datastore_path=str(self.root / "store"),
                        datastore_remote=None,
                        migrate_datastore_from=None,
                        replace_datastore=False,
                        debounce=2.5,
                        no_push=True,
                        load=False,
                    )
                )

            self.assertEqual(result, 0)
            plist = cli.plistlib.loads(cli.PLIST_PATH.read_bytes())
            self.assertEqual(plist["ProgramArguments"][0], str(service_bin.resolve()))
            self.assertNotIn("WorkingDirectory", plist)
        finally:
            cli.STATE_PATH, cli.DEFAULT_DATASTORE, cli.PLIST_PATH, cli.LOG_DIR = old_paths

    def test_install_can_migrate_datastore_before_initializing_repo(self) -> None:
        old_paths = (cli.STATE_PATH, cli.DEFAULT_DATASTORE, cli.PLIST_PATH, cli.LOG_DIR)
        try:
            cli.STATE_PATH = self.root / "state.json"
            cli.DEFAULT_DATASTORE = self.root / "default-store"
            cli.PLIST_PATH = self.root / "LaunchAgents" / "skillskeeper.plist"
            cli.LOG_DIR = self.root / "Logs"
            source_store = self.root / "source-store"
            source_store.mkdir()
            (source_store / "README.md").write_text("source datastore\n", encoding="utf-8")
            dest_store = self.root / "dest-store"
            runtime_root = self.root / "runtime"
            service_bin = runtime_root / ".venv" / "bin" / "skillskeeper"
            service_bin.parent.mkdir(parents=True)
            service_bin.write_text("#!/bin/sh\n", encoding="utf-8")

            with redirect_stdout(StringIO()):
                result = cli.command_install(
                    SimpleNamespace(
                        package=None,
                        runtime_root=str(runtime_root),
                        runtime_python=str(Path("/usr/bin/python3")),
                        replace_runtime=False,
                        skip_runtime_install=True,
                        datastore_path=str(dest_store),
                        datastore_remote=None,
                        migrate_datastore_from=str(source_store),
                        replace_datastore=False,
                        debounce=1.0,
                        no_push=True,
                        load=False,
                    )
                )

            self.assertEqual(result, 0)
            self.assertEqual((dest_store / "README.md").read_text(encoding="utf-8"), "source datastore\n")
            self.assertTrue((dest_store / ".git").exists())
        finally:
            cli.STATE_PATH, cli.DEFAULT_DATASTORE, cli.PLIST_PATH, cli.LOG_DIR = old_paths

    def test_rewrite_skill_name_replaces_frontmatter_name(self) -> None:
        text = "---\nname: old-name\ndescription: Example.\n---\n\n# Old\n"

        rewritten = cli.rewrite_skill_name(text, "keld-old-name")

        self.assertIn("name: keld-old-name", rewritten)
        self.assertNotIn("name: old-name", rewritten)

    def test_validate_skill_dir_requires_description(self) -> None:
        skill_dir = self.root / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: skill\n---\n\n# Skill\n", encoding="utf-8")

        result = cli.validate_skill_dir(skill_dir)

        self.assertFalse(result.ok)
        self.assertIn("frontmatter must include description", result.errors)

    def test_validate_skill_dir_accepts_valid_skill(self) -> None:
        skill_dir = self.make_skill(self.root, "valid-skill", body="# Valid\n\nDo the thing.\n")

        result = cli.validate_skill_dir(skill_dir)

        self.assertTrue(result.ok)
        self.assertEqual(result.name, "valid-skill")

    def test_skill_add_global_validates_installs_and_syncs(self) -> None:
        old_paths = (cli.PROJECTS_SKILLS, cli.sync_all, cli.copy_projects_skills_to_codex)
        try:
            source = self.make_skill(self.root / "source", "source-skill")
            projects_skills = self.root / "Projects" / ".agents" / "skills"
            cli.PROJECTS_SKILLS = projects_skills
            calls: list[str] = []
            cli.sync_all = lambda push=True: (1, False, False)
            cli.copy_projects_skills_to_codex = lambda prefix="keld", state=None: calls.append(prefix) or 1

            with redirect_stdout(StringIO()) as stdout:
                result = cli.command_skill_add(
                    SimpleNamespace(
                        source=str(source),
                        global_skill=True,
                        workspace=None,
                        name="renamed-skill",
                        no_register=False,
                        no_push=True,
                        no_codex_sync=False,
                        codex_prefix="keld",
                    )
                )

            self.assertEqual(result, 0)
            installed = projects_skills / "renamed-skill" / "SKILL.md"
            self.assertTrue(installed.exists())
            self.assertIn("name: renamed-skill", installed.read_text(encoding="utf-8"))
            self.assertEqual(calls, ["keld"])
            self.assertIn("installed:", stdout.getvalue())
        finally:
            cli.PROJECTS_SKILLS, cli.sync_all, cli.copy_projects_skills_to_codex = old_paths

    def test_skill_add_workspace_auto_registers_workspace(self) -> None:
        old_paths = (cli.STATE_PATH, cli.DEFAULT_DATASTORE, cli.sync_all, cli.copy_projects_skills_to_codex)
        try:
            source = self.make_skill(self.root / "source", "workspace-skill")
            workspace = (self.root / "workspace").resolve()
            workspace.mkdir()
            cli.STATE_PATH = self.root / "state.json"
            cli.DEFAULT_DATASTORE = self.root / "store"
            cli.sync_all = lambda push=True: (1, False, False)
            cli.copy_projects_skills_to_codex = lambda prefix="keld", state=None: 0

            with redirect_stdout(StringIO()):
                result = cli.command_skill_add(
                    SimpleNamespace(
                        source=str(source),
                        global_skill=False,
                        workspace=str(workspace),
                        name=None,
                        no_register=False,
                        no_push=True,
                        no_codex_sync=True,
                        codex_prefix="keld",
                    )
                )

            self.assertEqual(result, 0)
            self.assertTrue((workspace / ".agents" / "skills" / "workspace-skill" / "SKILL.md").exists())
            state = cli.read_state()
            self.assertEqual(state["workspaces"], [{"path": str(workspace)}])
        finally:
            (
                cli.STATE_PATH,
                cli.DEFAULT_DATASTORE,
                cli.sync_all,
                cli.copy_projects_skills_to_codex,
            ) = old_paths

    def test_skill_add_refuses_existing_target(self) -> None:
        old_paths = (cli.PROJECTS_SKILLS, cli.sync_all, cli.copy_projects_skills_to_codex)
        try:
            source = self.make_skill(self.root / "source", "existing-skill")
            projects_skills = self.root / "Projects" / ".agents" / "skills"
            self.make_skill(projects_skills, "existing-skill")
            cli.PROJECTS_SKILLS = projects_skills
            cli.sync_all = lambda push=True: (1, False, False)
            cli.copy_projects_skills_to_codex = lambda prefix="keld", state=None: 1

            with self.assertRaises(cli.KeeperError):
                cli.command_skill_add(
                    SimpleNamespace(
                        source=str(source),
                        global_skill=True,
                        workspace=None,
                        name=None,
                        no_register=False,
                        no_push=True,
                        no_codex_sync=True,
                        codex_prefix="keld",
                    )
                )
        finally:
            cli.PROJECTS_SKILLS, cli.sync_all, cli.copy_projects_skills_to_codex = old_paths

    def test_skill_update_replaces_existing_target(self) -> None:
        old_paths = (cli.PROJECTS_SKILLS, cli.sync_all, cli.copy_projects_skills_to_codex)
        try:
            source = self.make_skill(self.root / "source", "replace-me", body="# New\n")
            projects_skills = self.root / "Projects" / ".agents" / "skills"
            self.make_skill(projects_skills, "replace-me", body="# Old\n")
            cli.PROJECTS_SKILLS = projects_skills
            cli.sync_all = lambda push=True: (1, False, False)
            cli.copy_projects_skills_to_codex = lambda prefix="keld", state=None: 1

            with redirect_stdout(StringIO()):
                result = cli.command_skill_update(
                    SimpleNamespace(
                        source=str(source),
                        global_skill=True,
                        workspace=None,
                        name=None,
                        no_register=False,
                        no_push=True,
                        no_codex_sync=True,
                        codex_prefix="keld",
                    )
                )

            self.assertEqual(result, 0)
            updated = (projects_skills / "replace-me" / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("# New", updated)
            self.assertNotIn("# Old", updated)
        finally:
            cli.PROJECTS_SKILLS, cli.sync_all, cli.copy_projects_skills_to_codex = old_paths

    def test_directive_add_and_remove_updates_skill(self) -> None:
        old_paths = (cli.PROJECTS_SKILLS, cli.sync_all, cli.copy_projects_skills_to_codex)
        try:
            projects_skills = self.root / "Projects" / ".agents" / "skills"
            skill = self.make_skill(projects_skills, "directive-skill", body="# Directive Skill\n")
            cli.PROJECTS_SKILLS = projects_skills
            cli.sync_all = lambda push=True: (1, False, False)
            cli.copy_projects_skills_to_codex = lambda prefix="keld", state=None: 1

            with redirect_stdout(StringIO()):
                added = cli.command_skill_directive(
                    SimpleNamespace(
                        directive_command="add",
                        identity="directive-skill",
                        title="Preserve Context",
                        body="Always preserve local context.",
                        body_file=None,
                        global_skill=True,
                        workspace=None,
                        no_register=False,
                        no_push=True,
                        no_codex_sync=True,
                        codex_prefix="keld",
                    )
                )

            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertEqual(added, 0)
            self.assertIn("skillskeeper-directive: preserve-context", text)
            self.assertIn("Always preserve local context.", text)

            with redirect_stdout(StringIO()):
                removed = cli.command_skill_directive(
                    SimpleNamespace(
                        directive_command="remove",
                        identity="directive-skill",
                        title="Preserve Context",
                        global_skill=True,
                        workspace=None,
                        no_register=False,
                        no_push=True,
                        no_codex_sync=True,
                        codex_prefix="keld",
                    )
                )

            self.assertEqual(removed, 0)
            self.assertNotIn("skillskeeper-directive: preserve-context", (skill / "SKILL.md").read_text(encoding="utf-8"))
        finally:
            cli.PROJECTS_SKILLS, cli.sync_all, cli.copy_projects_skills_to_codex = old_paths

    def make_active_datastore_skill(
        self,
        datastore: Path,
        workspace: Path,
        source_kind: str,
        identity: str,
    ) -> Path:
        workspace = cli.resolve_path(workspace)
        skill = self.make_skill(
            datastore / "registered" / cli.workspace_key(workspace) / source_kind,
            identity,
        )
        (skill / ".skillskeeper-source.json").write_text(
            "{}\n",
            encoding="utf-8",
        )
        return skill

    def test_archive_global_skill_removes_matching_codex_mirror(self) -> None:
        old_paths = (cli.STATE_PATH, cli.DEFAULT_DATASTORE, cli.PROJECTS_SKILLS, cli.CODEX_SKILLS, cli.git_commit_all)
        try:
            datastore = self.root / "store"
            projects_root = self.root / "Projects"
            projects_skills = projects_root / ".agents" / "skills"
            codex_skills = self.root / "codex-skills"
            cli.STATE_PATH = self.root / "state.json"
            cli.DEFAULT_DATASTORE = datastore
            cli.PROJECTS_SKILLS = projects_skills
            cli.CODEX_SKILLS = codex_skills
            cli.git_commit_all = lambda _path, _message: False
            self.make_active_datastore_skill(datastore, projects_root, "agents-skills", "global-skill")
            self.make_skill(codex_skills, "keld-global-skill")
            self.make_skill(codex_skills, "keld-other-skill")
            cli.write_state({"version": 1, "datastore": str(datastore), "workspaces": []})

            with redirect_stdout(StringIO()) as stdout:
                result = cli.command_archive_skill(
                    SimpleNamespace(
                        workspace=str(projects_root),
                        source_kind="agents-skills",
                        identity="global-skill",
                        codex_prefix="keld",
                        no_push=True,
                    )
                )

            self.assertEqual(result, 0)
            output = stdout.getvalue()
            self.assertIn("codex mirror status: removed", output)
            self.assertFalse((codex_skills / "keld-global-skill").exists())
            self.assertTrue((codex_skills / "keld-other-skill" / "SKILL.md").exists())
            archived = list(datastore.glob("archived/intentional/*/*/agents-skills/global-skill/SKILL.md"))
            self.assertEqual(len(archived), 1)
        finally:
            cli.STATE_PATH, cli.DEFAULT_DATASTORE, cli.PROJECTS_SKILLS, cli.CODEX_SKILLS, cli.git_commit_all = old_paths

    def test_archive_cli_route_removes_matching_codex_mirror(self) -> None:
        old_paths = (cli.STATE_PATH, cli.DEFAULT_DATASTORE, cli.PROJECTS_SKILLS, cli.CODEX_SKILLS, cli.git_commit_all)
        try:
            datastore = self.root / "store"
            projects_root = self.root / "Projects"
            codex_skills = self.root / "codex-skills"
            cli.STATE_PATH = self.root / "state.json"
            cli.DEFAULT_DATASTORE = datastore
            cli.PROJECTS_SKILLS = projects_root / ".agents" / "skills"
            cli.CODEX_SKILLS = codex_skills
            cli.git_commit_all = lambda _path, _message: False
            self.make_active_datastore_skill(datastore, projects_root, "agents-skills", "global-skill")
            self.make_skill(codex_skills, "keld-global-skill")
            cli.write_state({"version": 1, "datastore": str(datastore), "workspaces": []})

            with redirect_stdout(StringIO()) as stdout:
                result = cli.main(
                    [
                        "archive",
                        str(projects_root),
                        "agents-skills",
                        "global-skill",
                        "--no-push",
                    ]
                )

            self.assertEqual(result, 0)
            output = stdout.getvalue()
            self.assertIn("archived:", output)
            self.assertIn("codex mirror:", output)
            self.assertIn("codex mirror status: removed", output)
            self.assertFalse((codex_skills / "keld-global-skill").exists())
            archived = list(datastore.glob("archived/intentional/*/*/agents-skills/global-skill/SKILL.md"))
            self.assertEqual(len(archived), 1)
        finally:
            cli.STATE_PATH, cli.DEFAULT_DATASTORE, cli.PROJECTS_SKILLS, cli.CODEX_SKILLS, cli.git_commit_all = old_paths

    def test_archive_global_skill_reports_missing_codex_mirror_as_success(self) -> None:
        old_paths = (cli.STATE_PATH, cli.DEFAULT_DATASTORE, cli.PROJECTS_SKILLS, cli.CODEX_SKILLS, cli.git_commit_all)
        try:
            datastore = self.root / "store"
            projects_root = self.root / "Projects"
            cli.STATE_PATH = self.root / "state.json"
            cli.DEFAULT_DATASTORE = datastore
            cli.PROJECTS_SKILLS = projects_root / ".agents" / "skills"
            cli.CODEX_SKILLS = self.root / "codex-skills"
            cli.git_commit_all = lambda _path, _message: False
            self.make_active_datastore_skill(datastore, projects_root, "agents-skills", "global-skill")
            cli.write_state({"version": 1, "datastore": str(datastore), "workspaces": []})

            with redirect_stdout(StringIO()) as stdout:
                result = cli.command_archive_skill(
                    SimpleNamespace(
                        workspace=str(projects_root),
                        source_kind="agents-skills",
                        identity="global-skill",
                        codex_prefix="keld",
                        no_push=True,
                    )
                )

            self.assertEqual(result, 0)
            self.assertIn("codex mirror status: missing", stdout.getvalue())
        finally:
            cli.STATE_PATH, cli.DEFAULT_DATASTORE, cli.PROJECTS_SKILLS, cli.CODEX_SKILLS, cli.git_commit_all = old_paths

    def test_archive_global_skill_honors_custom_codex_prefix(self) -> None:
        old_paths = (cli.STATE_PATH, cli.DEFAULT_DATASTORE, cli.PROJECTS_SKILLS, cli.CODEX_SKILLS, cli.git_commit_all)
        try:
            datastore = self.root / "store"
            projects_root = self.root / "Projects"
            codex_skills = self.root / "codex-skills"
            cli.STATE_PATH = self.root / "state.json"
            cli.DEFAULT_DATASTORE = datastore
            cli.PROJECTS_SKILLS = projects_root / ".agents" / "skills"
            cli.CODEX_SKILLS = codex_skills
            cli.git_commit_all = lambda _path, _message: False
            self.make_active_datastore_skill(datastore, projects_root, "agents-skills", "global-skill")
            self.make_skill(codex_skills, "team-global-skill")
            self.make_skill(codex_skills, "keld-global-skill")
            cli.write_state({"version": 1, "datastore": str(datastore), "workspaces": []})

            with redirect_stdout(StringIO()) as stdout:
                result = cli.command_archive_skill(
                    SimpleNamespace(
                        workspace=str(projects_root),
                        source_kind="agents-skills",
                        identity="global-skill",
                        codex_prefix="team",
                        no_push=True,
                    )
                )

            self.assertEqual(result, 0)
            self.assertIn("codex mirror status: removed", stdout.getvalue())
            self.assertFalse((codex_skills / "team-global-skill").exists())
            self.assertTrue((codex_skills / "keld-global-skill" / "SKILL.md").exists())
        finally:
            cli.STATE_PATH, cli.DEFAULT_DATASTORE, cli.PROJECTS_SKILLS, cli.CODEX_SKILLS, cli.git_commit_all = old_paths

    def test_archive_local_workspace_skill_skips_codex_mirror_removal(self) -> None:
        old_paths = (cli.STATE_PATH, cli.DEFAULT_DATASTORE, cli.PROJECTS_SKILLS, cli.CODEX_SKILLS, cli.git_commit_all)
        try:
            datastore = self.root / "store"
            workspace = self.root / "workspace"
            codex_skills = self.root / "codex-skills"
            cli.STATE_PATH = self.root / "state.json"
            cli.DEFAULT_DATASTORE = datastore
            cli.PROJECTS_SKILLS = self.root / "Projects" / ".agents" / "skills"
            cli.CODEX_SKILLS = codex_skills
            cli.git_commit_all = lambda _path, _message: False
            self.make_active_datastore_skill(datastore, workspace, "agents-skills", "local-skill")
            self.make_skill(codex_skills, "keld-local-skill")
            cli.write_state({"version": 1, "datastore": str(datastore), "workspaces": []})

            with redirect_stdout(StringIO()) as stdout:
                result = cli.command_archive_skill(
                    SimpleNamespace(
                        workspace=str(workspace),
                        source_kind="agents-skills",
                        identity="local-skill",
                        codex_prefix="keld",
                        no_push=True,
                    )
                )

            self.assertEqual(result, 0)
            self.assertIn("codex mirror status: skipped", stdout.getvalue())
            self.assertTrue((codex_skills / "keld-local-skill" / "SKILL.md").exists())
        finally:
            cli.STATE_PATH, cli.DEFAULT_DATASTORE, cli.PROJECTS_SKILLS, cli.CODEX_SKILLS, cli.git_commit_all = old_paths

    def test_archive_failure_does_not_remove_codex_mirror(self) -> None:
        old_paths = (cli.STATE_PATH, cli.DEFAULT_DATASTORE, cli.PROJECTS_SKILLS, cli.CODEX_SKILLS)
        try:
            datastore = self.root / "store"
            projects_root = self.root / "Projects"
            codex_skills = self.root / "codex-skills"
            cli.STATE_PATH = self.root / "state.json"
            cli.DEFAULT_DATASTORE = datastore
            cli.PROJECTS_SKILLS = projects_root / ".agents" / "skills"
            cli.CODEX_SKILLS = codex_skills
            self.make_skill(codex_skills, "keld-global-skill")
            cli.write_state({"version": 1, "datastore": str(datastore), "workspaces": []})

            with self.assertRaises(cli.KeeperError):
                cli.command_archive_skill(
                    SimpleNamespace(
                        workspace=str(projects_root),
                        source_kind="agents-skills",
                        identity="global-skill",
                        codex_prefix="keld",
                        no_push=True,
                    )
                )

            self.assertTrue((codex_skills / "keld-global-skill" / "SKILL.md").exists())
        finally:
            cli.STATE_PATH, cli.DEFAULT_DATASTORE, cli.PROJECTS_SKILLS, cli.CODEX_SKILLS = old_paths

    def write_graph_manifest(self, datastore: Path, payload: dict[str, object]) -> Path:
        manifest = datastore / "skills-library" / "graph" / "skill-graph.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps(payload), encoding="utf-8")
        return manifest

    def valid_graph_payload(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "nodes": [
                {"id": "Research Writer", "type": "profession"},
                {"id": "source-review", "type": "skill"},
            ],
            "edges": [
                {"source": "Research Writer", "target": "source-review", "relationship": "includes"}
            ],
        }

    def test_library_graph_rebuild_cli_reports_manifest_hash_without_cache_write(self) -> None:
        old_paths = (cli.STATE_PATH, cli.DEFAULT_DATASTORE)
        try:
            datastore = self.root / "store"
            cli.STATE_PATH = self.root / "state.json"
            cli.DEFAULT_DATASTORE = datastore
            self.write_graph_manifest(datastore, self.valid_graph_payload())
            cli.write_state({"version": 1, "datastore": str(datastore), "workspaces": []})

            with redirect_stdout(StringIO()) as stdout:
                result = cli.main(["library", "graph", "rebuild"])

            output = stdout.getvalue()
            self.assertEqual(result, 0)
            self.assertIn("nodes: 2", output)
            self.assertIn("edges: 1", output)
            self.assertIn("manifest hash:", output)
            self.assertIn("cache written: false", output)
            self.assertFalse((datastore / "skills-library" / "graph" / "index.kuzu").exists())
        finally:
            cli.STATE_PATH, cli.DEFAULT_DATASTORE = old_paths

    def test_library_graph_rebuild_cli_reports_validation_errors(self) -> None:
        old_paths = (cli.STATE_PATH, cli.DEFAULT_DATASTORE)
        try:
            datastore = self.root / "store"
            payload = self.valid_graph_payload()
            payload["edges"] = [{"source": "Research Writer", "target": "missing", "relationship": "includes"}]
            cli.STATE_PATH = self.root / "state.json"
            cli.DEFAULT_DATASTORE = datastore
            self.write_graph_manifest(datastore, payload)
            cli.write_state({"version": 1, "datastore": str(datastore), "workspaces": []})

            with redirect_stderr(StringIO()) as stderr:
                result = cli.main(["library", "graph", "rebuild"])

            self.assertEqual(result, 1)
            self.assertIn("graph manifest validation failed", stderr.getvalue())
            self.assertIn("unknown target node 'missing'", stderr.getvalue())
            self.assertFalse((datastore / "skills-library" / "graph" / "index.kuzu").exists())
        finally:
            cli.STATE_PATH, cli.DEFAULT_DATASTORE = old_paths

    def test_library_graph_status_cli_reports_valid_manifest(self) -> None:
        old_paths = (cli.STATE_PATH, cli.DEFAULT_DATASTORE)
        try:
            datastore = self.root / "store"
            cli.STATE_PATH = self.root / "state.json"
            cli.DEFAULT_DATASTORE = datastore
            self.write_graph_manifest(datastore, self.valid_graph_payload())
            cli.write_state({"version": 1, "datastore": str(datastore), "workspaces": []})

            with redirect_stdout(StringIO()) as stdout:
                result = cli.main(["library", "graph", "status"])

            self.assertEqual(result, 0)
            self.assertIn("status: valid", stdout.getvalue())
            self.assertIn("manifest hash:", stdout.getvalue())
        finally:
            cli.STATE_PATH, cli.DEFAULT_DATASTORE = old_paths


if __name__ == "__main__":
    unittest.main()
