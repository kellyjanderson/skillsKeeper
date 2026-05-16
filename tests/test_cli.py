from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from skills_keeper import cli


class SkillsKeeperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def make_skill(self, root: Path, name: str, body: str = "# Skill\n") -> Path:
        skill_dir = root / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Test skill.\n---\n\n{body}",
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

    def test_rewrite_skill_name_replaces_frontmatter_name(self) -> None:
        text = "---\nname: old-name\ndescription: Example.\n---\n\n# Old\n"

        rewritten = cli.rewrite_skill_name(text, "keld-old-name")

        self.assertIn("name: keld-old-name", rewritten)
        self.assertNotIn("name: old-name", rewritten)


if __name__ == "__main__":
    unittest.main()
