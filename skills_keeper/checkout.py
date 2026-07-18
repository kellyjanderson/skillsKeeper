from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .graph import GraphManifest, GraphManifestError, default_manifest_path, load_manifest, resolve_top_down, validate_manifest
from .ids import skill_identity


LOCKFILE_VERSION = 1
LOCKFILE_RELATIVE_PATH = Path(".agents") / "skillskeeper-lock.json"
ACTIVE_SKILLS_RELATIVE_PATH = Path(".agents") / "skills"
LIBRARY_ROOT = Path("skills-library")
OWNERSHIP_CLASSES = {"library", "project-owned", "fully-managed-local", "global-managed"}
HASH_SKIP_NAMES = {
    ".DS_Store",
    ".composer-state.json",
    ".system-skills-composer.json",
    "__pycache__",
}


class CheckoutLockfileError(Exception):
    pass


@dataclass(frozen=True)
class CheckoutEntry:
    skill_id: str
    source_hash: str
    graph_path: tuple[str, ...]
    materialized_path: str
    ownership_class: str = "library"
    selected_by: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CheckoutLockfile:
    workspace: str
    schema_version: int = LOCKFILE_VERSION
    roots: tuple[str, ...] = ()
    entries: tuple[CheckoutEntry, ...] = ()


@dataclass(frozen=True)
class CheckoutResult:
    skill_id: str
    source_path: Path
    materialized_path: Path
    lockfile_path: Path
    source_hash: str
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class CheckoutPlanItem:
    entry: CheckoutEntry
    source_path: Path
    target_path: Path


@dataclass(frozen=True)
class CheckoutPlan:
    root_id: str
    items: tuple[CheckoutPlanItem, ...]


@dataclass(frozen=True)
class CheckoutTreeResult:
    root_id: str
    materialized_paths: tuple[Path, ...]
    lockfile_path: Path
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class CheckoutEntryStatus:
    skill_id: str
    status: str
    materialized_path: Path
    source_path: Path
    pinned_hash: str
    active_hash: str | None = None
    source_hash: str | None = None
    message: str = ""


@dataclass(frozen=True)
class CheckoutStatus:
    workspace: Path
    lockfile_path: Path
    entries: tuple[CheckoutEntryStatus, ...]

    @property
    def status(self) -> str:
        return "clean" if all(entry.status == "clean" for entry in self.entries) else "attention"

    @property
    def clean(self) -> int:
        return sum(1 for entry in self.entries if entry.status == "clean")

    @property
    def dirty(self) -> int:
        return sum(1 for entry in self.entries if entry.status == "dirty")

    @property
    def missing(self) -> int:
        return sum(1 for entry in self.entries if entry.status == "missing")

    @property
    def stale(self) -> int:
        return sum(1 for entry in self.entries if entry.status == "stale")


def lockfile_path(workspace: Path) -> Path:
    return workspace / LOCKFILE_RELATIVE_PATH


def empty_lockfile(workspace: Path) -> CheckoutLockfile:
    return CheckoutLockfile(workspace=str(workspace.resolve()))


def load_lockfile(workspace: Path) -> CheckoutLockfile:
    path = lockfile_path(workspace)
    if not path.exists():
        return empty_lockfile(workspace)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise CheckoutLockfileError(f"lockfile is not valid JSON: {error}") from error
    except OSError as error:
        raise CheckoutLockfileError(f"failed to read lockfile: {error}") from error
    lockfile = lockfile_from_dict(raw)
    errors = validate_lockfile(lockfile)
    if errors:
        raise CheckoutLockfileError("; ".join(errors))
    return normalize_lockfile(lockfile, workspace=workspace)


