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

    def test_rewrite_skill_name_replaces_frontmatter_name(self) -> None:
        text = "---\nname: old-name\ndescription: Example.\n---\n\n# Old\n"

        rewritten = cli.rewrite_skill_name(text, "keld-old-name")

        self.assertIn("name: keld-old-name", rewritten)
        self.assertNotIn("name: old-name", rewritten)


if __name__ == "__main__":
    unittest.main()
