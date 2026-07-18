from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .ids import skill_identity


GRAPH_ROOT = Path("skills-library") / "graph"
GRAPH_MANIFEST_FILENAME = "skill-graph.json"
NODE_TYPES = {"skill", "index", "profession", "context", "phase", "standard"}
EDGE_TYPES = {"includes", "requires", "recommends", "extends", "conflicts", "replaces"}
ACYCLIC_EDGE_TYPES = {"includes", "requires", "extends", "replaces"}
TOP_DOWN_EDGE_TYPES = ("includes", "requires", "recommends", "extends")
CONFLICT_EDGE_TYPES = {"conflicts", "replaces"}


class GraphManifestError(Exception):
    pass


@dataclass(frozen=True)
class GraphValidationError:
    path: str
    message: str

    def format(self) -> str:
        return f"{self.path}: {self.message}"


@dataclass(frozen=True)
class GraphNode:
    id: str
    type: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str
    relationship: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphManifest:
    schema_version: int
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]


@dataclass(frozen=True)
class TraversalPath:
    root_id: str
    skill_id: str
    edges: tuple[GraphEdge, ...]


@dataclass(frozen=True)
class TraversalResult:
    root_id: str
    resolved_ids: tuple[str, ...] = ()
    affected_roots: tuple[str, ...] = ()
    paths: tuple[TraversalPath, ...] = ()
    conflicts: tuple[GraphEdge, ...] = ()
    errors: tuple[str, ...] = ()


def default_manifest_path(datastore: Path) -> Path:
    return datastore / GRAPH_ROOT / GRAPH_MANIFEST_FILENAME


def load_manifest(path: Path) -> GraphManifest:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise GraphManifestError(f"manifest does not exist: {path}") from error
    except json.JSONDecodeError as error:
        raise GraphManifestError(f"manifest is not valid JSON: {error}") from error
    except OSError as error:
        raise GraphManifestError(f"failed to read manifest: {error}") from error
    if not isinstance(raw, dict):
        raise GraphManifestError("manifest root must be an object")
    version = raw.get("schema_version", raw.get("schemaVersion", 1))
    nodes = raw.get("nodes", [])
    edges = raw.get("edges", [])
    if not isinstance(nodes, list):
        raise GraphManifestError("nodes must be a list")
    if not isinstance(edges, list):
        raise GraphManifestError("edges must be a list")
    return GraphManifest(
        schema_version=int(version),
        nodes=tuple(_node_from_raw(item, index) for index, item in enumerate(nodes)),
        edges=tuple(_edge_from_raw(item, index) for index, item in enumerate(edges)),
    )


def validate_manifest(manifest: GraphManifest) -> list[GraphValidationError]:
    errors: list[GraphValidationError] = []
    seen: dict[str, int] = {}
    normalized_ids: set[str] = set()
    for index, node in enumerate(manifest.nodes):
        node_path = f"nodes[{index}]"
        normalized = skill_identity(node.id)
        if not node.id:
            errors.append(GraphValidationError(f"{node_path}.id", "node id is required"))
        if normalized in seen:
            errors.append(
                GraphValidationError(
                    f"{node_path}.id",
                    f"duplicate normalized node id {normalized!r}; first seen at nodes[{seen[normalized]}]",
                )
            )
        seen.setdefault(normalized, index)
        normalized_ids.add(normalized)
        if node.type not in NODE_TYPES:
            errors.append(GraphValidationError(f"{node_path}.type", f"unknown node type {node.type!r}"))
    for index, edge in enumerate(manifest.edges):
        edge_path = f"edges[{index}]"
        source = skill_identity(edge.source)
        target = skill_identity(edge.target)
        if not edge.source:
            errors.append(GraphValidationError(f"{edge_path}.source", "edge source is required"))
        elif source not in normalized_ids:
            errors.append(GraphValidationError(f"{edge_path}.source", f"unknown source node {edge.source!r}"))
        if not edge.target:
            errors.append(GraphValidationError(f"{edge_path}.target", "edge target is required"))
        elif target not in normalized_ids:
            errors.append(GraphValidationError(f"{edge_path}.target", f"unknown target node {edge.target!r}"))
        if edge.relationship not in EDGE_TYPES:
            errors.append(
                GraphValidationError(
                    f"{edge_path}.relationship",
                    f"unknown relationship {edge.relationship!r}",
                )
            )
    errors.extend(_cycle_errors(manifest))
    return errors