def write_lockfile(workspace: Path, lockfile: CheckoutLockfile) -> None:
    normalized = normalize_lockfile(lockfile, workspace=workspace)
    errors = validate_lockfile(normalized)
    if errors:
        raise CheckoutLockfileError("; ".join(errors))
    path = lockfile_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(lockfile_to_dict(normalized), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def validate_lockfile(lockfile: CheckoutLockfile) -> list[str]:
    errors: list[str] = []
    if lockfile.schema_version != LOCKFILE_VERSION:
        errors.append(f"unsupported lockfile version: {lockfile.schema_version}")
    if not lockfile.workspace:
        errors.append("workspace is required")
    seen_skills: dict[str, int] = {}
    seen_paths: dict[str, int] = {}
    for root in lockfile.roots:
        if skill_identity(root) != root:
            errors.append(f"root id must be normalized: {root!r}")
    for index, entry in enumerate(lockfile.entries):
        prefix = f"entries[{index}]"
        if not entry.skill_id:
            errors.append(f"{prefix}.skill_id is required")
        elif skill_identity(entry.skill_id) != entry.skill_id:
            errors.append(f"{prefix}.skill_id must be normalized as {skill_identity(entry.skill_id)!r}")
        if entry.skill_id in seen_skills:
            errors.append(f"{prefix}.skill_id duplicates entries[{seen_skills[entry.skill_id]}]")
        seen_skills.setdefault(entry.skill_id, index)
        if entry.ownership_class not in OWNERSHIP_CLASSES:
            errors.append(f"{prefix}.ownership_class is unknown: {entry.ownership_class!r}")
        if not _is_source_hash(entry.source_hash):
            errors.append(f"{prefix}.source_hash must be sha256:<64 hex chars>")
        if not _is_safe_relative_path(entry.materialized_path):
            errors.append(f"{prefix}.materialized_path must be a safe relative path")
        if entry.materialized_path in seen_paths:
            errors.append(f"{prefix}.materialized_path duplicates entries[{seen_paths[entry.materialized_path]}]")
        seen_paths.setdefault(entry.materialized_path, index)
        for graph_index, graph_id in enumerate(entry.graph_path):
            if skill_identity(graph_id) != graph_id:
                errors.append(f"{prefix}.graph_path[{graph_index}] must be normalized: {graph_id!r}")
    return errors


def hash_skill_source(path: Path) -> str:
    if not path.is_dir():
        raise CheckoutLockfileError(f"skill source is not a directory: {path}")
    digest = hashlib.sha256()
    for file_path in _hashable_files(path):
        relative = file_path.relative_to(path).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        try:
            digest.update(file_path.read_bytes())
        except OSError as error:
            raise CheckoutLockfileError(f"failed to read skill source file {file_path}: {error}") from error
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def checkout_skill(workspace: Path, skill_id: str, datastore: Path) -> CheckoutResult:
    normalized_id = skill_identity(skill_id)
    manifest = _load_valid_manifest(datastore)
    source_path = library_skill_source_path(datastore, manifest, normalized_id)
    target = workspace / ACTIVE_SKILLS_RELATIVE_PATH / normalized_id
    materialized = materialize_skill(source_path, target)
    source_hash = hash_skill_source(source_path)
    relative_target = materialized.relative_to(workspace).as_posix()
    lockfile = load_lockfile(workspace)
    entry = CheckoutEntry(
        skill_id=normalized_id,
        source_hash=source_hash,
        graph_path=(normalized_id,),
        materialized_path=relative_target,
        ownership_class="library",
        selected_by=(normalized_id,),
    )
    write_lockfile(workspace, record_checkout_entry(lockfile, entry))
    return CheckoutResult(
        skill_id=normalized_id,
        source_path=source_path,
        materialized_path=materialized,
        lockfile_path=lockfile_path(workspace),
        source_hash=source_hash,
    )


def checkout_tree(workspace: Path, root_id: str, datastore: Path) -> CheckoutTreeResult:
    manifest = _load_valid_manifest(datastore)
    plan = plan_checkout_tree(workspace, datastore, manifest, root_id)
    _preflight_plan(plan)
    materialized_paths: list[Path] = []
    created_paths: list[Path] = []
    try:
        for item in plan.items:
            existed = item.target_path.exists()
            materialized = materialize_skill(item.source_path, item.target_path)
            materialized_paths.append(materialized)
            if not existed:
                created_paths.append(materialized)
        lockfile = load_lockfile(workspace)
        write_lockfile(workspace, record_checkout_entries(lockfile, tuple(item.entry for item in plan.items)))
    except Exception:
        for path in reversed(created_paths):
            if path.exists():
                shutil.rmtree(path)
        raise
    return CheckoutTreeResult(
        root_id=plan.root_id,
        materialized_paths=tuple(materialized_paths),
        lockfile_path=lockfile_path(workspace),
    )


def plan_checkout_tree(workspace: Path, datastore: Path, manifest: GraphManifest, root_id: str) -> CheckoutPlan:
    try:
        traversal = resolve_top_down(manifest, root_id)
    except GraphManifestError as error:
        raise CheckoutLockfileError(str(error)) from error
    items: list[CheckoutPlanItem] = []
    for path in traversal.paths:
        source_path = library_skill_source_path(datastore, manifest, path.skill_id)
        source_hash = hash_skill_source(source_path)
        target_path = workspace / ACTIVE_SKILLS_RELATIVE_PATH / path.skill_id
        graph_path = _traversal_graph_path(path.edges, path.skill_id)
        entry = CheckoutEntry(
            skill_id=path.skill_id,
            source_hash=source_hash,
            graph_path=graph_path,
            materialized_path=target_path.relative_to(workspace).as_posix(),
            ownership_class="library",
            selected_by=(traversal.root_id,),
        )
        items.append(CheckoutPlanItem(entry, source_path, target_path))
    return CheckoutPlan(traversal.root_id, tuple(items))


def checkout_status(workspace: Path, datastore: Path) -> CheckoutStatus:
    lockfile = load_lockfile(workspace)
    manifest = _load_valid_manifest(datastore)
    return CheckoutStatus(
        workspace=workspace.resolve(),
        lockfile_path=lockfile_path(workspace),
        entries=tuple(_entry_status(workspace, datastore, manifest, entry) for entry in lockfile.entries),
    )


def format_checkout_status(status: CheckoutStatus) -> str:
    lines = [
        f"workspace: {status.workspace}",
        f"lockfile: {status.lockfile_path}",
        f"status: {status.status}",
        f"entries: {len(status.entries)}",
        f"clean: {status.clean}",
        f"dirty: {status.dirty}",
        f"missing: {status.missing}",
        f"stale: {status.stale}",
    ]
    for entry in status.entries:
        lines.append(f"entry: {entry.skill_id} {entry.status} {entry.materialized_path}")
        if entry.message:
            lines.append(f"message: {entry.skill_id}: {entry.message}")
    return "\n".join(lines)


def materialize_skill(source: Path, target: Path) -> Path:
    if not source.is_dir():
        raise CheckoutLockfileError(f"library skill source is not a directory: {source}")
    if not (source / "SKILL.md").is_file():
        raise CheckoutLockfileError(f"library skill source is missing SKILL.md: {source}")
    if target.exists():
        if not target.is_dir():
            raise CheckoutLockfileError(f"checkout target exists and is not a directory: {target}")
        if hash_skill_source(target) != hash_skill_source(source):
            raise CheckoutLockfileError(f"checkout target has local changes: {target}")
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, ignore=_copy_ignore)
    return target


