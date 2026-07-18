from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from skills_keeper import graph


class GraphManifestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write_manifest(self, payload: dict[str, object]) -> Path:
        path = self.root / "skill-graph.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def write_datastore_manifest(self, datastore: Path, payload: dict[str, object]) -> Path:
        path = graph.default_manifest_path(datastore)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def valid_payload(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "nodes": [
                {"id": "Research Writer", "type": "profession", "label": "Research writer"},
                {"id": "source-review", "type": "skill"},
            ],
            "edges": [
                {"source": "Research Writer", "target": "source-review", "relationship": "includes"}
            ],
        }

    def test_valid_manifest_normalizes_ids_and_hashes_stably(self) -> None:
        manifest = graph.load_manifest(self.write_manifest(self.valid_payload()))

        errors = graph.validate_manifest(manifest)
        normalized = graph.normalize_manifest(manifest)

        self.assertEqual(errors, [])
        self.assertEqual([node.id for node in normalized.nodes], ["Research-Writer", "source-review"])
        self.assertEqual(len(graph.manifest_hash(manifest)), 64)
        self.assertEqual(graph.manifest_hash(manifest), graph.manifest_hash(normalized))

    def test_duplicate_normalized_ids_are_validation_errors(self) -> None:
        payload = self.valid_payload()
        payload["nodes"] = [
            {"id": "Source Review", "type": "skill"},
            {"id": "Source-Review", "type": "skill"},
        ]
        payload["edges"] = []
        manifest = graph.load_manifest(self.write_manifest(payload))

        errors = graph.validate_manifest(manifest)

        self.assertIn("duplicate normalized node id 'Source-Review'", "; ".join(error.format() for error in errors))

    def test_missing_target_is_validation_error(self) -> None:
        payload = self.valid_payload()
        payload["edges"] = [{"source": "Research Writer", "target": "missing", "relationship": "includes"}]
        manifest = graph.load_manifest(self.write_manifest(payload))

        errors = graph.validate_manifest(manifest)

        self.assertIn("unknown target node 'missing'", "; ".join(error.format() for error in errors))

    def test_unknown_node_type_is_validation_error(self) -> None:
        payload = self.valid_payload()
        payload["nodes"] = [{"id": "source-review", "type": "unknown"}]
        payload["edges"] = []
        manifest = graph.load_manifest(self.write_manifest(payload))

        errors = graph.validate_manifest(manifest)

        self.assertIn("unknown node type 'unknown'", "; ".join(error.format() for error in errors))

    def test_unknown_relationship_is_validation_error(self) -> None:
        payload = self.valid_payload()
        payload["edges"] = [{"source": "Research Writer", "target": "source-review", "relationship": "owns"}]
        manifest = graph.load_manifest(self.write_manifest(payload))

        errors = graph.validate_manifest(manifest)

        self.assertIn("unknown relationship 'owns'", "; ".join(error.format() for error in errors))

    def test_load_manifest_rejects_non_integer_schema_version(self) -> None:
        payload = self.valid_payload()
        payload["schema_version"] = "abc"

        with self.assertRaisesRegex(graph.GraphManifestError, "schema_version must be an integer"):
            graph.load_manifest(self.write_manifest(payload))

    def test_cycle_validation_terminates_with_clear_error(self) -> None:
        payload = {
            "schema_version": 1,
            "nodes": [
                {"id": "alpha", "type": "skill"},
                {"id": "beta", "type": "skill"},
            ],
            "edges": [
                {"source": "alpha", "target": "beta", "relationship": "requires"},
                {"source": "beta", "target": "alpha", "relationship": "requires"},
            ],
        }
        manifest = graph.load_manifest(self.write_manifest(payload))

        errors = graph.validate_manifest(manifest)

        self.assertIn("cycle detected", "; ".join(error.format() for error in errors))

    def traversal_payload(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "nodes": [
                {"id": "Research Writer", "type": "profession"},
                {"id": "writer-index", "type": "index"},
                {"id": "drafting", "type": "skill"},
                {"id": "review", "type": "skill"},
                {"id": "legacy-review", "type": "skill"},
            ],
            "edges": [
                {"source": "Research Writer", "target": "writer-index", "relationship": "includes"},
                {"source": "writer-index", "target": "drafting", "relationship": "requires"},
                {"source": "writer-index", "target": "review", "relationship": "recommends"},
                {"source": "Research Writer", "target": "legacy-review", "relationship": "conflicts"},
            ],
        }

    def test_resolve_top_down_returns_skills_paths_and_conflicts(self) -> None:
        manifest = graph.load_manifest(self.write_manifest(self.traversal_payload()))

        result = graph.resolve_top_down(manifest, "Research Writer")

        self.assertEqual(result.resolved_ids, ("drafting", "review"))
        self.assertEqual([path.skill_id for path in result.paths], ["drafting", "review"])
        self.assertEqual([edge.target for edge in result.paths[0].edges], ["writer-index", "drafting"])
        self.assertEqual(len(result.conflicts), 1)
        self.assertEqual(result.conflicts[0].target, "legacy-review")

    def test_resolve_bottom_up_reports_affected_roots(self) -> None:
        manifest = graph.load_manifest(self.write_manifest(self.traversal_payload()))

        result = graph.resolve_bottom_up(manifest, "drafting")

        self.assertEqual(result.affected_roots, ("writer-index", "Research-Writer"))
        self.assertEqual([path.root_id for path in result.paths], ["writer-index", "Research-Writer"])
        self.assertEqual([edge.source for edge in result.paths[-1].edges], ["Research-Writer", "writer-index"])

    def test_resolve_top_down_missing_root_is_explicit(self) -> None:
        manifest = graph.load_manifest(self.write_manifest(self.traversal_payload()))

        with self.assertRaisesRegex(graph.GraphManifestError, "root node does not exist"):
            graph.resolve_top_down(manifest, "missing-root")

    def test_detect_traversal_cycle_returns_diagnostic(self) -> None:
        payload = {
            "schema_version": 1,
            "nodes": [
                {"id": "alpha", "type": "skill"},
                {"id": "beta", "type": "skill"},
            ],
            "edges": [
                {"source": "alpha", "target": "beta", "relationship": "requires"},
                {"source": "beta", "target": "alpha", "relationship": "requires"},
            ],
        }
        manifest = graph.load_manifest(self.write_manifest(payload))

        self.assertEqual(graph.detect_traversal_cycle(manifest, "alpha"), ["alpha -> beta -> alpha"])

    def test_cache_status_is_fresh_after_metadata_write(self) -> None:
        datastore = self.root / "store"
        manifest_path = self.write_datastore_manifest(datastore, self.valid_payload())
        manifest = graph.load_manifest(manifest_path)

        metadata = graph.write_cache_metadata(datastore, manifest, manifest_path=manifest_path)
        status = graph.graph_cache_status(datastore)

        self.assertTrue(graph.default_cache_metadata_path(datastore).exists())
        self.assertEqual(status.status, "fresh")
        self.assertEqual(status.manifest_hash, metadata.manifest_hash)
        self.assertEqual(status.cached_manifest_hash, metadata.manifest_hash)

    def test_cache_status_is_missing_without_metadata(self) -> None:
        datastore = self.root / "store"
        self.write_datastore_manifest(datastore, self.valid_payload())

        status = graph.graph_cache_status(datastore)

        self.assertEqual(status.status, "missing")
        self.assertIn("missing", status.message)
        self.assertIsNotNone(status.manifest_hash)

    def test_cache_status_is_stale_when_manifest_hash_changes(self) -> None:
        datastore = self.root / "store"
        manifest_path = self.write_datastore_manifest(datastore, self.valid_payload())
        graph.write_cache_metadata(datastore, graph.load_manifest(manifest_path), manifest_path=manifest_path)
        changed = self.valid_payload()
        changed["nodes"] = [
            {"id": "Research Writer", "type": "profession", "label": "Changed"},
            {"id": "source-review", "type": "skill"},
        ]
        self.write_datastore_manifest(datastore, changed)

        status = graph.graph_cache_status(datastore)

        self.assertEqual(status.status, "stale")
        self.assertIsNotNone(status.cached_manifest_hash)
        self.assertNotEqual(status.manifest_hash, status.cached_manifest_hash)

    def test_cache_status_is_invalid_when_metadata_is_invalid(self) -> None:
        datastore = self.root / "store"
        self.write_datastore_manifest(datastore, self.valid_payload())
        metadata_path = graph.default_cache_metadata_path(datastore)
        metadata_path.parent.mkdir(parents=True)
        metadata_path.write_text("{", encoding="utf-8")

        status = graph.graph_cache_status(datastore)

        self.assertEqual(status.status, "invalid")
        self.assertIn("cache metadata is not valid JSON", status.message)


if __name__ == "__main__":
    unittest.main()
