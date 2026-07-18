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


if __name__ == "__main__":
    unittest.main()