def record_checkout_entry(lockfile: CheckoutLockfile, entry: CheckoutEntry) -> CheckoutLockfile:
    return record_checkout_entries(lockfile, (entry,))


def record_checkout_entries(lockfile: CheckoutLockfile, entries: tuple[CheckoutEntry, ...]) -> CheckoutLockfile:
    normalized_entries = tuple(normalize_entry(entry) for entry in entries)
    replaced_skill_ids = {entry.skill_id for entry in normalized_entries}
    replaced_paths = {entry.materialized_path for entry in normalized_entries}
    next_entries = [
        existing
        for existing in lockfile.entries
        if existing.skill_id not in replaced_skill_ids
        and existing.materialized_path not in replaced_paths
    ]
    next_entries.extend(normalized_entries)
    roots = set(lockfile.roots)
    for entry in normalized_entries:
        roots.update(entry.selected_by)
    return normalize_lockfile(
        CheckoutLockfile(
            workspace=lockfile.workspace,
            schema_version=lockfile.schema_version,
            roots=tuple(roots),
            entries=tuple(next_entries),
        )
    )


def normalize_lockfile(lockfile: CheckoutLockfile, workspace: Path | None = None) -> CheckoutLockfile:
    return CheckoutLockfile(
        workspace=str((workspace.resolve() if workspace is not None else Path(lockfile.workspace).expanduser().resolve())),
        schema_version=lockfile.schema_version,
        roots=tuple(sorted(skill_identity(root) for root in lockfile.roots)),
        entries=tuple(sorted((normalize_entry(entry) for entry in lockfile.entries), key=lambda item: item.materialized_path)),
    )


