from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from skills_keeper import checkout


class CheckoutLockfileTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def make_skill(self, name: str, body: str = "# Skill\n") -> Path:
        skill_dir = self.root / name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Fixture skill for tests.\n---\n\n{body}",
            encoding="utf-8",
        )
        return skill_dir

    def entry(self, materialized_path: str = ".agents/skills/source-review") -> checkout.CheckoutEntry:
        return checkout.CheckoutEntry(
            skill_id="source-review",
            source_hash="sha256:" + ("a" * 64),
            graph_path=("Research-Writer", "source-review"),
            materialized_path=materialized_path,
            ownership_class="library",
            selected_by=("Research-Writer",),
        )

    def test_missing_lockfile_loads_empty_workspace_lockfile(self) -> None:
        workspace = self.root / "workspace"

        lockfile = checkout.load_lockfile(workspace)

        self.assertEqual(lockfile.workspace, str(workspace.resolve()))
        self.assertEqual(lockfile.schema_version, 1)
        self.assertEqual(lockfile.entries, ())

    def test_lockfile_round_trips_with_stable_entry_order(self) -> None:
        workspace = self.root / "workspace"
        lockfile = checkout.CheckoutLockfile(
            workspace=str(workspace),
            roots=("Research-Writer",),
            entries=(
                self.entry(".agents/skills/z-review"),
                checkout.CheckoutEntry(
                    skill_id="drafting",
                    source_hash="sha256:" + ("b" * 64),
                    graph_path=("Research-Writer", "drafting"),
                    materialized_path=".agents/skills/drafting",
                ),
            ),
        )

        checkout.write_lockfile(workspace, lockfile)
        loaded = checkout.load_lockfile(workspace)

        self.assertEqual([entry.materialized_path for entry in loaded.entries], [".agents/skills/drafting", ".agents/skills/z-review"])
        raw = json.loads(checkout.lockfile_path(workspace).read_text(encoding="utf-8"))
        self.assertEqual(raw["version"], 1)
        self.assertEqual(raw["roots"], ["Research-Writer"])
        self.assertEqual(raw["checkouts"][0]["skill_id"], "drafting")

    def test_hash_skill_source_changes_when_content_changes(self) -> None:
        skill_dir = self.make_skill("source-review", body="# One\n")
        first = checkout.hash_skill_source(skill_dir)

        (skill_dir / "SKILL.md").write_text(
            "---\nname: source-review\ndescription: Fixture skill for tests.\n---\n\n# Two\n",
            encoding="utf-8",
        )
        second = checkout.hash_skill_source(skill_dir)

        self.assertTrue(first.startswith("sha256:"))
        self.assertNotEqual(first, second)

    def test_hash_skill_source_ignores_runtime_state_files(self) -> None:
        skill_dir = self.make_skill("source-review")
        first = checkout.hash_skill_source(skill_dir)

        (skill_dir / ".composer-state.json").write_text('{"runtime": true}\n', encoding="utf-8")
        (skill_dir / ".system-skills-composer.json").write_text('{"runtime": true}\n', encoding="utf-8")
        (skill_dir / "__pycache__").mkdir()
        (skill_dir / "__pycache__" / "ignored.pyc").write_bytes(b"ignored")
        second = checkout.hash_skill_source(skill_dir)

        self.assertEqual(first, second)

    def test_invalid_lockfile_fails_clearly(self) -> None:
        workspace = self.root / "workspace"
        path = checkout.lockfile_path(workspace)
        path.parent.mkdir(parents=True)
        path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "workspace": str(workspace),
                    "checkouts": [
                        {
                            "skill_id": "Source Review",
                            "source_hash": "sha256:bad",
                            "graph_path": ["Research Writer"],
                            "materialized_path": "/tmp/source-review",
                            "ownership_class": "library",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        with self.assertRaises(checkout.CheckoutLockfileError) as context:
            checkout.load_lockfile(workspace)

        message = str(context.exception)
        self.assertIn("skill_id must be normalized", message)
        self.assertIn("source_hash must be sha256", message)
        self.assertIn("materialized_path must be a safe relative path", message)

    def test_write_lockfile_rejects_duplicate_materialized_paths(self) -> None:
        workspace = self.root / "workspace"
        lockfile = checkout.CheckoutLockfile(
            workspace=str(workspace),
            entries=(
                self.entry(),
                checkout.CheckoutEntry(
                    skill_id="drafting",
                    source_hash="sha256:" + ("b" * 64),
                    graph_path=("Research-Writer", "drafting"),
                    materialized_path=".agents/skills/source-review",
                ),
            ),
        )

        with self.assertRaisesRegex(checkout.CheckoutLockfileError, "materialized_path duplicates"):
            checkout.write_lockfile(workspace, lockfile)


if __name__ == "__main__":
    unittest.main()