def normalize_manifest(manifest: GraphManifest) -> GraphManifest:
    nodes = tuple(
        sorted(
            (
                GraphNode(skill_identity(node.id), node.type, dict(sorted(node.metadata.items())))
                for node in manifest.nodes
            ),
            key=lambda node: (node.id, node.type),
        )
    )
    edges = tuple(
        sorted(
            (
                GraphEdge(
                    skill_identity(edge.source),
                    skill_identity(edge.target),
                    edge.relationship,
                    dict(sorted(edge.metadata.items())),
                )
                for edge in manifest.edges
            ),
            key=lambda edge: (edge.source, edge.relationship, edge.target),
        )
    )
    return GraphManifest(manifest.schema_version, nodes, edges)


def manifest_hash(manifest: GraphManifest) -> str:
    normalized = normalize_manifest(manifest)
    payload = json.dumps(manifest_to_dict(normalized), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def manifest_to_dict(manifest: GraphManifest) -> dict[str, Any]:
    return {
        "schema_version": manifest.schema_version,
        "nodes": [
            {"id": node.id, "type": node.type, **node.metadata}
            for node in manifest.nodes
        ],
        "edges": [
            {
                "source": edge.source,
                "target": edge.target,
                "relationship": edge.relationship,
                **edge.metadata,
            }
            for edge in manifest.edges
        ],
    }


def resolve_top_down(manifest: GraphManifest, root_id: str) -> TraversalResult:
    normalized = _valid_normalized_manifest(manifest)
    root = skill_identity(root_id)
    nodes = _node_map(normalized)
    if root not in nodes:
        raise GraphManifestError(f"root node does not exist: {root_id}")
    outgoing = _outgoing_edges(normalized)
    cycles = tuple(detect_traversal_cycle(normalized, root))
    queue: list[tuple[str, tuple[GraphEdge, ...]]] = [(root, ())]
    visited: set[str] = set()
    resolved: list[str] = []
    paths: list[TraversalPath] = []
    conflicts: list[GraphEdge] = []
    conflict_keys: set[tuple[str, str, str]] = set()
    while queue:
        current, path_edges = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        node = nodes[current]
        if node.type == "skill" and current not in resolved:
            resolved.append(current)
            paths.append(TraversalPath(root, current, path_edges))
        for edge in outgoing.get(current, []):
            if edge.relationship in CONFLICT_EDGE_TYPES:
                key = (edge.source, edge.relationship, edge.target)
                if key not in conflict_keys:
                    conflicts.append(edge)
                    conflict_keys.add(key)
            if edge.relationship in TOP_DOWN_EDGE_TYPES:
                queue.append((edge.target, (*path_edges, edge)))
    return TraversalResult(
        root_id=root,
        resolved_ids=tuple(resolved),
        paths=tuple(paths),
        conflicts=tuple(conflicts),
        errors=cycles,
    )


def resolve_bottom_up(manifest: GraphManifest, skill_id: str) -> TraversalResult:
    normalized = _valid_normalized_manifest(manifest)
    skill = skill_identity(skill_id)
    nodes = _node_map(normalized)
    if skill not in nodes:
        raise GraphManifestError(f"skill node does not exist: {skill_id}")
    incoming = _incoming_edges(normalized)
    queue: list[tuple[str, tuple[GraphEdge, ...]]] = [(skill, ())]
    visited: set[str] = set()
    roots: list[str] = []
    paths: list[TraversalPath] = []
    conflicts: list[GraphEdge] = []
    conflict_keys: set[tuple[str, str, str]] = set()
    while queue:
        current, path_edges = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        for edge in incoming.get(current, []):
            if edge.relationship in TOP_DOWN_EDGE_TYPES:
                next_path = (edge, *path_edges)
                source_node = nodes[edge.source]
                if source_node.type != "skill" and edge.source not in roots:
                    roots.append(edge.source)
                    paths.append(TraversalPath(edge.source, skill, next_path))
                queue.append((edge.source, next_path))
            elif edge.relationship in CONFLICT_EDGE_TYPES:
                key = (edge.source, edge.relationship, edge.target)
                if key not in conflict_keys:
                    conflicts.append(edge)
                    conflict_keys.add(key)
    return TraversalResult(
        root_id=skill,
        affected_roots=tuple(roots),
        paths=tuple(paths),
        conflicts=tuple(conflicts),
    )


def detect_traversal_cycle(manifest: GraphManifest, start_id: str) -> list[str]:
    normalized = _normalize_for_traversal(manifest)
    start = skill_identity(start_id)
    outgoing = _outgoing_edges(normalized)
    cycles: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, path: tuple[str, ...]) -> None:
        if node in visiting:
            cycle_start = path.index(node) if node in path else 0
            cycles.append(" -> ".join(path[cycle_start:]))
            return
        if node in visited:
            return
        visiting.add(node)
        for edge in outgoing.get(node, []):
            if edge.relationship in TOP_DOWN_EDGE_TYPES:
                visit(edge.target, (*path, edge.target))
        visiting.remove(node)
        visited.add(node)

    visit(start, (start,))
    return cycles