def normalize_entry(entry: CheckoutEntry) -> CheckoutEntry:
    return CheckoutEntry(
        skill_id=skill_identity(entry.skill_id),
        source_hash=entry.source_hash,
        graph_path=tuple(skill_identity(item) for item in entry.graph_path),
        materialized_path=Path(entry.materialized_path).as_posix(),
        ownership_class=entry.ownership_class,
        selected_by=tuple(sorted(skill_identity(item) for item in entry.selected_by)),
        metadata=dict(sorted(entry.metadata.items())),
    )


def lockfile_to_dict(lockfile: CheckoutLockfile) -> dict[str, Any]:
    return {
        "checkouts": [entry_to_dict(entry) for entry in lockfile.entries],
        "roots": list(lockfile.roots),
        "version": lockfile.schema_version,
        "workspace": lockfile.workspace,
    }


def entry_to_dict(entry: CheckoutEntry) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "graph_path": list(entry.graph_path),
        "materialized_path": entry.materialized_path,
        "ownership_class": entry.ownership_class,
        "skill_id": entry.skill_id,
        "source_hash": entry.source_hash,
    }
    if entry.selected_by:
        payload["selected_by"] = list(entry.selected_by)
    payload.update(entry.metadata)
    return payload


def lockfile_from_dict(raw: Any) -> CheckoutLockfile:
    if not isinstance(raw, dict):
        raise CheckoutLockfileError("lockfile root must be an object")
    entries = raw.get("checkouts", raw.get("entries", []))
    roots = raw.get("roots", [])
    if not isinstance(entries, list):
        raise CheckoutLockfileError("checkouts must be a list")
    if not isinstance(roots, list):
        raise CheckoutLockfileError("roots must be a list")
    try:
        schema_version = int(raw.get("version", raw.get("schema_version", LOCKFILE_VERSION)))
    except (TypeError, ValueError) as error:
        raise CheckoutLockfileError("lockfile version must be an integer") from error
    return CheckoutLockfile(
        workspace=str(raw.get("workspace", "")),
        schema_version=schema_version,
        roots=tuple(str(root) for root in roots),
        entries=tuple(entry_from_dict(entry, index) for index, entry in enumerate(entries)),
    )


def entry_from_dict(raw: Any, index: int = 0) -> CheckoutEntry:
    if not isinstance(raw, dict):
        raise CheckoutLockfileError(f"checkouts[{index}] must be an object")
    metadata = {
        key: value
        for key, value in raw.items()
        if key not in {"skill_id", "source_hash", "graph_path", "materialized_path", "ownership_class", "selected_by"}
    }
    graph_path = raw.get("graph_path", [])
    selected_by = raw.get("selected_by", [])
    if not isinstance(graph_path, list):
        raise CheckoutLockfileError(f"checkouts[{index}].graph_path must be a list")
    if not isinstance(selected_by, list):
        raise CheckoutLockfileError(f"checkouts[{index}].selected_by must be a list")
    return CheckoutEntry(
        skill_id=str(raw.get("skill_id", "")),
        source_hash=str(raw.get("source_hash", "")),
        graph_path=tuple(str(item) for item in graph_path),
        materialized_path=str(raw.get("materialized_path", "")),
        ownership_class=str(raw.get("ownership_class", "library")),
        selected_by=tuple(str(item) for item in selected_by),
        metadata=metadata,
    )


def library_skill_source_path(datastore: Path, manifest: GraphManifest, skill_id: str) -> Path:
    normalized_id = skill_identity(skill_id)
    for node in manifest.nodes:
        if skill_identity(node.id) != normalized_id:
            continue
        if node.type != "skill":
            raise CheckoutLockfileError(f"graph node is not a skill: {skill_id}")
        source = str(node.metadata.get("source") or (Path("skills") / normalized_id).as_posix())
        if not _is_safe_relative_path(source):
            raise CheckoutLockfileError(f"graph source path must be relative and safe: {source}")
        return datastore / LIBRARY_ROOT / source
    raise CheckoutLockfileError(f"graph skill node does not exist: {skill_id}")


