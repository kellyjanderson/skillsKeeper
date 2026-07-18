from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from skills_keeper import checkout, cli, graph


class CheckoutLockfileTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def make_skill(self, name: str, body: str = "# Skill\n") -> Path:
        return self.make_skill_at(self.root, name, body=body)

    def make_skill_at(self, root: Path, name: str, body: str = "# Skill\n") -> Path:
        skill_dir = root / name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Fixture skill for tests.\n---\n\n{body}",
            encoding="utf-8",
        )
        return skill_dir

    def write_graph_manifest(self, datastore: Path, skill_id: str = "source-review") -> Path:
        path = graph.default_manifest_path(datastore)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "nodes": [{"id": skill_id, "type": "skill", "source": f"skills/{skill_id}"}],
                    "edges": [],
                }
            ),
            encoding="utf-8",
        )
        return path

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

    def test_checkout_skill_cli_materializes_skill_and_records_lockfile(self) -> None:
        old_paths = (cli.STATE_PATH, cli.DEFAULT_DATASTORE)
        try:
            datastore = self.root / "store"
            workspace = self.root / "workspace"
            self.make_skill_at(datastore / "skills-library" / "skills", "source-review")
            self.write_graph_manifest(datastore)
            cli.STATE_PATH = self.root / "state.json"
            cli.DEFAULT_DATASTORE = datastore
            cli.write_state({"version": 1, "datastore": str(datastore), "workspaces": []})

            with redirect_stdout(StringIO()) as stdout:
                result = cli.main(["checkout", "skill", "source-review", "--workspace", str(workspace)])

            self.assertEqual(result, 0)
            output = stdout.getvalue()
            self.assertIn("skill: source-review", output)
            self.assertIn("status: checked-out", output)
            self.assertTrue((workspace / ".agents" / "skills" / "source-review" / "SKILL.md").exists())
            lockfile = checkout.load_lockfile(workspace)
            self.assertEqual(len(lockfile.entries), 1)
            self.assertEqual(lockfile.entries[0].ownership_class, "library")
            self.assertEqual(lockfile.entries[0].materialized_path, ".agents/skills/source-review")
        finally:
            cli.STATE_PATH, cli.DEFAULT_DATASTORE = old_paths

    def test_checkout_skill_refuses_dirty_existing_target(self) -> None:
        datastore = self.root / "store"
        workspace = self.root / "workspace"
        self.make_skill_at(datastore / "skills-library" / "skills", "source-review", body="# Clean\n")
        self.write_graph_manifest(datastore)
        target = self.make_skill_at(workspace / ".agents" / "skills", "source-review", body="# Local edit\n")

        with self.assertRaisesRegex(checkout.CheckoutLockfileError, "local changes"):
            checkout.checkout_skill(workspace, "source-review", datastore)

        self.assertIn("# Local edit", (target / "SKILL.md").read_text(encoding="utf-8"))
        self.assertFalse(checkout.lockfile_path(workspace).exists())

    def test_checkout_skill_invalid_source_does_not_leave_partial_active_copy(self) -> None:
        datastore = self.root / "store"
        workspace = self.root / "workspace"
        self.write_graph_manifest(datastore)

        with self.assertRaisesRegex(checkout.CheckoutLockfileError, "library skill source is not a directory"):
            checkout.checkout_skill(workspace, "source-review", datastore)

        self.assertFalse((workspace / ".agents" / "skills" / "source-review").exists())

    def test_checkout_skill_cli_reports_invalid_graph_without_materializing(self) -> None:
        old_paths = (cli.STATE_PATH, cli.DEFAULT_DATASTORE)
        try:
            datastore = self.root / "store"
            workspace = self.root / "workspace"
            self.make_skill_at(datastore / "skills-library" / "skills", "source-review")
            path = graph.default_manifest_path(datastore)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "nodes": [{"id": "source-review", "type": "skill"}],
                        "edges": [{"source": "source-review", "target": "missing", "relationship": "requires"}],
                    }
                ),
                encoding="utf-8",
            )
            cli.STATE_PATH = self.root / "state.json"
            cli.DEFAULT_DATASTORE = datastore
            cli.write_state({"version": 1, "datastore": str(datastore), "workspaces": []})

            with redirect_stderr(StringIO()) as stderr:
                result = cli.main(["checkout", "skill", "source-review", "--workspace", str(workspace)])

            self.assertEqual(result, 1)
            self.assertIn("graph manifest validation failed", stderr.getvalue())
            self.assertFalse((workspace / ".agents" / "skills" / "source-review").exists())
        finally:
            cli.STATE_PATH, cli.DEFAULT_DATASTORE = old_paths


if __name__ == "__main__":
    unittest.main()