def _node_from_raw(item: Any, index: int) -> GraphNode:
    if not isinstance(item, dict):
        raise GraphManifestError(f"nodes[{index}] must be an object")
    metadata = {key: value for key, value in item.items() if key not in {"id", "type"}}
    return GraphNode(str(item.get("id", "")), str(item.get("type", "")), metadata)


def _edge_from_raw(item: Any, index: int) -> GraphEdge:
    if not isinstance(item, dict):
        raise GraphManifestError(f"edges[{index}] must be an object")
    relationship = item.get("relationship", item.get("type", ""))
    metadata = {key: value for key, value in item.items() if key not in {"source", "target", "relationship", "type"}}
    return GraphEdge(str(item.get("source", "")), str(item.get("target", "")), str(relationship), metadata)


def _valid_normalized_manifest(manifest: GraphManifest) -> GraphManifest:
    errors = validate_manifest(manifest)
    if errors:
        raise GraphManifestError("; ".join(error.format() for error in errors))
    return _normalize_for_traversal(manifest)


def _normalize_for_traversal(manifest: GraphManifest) -> GraphManifest:
    nodes = tuple(
        GraphNode(skill_identity(node.id), node.type, dict(node.metadata))
        for node in manifest.nodes
    )
    edges = tuple(
        GraphEdge(
            skill_identity(edge.source),
            skill_identity(edge.target),
            edge.relationship,
            dict(edge.metadata),
        )
        for edge in manifest.edges
    )
    return GraphManifest(manifest.schema_version, nodes, edges)


def _node_map(manifest: GraphManifest) -> dict[str, GraphNode]:
    return {node.id: node for node in manifest.nodes}


def _outgoing_edges(manifest: GraphManifest) -> dict[str, list[GraphEdge]]:
    relationship_order = {relationship: index for index, relationship in enumerate(TOP_DOWN_EDGE_TYPES)}
    result: dict[str, list[GraphEdge]] = {}
    for edge in manifest.edges:
        result.setdefault(edge.source, []).append(edge)
        result[edge.source].sort(key=lambda item: relationship_order.get(item.relationship, 99))
    return result


def _incoming_edges(manifest: GraphManifest) -> dict[str, list[GraphEdge]]:
    relationship_order = {relationship: index for index, relationship in enumerate(TOP_DOWN_EDGE_TYPES)}
    result: dict[str, list[GraphEdge]] = {}
    for edge in manifest.edges:
        result.setdefault(edge.target, []).append(edge)
        result[edge.target].sort(key=lambda item: relationship_order.get(item.relationship, 99))
    return result


def _cycle_errors(manifest: GraphManifest) -> list[GraphValidationError]:
    adjacency: dict[str, list[str]] = {}
    for edge in manifest.edges:
        if edge.relationship in ACYCLIC_EDGE_TYPES:
            adjacency.setdefault(skill_identity(edge.source), []).append(skill_identity(edge.target))
    errors: list[GraphValidationError] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, path: tuple[str, ...]) -> None:
        if node in visiting:
            cycle_start = path.index(node) if node in path else 0
            cycle = " -> ".join(path[cycle_start:])
            errors.append(GraphValidationError("edges", f"cycle detected: {cycle}"))
            return
        if node in visited:
            return
        visiting.add(node)
        for target in adjacency.get(node, []):
            visit(target, (*path, target))
        visiting.remove(node)
        visited.add(node)

    for node in sorted(adjacency):
        visit(node, (node,))
    return errors