def _load_valid_manifest(datastore: Path) -> GraphManifest:
    try:
        manifest = load_manifest(default_manifest_path(datastore))
    except GraphManifestError as error:
        raise CheckoutLockfileError(str(error)) from error
    errors = validate_manifest(manifest)
    if errors:
        detail = "; ".join(error.format() for error in errors)
        raise CheckoutLockfileError(f"graph manifest validation failed: {detail}")
    return manifest


def _hashable_files(path: Path) -> list[Path]:
    files: list[Path] = []
    for file_path in sorted(path.rglob("*")):
        if any(part in HASH_SKIP_NAMES for part in file_path.relative_to(path).parts):
            continue
        if file_path.is_file():
            files.append(file_path)
    return files


def _copy_ignore(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in HASH_SKIP_NAMES}


def _preflight_plan(plan: CheckoutPlan) -> None:
    for item in plan.items:
        if not item.source_path.is_dir():
            raise CheckoutLockfileError(f"library skill source is not a directory: {item.source_path}")
        if not (item.source_path / "SKILL.md").is_file():
            raise CheckoutLockfileError(f"library skill source is missing SKILL.md: {item.source_path}")
        if item.target_path.exists():
            if not item.target_path.is_dir():
                raise CheckoutLockfileError(f"checkout target exists and is not a directory: {item.target_path}")
            if hash_skill_source(item.target_path) != item.entry.source_hash:
                raise CheckoutLockfileError(f"checkout target has local changes: {item.target_path}")


def _traversal_graph_path(edges: tuple[Any, ...], skill_id: str) -> tuple[str, ...]:
    if not edges:
        return (skill_id,)
    path = [edges[0].source]
    path.extend(edge.target for edge in edges)
    return tuple(path)


def _entry_status(
    workspace: Path,
    datastore: Path,
    manifest: GraphManifest,
    entry: CheckoutEntry,
) -> CheckoutEntryStatus:
    active_path = workspace / entry.materialized_path
    source_path = library_skill_source_path(datastore, manifest, entry.skill_id)
    if not active_path.exists():
        return CheckoutEntryStatus(
            entry.skill_id,
            "missing",
            active_path,
            source_path,
            entry.source_hash,
            message="active checkout is missing",
        )
    if not active_path.is_dir():
        return CheckoutEntryStatus(
            entry.skill_id,
            "dirty",
            active_path,
            source_path,
            entry.source_hash,
            message="active checkout path is not a directory",
        )
    active_hash = hash_skill_source(active_path)
    if active_hash != entry.source_hash:
        return CheckoutEntryStatus(
            entry.skill_id,
            "dirty",
            active_path,
            source_path,
            entry.source_hash,
            active_hash=active_hash,
            message="active checkout hash differs from lockfile",
        )
    try:
        source_hash = hash_skill_source(source_path)
    except CheckoutLockfileError:
        return CheckoutEntryStatus(
            entry.skill_id,
            "stale",
            active_path,
            source_path,
            entry.source_hash,
            active_hash=active_hash,
            message="library source is unavailable",
        )
    if source_hash != entry.source_hash:
        return CheckoutEntryStatus(
            entry.skill_id,
            "stale",
            active_path,
            source_path,
            entry.source_hash,
            active_hash=active_hash,
            source_hash=source_hash,
            message="library source hash differs from lockfile",
        )
    return CheckoutEntryStatus(
        entry.skill_id,
        "clean",
        active_path,
        source_path,
        entry.source_hash,
        active_hash=active_hash,
        source_hash=source_hash,
    )


def _is_source_hash(value: str) -> bool:
    prefix = "sha256:"
    if not value.startswith(prefix):
        return False
    digest = value[len(prefix):]
    return len(digest) == 64 and all(char in "0123456789abcdef" for char in digest)


def _is_safe_relative_path(value: str) -> bool:
    if not value:
        return False
    path = Path(value)
    if path.is_absolute():
        return False
    return ".." not in path.parts
