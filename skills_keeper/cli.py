from __future__ import annotations

import argparse
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal

from .checkout import CheckoutLockfileError, checkout_skill
from .graph import (
    GraphManifestError,
    default_cache_metadata_path,
    default_manifest_path,
    graph_cache_status,
    load_manifest,
    normalize_manifest,
    validate_manifest,
    write_cache_metadata,
)
from .ids import skill_identity, slug


APP_SUPPORT = Path.home() / "Library" / "Application Support" / "SkillsKeeper"
STATE_PATH = APP_SUPPORT / "state.json"
DEFAULT_DATASTORE = APP_SUPPORT / "datastore"
SERVICE_RUNTIME = APP_SUPPORT / "service-runtime"
SERVICE_VENV = SERVICE_RUNTIME / ".venv"
SERVICE_BIN = SERVICE_VENV / "bin" / "skillskeeper"
PROJECTS_SKILLS = Path.home() / "Documents" / "Projects" / ".agents" / "skills"
CODEX_SKILLS = Path.home() / ".codex" / "skills"
SKIP_FILENAMES = {".system-skills-composer.json", ".composer-state.json"}
LAUNCHD_LABEL = "com.kellyjanderson.skillskeeper"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"
LOG_DIR = Path.home() / "Library" / "Logs" / "SkillsKeeper"
ARCHIVED_DIRNAME = "archived"
REGISTERED_DIRNAME = "registered"
DEFAULT_SERVICE_PATH = f"{Path.home()}/.local/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"


class KeeperError(Exception):
    def __init__(self, stage: str, message: str) -> None:
        super().__init__(message)
        self.stage = stage
        self.message = message


@dataclass(frozen=True)
class SkillSource:
    workspace: Path
    skill_dir: Path
    identity: str
    source_kind: str


@dataclass(frozen=True)
class SkillValidationResult:
    path: Path
    name: str
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.errors


MirrorRemovalStatus = Literal["removed", "missing", "skipped"]


@dataclass(frozen=True)
class ArchiveResult:
    archive_path: Path
    mirror_path: Path
    mirror_status: MirrorRemovalStatus


def read_state(path: Path | None = None) -> dict[str, Any]:
    path = path or STATE_PATH
    if not path.exists():
        return {
            "version": 1,
            "datastore": str(DEFAULT_DATASTORE),
            "workspaces": [],
            "skill_flags": {"global": {}, "workspaces": {}},
        }
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        state.setdefault("skill_flags", {"global": {}, "workspaces": {}})
        state["skill_flags"].setdefault("global", {})
        state["skill_flags"].setdefault("workspaces", {})
        return state
    except (OSError, json.JSONDecodeError) as error:
        raise KeeperError("state-read", f"failed to read {path}: {error}") from error


def write_state(state: dict[str, Any], path: Path | None = None) -> None:
    path = path or STATE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def resolve_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def registered_workspaces(state: dict[str, Any]) -> list[Path]:
    return [resolve_path(item["path"]) for item in state.get("workspaces", [])]


def datastore_path(state: dict[str, Any]) -> Path:
    return resolve_path(state.get("datastore") or DEFAULT_DATASTORE)


def timestamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def run_git(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=check)


def run_command(args: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=check)


def run_install_command(args: list[str], *, cwd: Path | None = None) -> None:
    result = run_command(args, cwd=cwd, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "command failed"
        raise KeeperError("install", f"{' '.join(args)}: {detail}")


def ensure_git_repo(path: Path, remote: str | None = None) -> None:
    path.mkdir(parents=True, exist_ok=True)
    if not (path / ".git").exists():
        run_git(["init"], path)
    if remote:
        existing = run_git(["remote"], path, check=False).stdout.split()
        if "origin" in existing:
            run_git(["remote", "set-url", "origin", remote], path)
        else:
            run_git(["remote", "add", "origin", remote], path)


def git_has_changes(path: Path) -> bool:
    result = run_git(["status", "--porcelain"], path)
    return bool(result.stdout.strip())


def git_commit_all(path: Path, message: str) -> bool:
    if not git_has_changes(path):
        return False
    run_git(["add", "."], path)
    run_git(["commit", "-m", message], path)
    return True


def push_if_remote(path: Path) -> bool:
    remotes = run_git(["remote"], path, check=False).stdout.split()
    if "origin" not in remotes:
        return False
    current = run_git(["branch", "--show-current"], path).stdout.strip() or "main"
    run_git(["push", "-u", "origin", current], path)
    return True


def parse_skill_name(skill_file: Path) -> str:
    try:
        text = skill_file.read_text(encoding="utf-8")
    except OSError:
        return skill_file.parent.name
    match = re.search(r"(?m)^name:\s*(.+?)\s*$", text)
    if not match:
        return skill_file.parent.name
    return match.group(1).strip().strip("'\"") or skill_file.parent.name


def resolve_skill_dir(path: str | Path) -> Path:
    resolved = resolve_path(path)
    if resolved.is_file() and resolved.name == "SKILL.md":
        return resolved.parent
    return resolved


def frontmatter_block(text: str) -> tuple[dict[str, str], str, list[str]]:
    errors: list[str] = []
    if not text.startswith("---\n"):
        return {}, text, ["SKILL.md must start with YAML frontmatter"]
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text, ["SKILL.md frontmatter must close with ---"]
    metadata: dict[str, str] = {}
    for line in text[4:end].splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in line:
            errors.append(f"invalid frontmatter line: {line}")
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip("'\"")
    return metadata, text[end + 5 :], errors


def validate_skill_dir(path: str | Path) -> SkillValidationResult:
    skill_dir = resolve_skill_dir(path)
    errors: list[str] = []
    warnings: list[str] = []
    name = skill_dir.name
    if not skill_dir.exists():
        return SkillValidationResult(skill_dir, name, (f"skill directory does not exist: {skill_dir}",), ())
    if not skill_dir.is_dir():
        return SkillValidationResult(skill_dir, name, (f"skill path is not a directory: {skill_dir}",), ())

    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        return SkillValidationResult(skill_dir, name, (f"missing required file: {skill_file}",), ())
    try:
        text = skill_file.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        return SkillValidationResult(skill_dir, name, (f"SKILL.md must be UTF-8 text: {error}",), ())
    except OSError as error:
        return SkillValidationResult(skill_dir, name, (f"failed to read SKILL.md: {error}",), ())

    metadata, body, frontmatter_errors = frontmatter_block(text)
    errors.extend(frontmatter_errors)
    name = metadata.get("name") or name
    description = metadata.get("description", "")
    if not metadata.get("name"):
        errors.append("frontmatter must include name")
    elif skill_identity(metadata["name"]) != metadata["name"]:
        warnings.append(f"name will be normalized by SkillsKeeper as {skill_identity(metadata['name'])}")
    if not description:
        errors.append("frontmatter must include description")
    elif len(description.split()) < 6:
        warnings.append("description is very short; Codex uses it to decide when to load the skill")
    if not body.strip():
        errors.append("SKILL.md body must not be empty")

    agents_metadata = skill_dir / "agents" / "openai.yaml"
    if (skill_dir / "agents").exists() and not agents_metadata.exists():
        warnings.append("agents/ exists without agents/openai.yaml")
    if agents_metadata.exists():
        try:
            metadata_text = agents_metadata.read_text(encoding="utf-8")
        except OSError as error:
            errors.append(f"failed to read agents/openai.yaml: {error}")
        else:
            for required in ("display_name:", "short_description:", "default_prompt:"):
                if required not in metadata_text:
                    warnings.append(f"agents/openai.yaml missing {required}")

    for skipped in sorted(SKIP_FILENAMES):
        if (skill_dir / skipped).exists():
            warnings.append(f"{skipped} is runtime state and will be skipped during archive/copy")

    return SkillValidationResult(skill_dir, name, tuple(errors), tuple(warnings))


def format_validation_result(result: SkillValidationResult) -> str:
    state = "ok" if result.ok else "failed"
    lines = [f"{state}: {result.path}", f"name: {result.name}"]
    for warning in result.warnings:
        lines.append(f"warning: {warning}")
    for error in result.errors:
        lines.append(f"error: {error}")
    return "\n".join(lines)


def read_text_arg(value: str | None, file_value: str | None, *, stage: str) -> str:
    if value is not None and file_value is not None:
        raise KeeperError(stage, "pass either --body or --body-file, not both")
    if file_value is not None:
        try:
            return resolve_path(file_value).read_text(encoding="utf-8")
        except OSError as error:
            raise KeeperError(stage, f"failed to read body file: {error}") from error
    if value is None:
        raise KeeperError(stage, "pass --body or --body-file")
    return value


def discover_skill_sources(workspace: Path) -> list[SkillSource]:
    sources: list[SkillSource] = []
    runtime_root = workspace / ".agents" / "skills"
    if runtime_root.is_dir():
        for skill_file in sorted(runtime_root.glob("*/SKILL.md")):
            skill_dir = skill_file.parent
            sources.append(
                SkillSource(
                    workspace=workspace,
                    skill_dir=skill_dir,
                    identity=parse_skill_name(skill_file),
                    source_kind="agents-skills",
                )
            )
    agents_root = workspace / ".agents"
    if agents_root.is_dir():
        for skill_file in sorted(agents_root.glob("*/SKILL.md")):
            if skill_file.parent.name == "skills":
                continue
            sources.append(
                SkillSource(
                    workspace=workspace,
                    skill_dir=skill_file.parent,
                    identity=parse_skill_name(skill_file),
                    source_kind="agents-local",
                )
            )
    return sources


def ignore_copy_entry(path: Path) -> bool:
    return path.name in SKIP_FILENAMES or path.name in {"__pycache__", ".DS_Store"}


def make_owner_writable(path: Path) -> None:
    for current in [path, *path.rglob("*")]:
        try:
            mode = current.stat().st_mode
            if current.is_dir():
                current.chmod(mode | 0o700)
            else:
                current.chmod(mode | 0o600)
        except OSError:
            continue


def copy_tree_clean(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    def ignore(_dir: str, names: list[str]) -> set[str]:
        return {name for name in names if ignore_copy_entry(Path(name))}
    shutil.copytree(src, dst, ignore=ignore)
    make_owner_writable(dst)


def directory_has_entries(path: Path) -> bool:
    return path.exists() and any(path.iterdir())


def backup_existing_file(path: Path) -> Path | None:
    if not path.exists():
        return None
    backup = path.with_name(f"{path.name}.backup-{timestamp()}")
    shutil.copy2(path, backup)
    return backup


def copy_datastore_for_install(source: Path, dest: Path, *, replace: bool) -> str:
    source = resolve_path(source)
    dest = resolve_path(dest)
    if source == dest:
        return "same-path"
    if not source.exists():
        raise KeeperError("install", f"migration source datastore does not exist: {source}")
    if directory_has_entries(dest):
        if not replace:
            raise KeeperError(
                "install",
                f"destination datastore already exists: {dest}; pass --replace-datastore to replace it",
            )
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, dest, symlinks=True)
    return "copied"


def workspace_key(workspace: Path) -> str:
    try:
        rel = workspace.relative_to(Path.home())
        return slug(str(rel))
    except ValueError:
        return slug(str(workspace))


def generated_codex_mirror_path(identity: str, prefix: str = "keld", root: Path | None = None) -> Path:
    root = resolve_path(root or CODEX_SKILLS)
    mirror_name = f"{slug(prefix)}-{skill_identity(identity)}"
    path = (root / mirror_name).resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise KeeperError("archive", f"generated mirror path escapes root: {path}") from error
    return path


def remove_generated_codex_mirror(
    identity: str,
    prefix: str = "keld",
    root: Path | None = None,
) -> tuple[Path, MirrorRemovalStatus]:
    mirror_path = generated_codex_mirror_path(identity, prefix=prefix, root=root)
    if not mirror_path.exists():
        return mirror_path, "missing"
    if mirror_path.is_dir() and not mirror_path.is_symlink():
        shutil.rmtree(mirror_path)
    else:
        mirror_path.unlink()
    return mirror_path, "removed"


def is_projects_global_skill(workspace: Path, source_kind: str) -> bool:
    return source_kind == "agents-skills" and resolve_path(workspace) == resolve_path(PROJECTS_SKILLS.parent.parent)


def skill_enabled(state: dict[str, Any], workspace: Path, identity: str) -> bool:
    key = skill_identity(identity)
    flags = state.get("skill_flags", {})
    global_flags = flags.get("global", {})
    if global_flags.get(key, {}).get("enabled") is False:
        return False
    workspace_flags = flags.get("workspaces", {}).get(str(resolve_path(workspace)), {})
    if workspace_flags.get(key, {}).get("enabled") is False:
        return False
    return True


def set_skill_enabled(
    state: dict[str, Any],
    identity: str,
    enabled: bool,
    workspace: Path | None = None,
) -> dict[str, Any]:
    key = skill_identity(identity)
    flags = state.setdefault("skill_flags", {"global": {}, "workspaces": {}})
    flags.setdefault("global", {})
    flags.setdefault("workspaces", {})
    target: dict[str, Any]
    if workspace is None:
        target = flags["global"]
    else:
        workspace_key_value = str(resolve_path(workspace))
        target = flags["workspaces"].setdefault(workspace_key_value, {})
    target[key] = {"enabled": enabled, "updated_at": timestamp()}
    return state


def disabled_skill_keys(state: dict[str, Any], workspace: Path | None = None) -> set[str]:
    flags = state.get("skill_flags", {})
    disabled = {
        key
        for key, value in flags.get("global", {}).items()
        if isinstance(value, dict) and value.get("enabled") is False
    }
    if workspace is not None:
        workspace_flags = flags.get("workspaces", {}).get(str(resolve_path(workspace)), {})
        disabled.update(
            key
            for key, value in workspace_flags.items()
            if isinstance(value, dict) and value.get("enabled") is False
        )
    return disabled


def source_archive_path(datastore: Path, active_path: Path, reason: str = "missing") -> Path:
    relative = active_path.relative_to(datastore / REGISTERED_DIRNAME)
    return datastore / ARCHIVED_DIRNAME / reason / timestamp() / relative


def move_active_skill_to_archive(datastore: Path, active_path: Path, reason: str = "missing") -> Path:
    if not active_path.exists():
        raise KeeperError("archive", f"active skill does not exist: {active_path}")
    archive_path = source_archive_path(datastore, active_path, reason=reason)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(active_path), str(archive_path))
    return archive_path


def active_skill_dirs(datastore: Path, workspace: Path) -> dict[tuple[str, str], Path]:
    root = datastore / REGISTERED_DIRNAME / workspace_key(workspace)
    result: dict[tuple[str, str], Path] = {}
    if not root.is_dir():
        return result
    for manifest in root.glob("*/*/.skillskeeper-source.json"):
        skill_dir = manifest.parent
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        source_kind = str(data.get("source_kind") or skill_dir.parent.name)
        identity = str(data.get("identity") or skill_dir.name)
        result[(source_kind, slug(identity))] = skill_dir
    return result


def move_disabled_workspace_skill_dirs(state: dict[str, Any], workspace: Path) -> int:
    disabled = disabled_skill_keys(state, workspace)
    if not disabled:
        return 0
    moved = 0
    runtime_root = workspace / ".agents" / "skills"
    if not runtime_root.is_dir():
        return 0
    archive_root = workspace / ".agents" / ".skillskeeper-disabled" / timestamp()
    runtime_sources = [
        source for source in discover_skill_sources(workspace)
        if source.source_kind == "agents-skills"
    ]
    seen_paths: set[Path] = set()
    for source in sorted(
        runtime_sources,
        key=lambda item: (skill_identity(item.identity), item.skill_dir.name),
    ):
        if skill_identity(source.identity) not in disabled:
            continue
        seen_paths.add(source.skill_dir)
        archive_root.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source.skill_dir), str(archive_root / source.skill_dir.name))
        moved += 1
    for key in sorted(disabled):
        path = runtime_root / key
        if not path.exists() or path in seen_paths:
            continue
        archive_root.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(archive_root / path.name))
        moved += 1
    return moved


def archive_workspace(datastore: Path, workspace: Path, state: dict[str, Any] | None = None) -> int:
    state = state or {"version": 1, "skill_flags": {"global": {}, "workspaces": {}}}
    count = 0
    root = datastore / REGISTERED_DIRNAME / workspace_key(workspace)
    move_disabled_workspace_skill_dirs(state, workspace)
    sources = discover_skill_sources(workspace)
    seen: set[tuple[str, str]] = set()
    for source in sources:
        key = (source.source_kind, slug(source.identity))
        if not skill_enabled(state, workspace, source.identity):
            active_path = root / source.source_kind / slug(source.identity)
            if active_path.exists():
                move_active_skill_to_archive(datastore, active_path, reason="disabled")
            continue
        seen.add(key)
        dst = root / source.source_kind / slug(source.identity)
        copy_tree_clean(source.skill_dir, dst)
        manifest = {
            "identity": source.identity,
            "source_kind": source.source_kind,
            "source_path": str(source.skill_dir),
            "workspace": str(workspace),
        }
        (dst / ".skillskeeper-source.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        count += 1
    for key, active_path in active_skill_dirs(datastore, workspace).items():
        if key[1] in disabled_skill_keys(state, workspace) and active_path.exists():
            move_active_skill_to_archive(datastore, active_path, reason="disabled")
        elif key not in seen and active_path.exists():
            move_active_skill_to_archive(datastore, active_path, reason="missing-from-workspace")
    return count


def infer_workspaces_from_datastore(datastore: Path) -> list[Path]:
    roots: dict[Path, None] = {}
    for manifest in sorted((datastore / REGISTERED_DIRNAME).glob("*/*/*/.skillskeeper-source.json")):
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        workspace = data.get("workspace")
        if isinstance(workspace, str):
            path = resolve_path(workspace)
            if path.is_dir():
                roots[path] = None
    return sorted(roots)


def merge_registered_workspaces(state: dict[str, Any], workspaces: Iterable[Path]) -> tuple[dict[str, Any], int]:
    existing = {resolve_path(item["path"]) for item in state.get("workspaces", [])}
    added = 0
    for workspace in workspaces:
        if workspace not in existing:
            state.setdefault("workspaces", []).append({"path": str(workspace)})
            existing.add(workspace)
            added += 1
    state["workspaces"] = sorted(state.get("workspaces", []), key=lambda item: item["path"])
    return state, added


def sync_all(push: bool = True) -> tuple[int, bool, bool]:
    state = read_state()
    datastore = datastore_path(state)
    ensure_git_repo(datastore)
    total = 0
    for workspace in registered_workspaces(state):
        total += archive_workspace(datastore, workspace, state=state)
    committed = git_commit_all(datastore, f"Archive skills snapshot ({total} skills)")
    pushed = push_if_remote(datastore) if push and committed else False
    return total, committed, pushed


def rewrite_skill_name(text: str, new_name: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            front = text[:end]
            rest = text[end:]
            if re.search(r"(?m)^name:\s*", front):
                return re.sub(r"(?m)^name:\s*.*$", f"name: {new_name}", text, count=1)
    return f"---\nname: {new_name}\n---\n\n{text}"


def copy_projects_skills_to_codex(prefix: str = "keld", state: dict[str, Any] | None = None) -> int:
    state = state or read_state()
    if not PROJECTS_SKILLS.is_dir():
        raise KeeperError("codex-sync", f"projects skills root does not exist: {PROJECTS_SKILLS}")
    CODEX_SKILLS.mkdir(parents=True, exist_ok=True)
    count = 0
    disabled = disabled_skill_keys(state, PROJECTS_SKILLS.parent.parent)
    for key in disabled:
        disabled_dir = CODEX_SKILLS / f"{prefix}-{key}"
        if disabled_dir.exists():
            shutil.rmtree(disabled_dir)
    for skill_file in sorted(PROJECTS_SKILLS.glob("*/SKILL.md")):
        src_dir = skill_file.parent
        source_name = parse_skill_name(skill_file)
        if not skill_enabled(state, PROJECTS_SKILLS.parent.parent, source_name):
            continue
        namespaced = f"{prefix}-{source_name}"
        dst_dir = CODEX_SKILLS / namespaced
        copy_tree_clean(src_dir, dst_dir)
        dst_skill = dst_dir / "SKILL.md"
        dst_skill.write_text(
            rewrite_skill_name(dst_skill.read_text(encoding="utf-8"), namespaced),
            encoding="utf-8",
        )
        count += 1
    return count


def reconcile_disabled_skills(
    state: dict[str, Any],
    workspace: Path | None = None,
    codex_prefix: str = "keld",
    push: bool = True,
) -> tuple[int, bool, bool, int]:
    datastore = datastore_path(state)
    ensure_git_repo(datastore)
    workspaces = [resolve_path(workspace)] if workspace is not None else registered_workspaces(state)
    total = 0
    for registered_workspace in workspaces:
        total += archive_workspace(datastore, registered_workspace, state=state)
    committed = git_commit_all(datastore, f"Reconcile disabled skills ({total} active skills)")
    pushed = push_if_remote(datastore) if push and committed else False
    codex_count = (
        copy_projects_skills_to_codex(prefix=codex_prefix, state=state)
        if PROJECTS_SKILLS.is_dir()
        else 0
    )
    return total, committed, pushed, codex_count


def command_register(args: argparse.Namespace) -> int:
    workspace = resolve_path(args.path)
    if not workspace.is_dir():
        raise KeeperError("register", f"workspace is not a directory: {workspace}")
    state = read_state()
    paths = {resolve_path(item["path"]) for item in state.get("workspaces", [])}
    if workspace not in paths:
        state.setdefault("workspaces", []).append({"path": str(workspace)})
        state["workspaces"] = sorted(state["workspaces"], key=lambda item: item["path"])
        write_state(state)
        print(f"registered: {workspace}")
    else:
        print(f"already registered: {workspace}")
    return 0


def command_unregister(args: argparse.Namespace) -> int:
    workspace = resolve_path(args.path)
    state = read_state()
    before = len(state.get("workspaces", []))
    state["workspaces"] = [
        item for item in state.get("workspaces", [])
        if resolve_path(item["path"]) != workspace
    ]
    write_state(state)
    print(f"unregistered: {workspace}" if len(state["workspaces"]) != before else f"not registered: {workspace}")
    return 0


def command_infer(args: argparse.Namespace) -> int:
    state = read_state()
    if args.datastore:
        state["datastore"] = str(resolve_path(args.datastore))
    datastore = datastore_path(state)
    if not datastore.is_dir():
        raise KeeperError("infer", f"datastore is not a directory: {datastore}")
    workspaces = infer_workspaces_from_datastore(datastore)
    state, added = merge_registered_workspaces(state, workspaces)
    if not args.dry_run:
        write_state(state)
    print(f"datastore: {datastore}")
    print(f"inferred workspaces: {len(workspaces)}")
    print(f"added: {added}")
    print(f"written: {str(not args.dry_run).lower()}")
    for workspace in workspaces:
        print(workspace)
    return 0


def command_list(_args: argparse.Namespace) -> int:
    state = read_state()
    print(f"state: {STATE_PATH}")
    print(f"datastore: {datastore_path(state)}")
    workspaces = registered_workspaces(state)
    print(f"registered workspaces: {len(workspaces)}")
    for workspace in workspaces:
        print(workspace)
    return 0


def command_datastore_init(args: argparse.Namespace) -> int:
    state = read_state()
    if args.path:
        state["datastore"] = str(resolve_path(args.path))
        write_state(state)
    datastore = datastore_path(state)
    ensure_git_repo(datastore, remote=args.remote)
    readme = datastore / "README.md"
    if not readme.exists():
        readme.write_text(
            "# SkillsKeeper Datastore\n\nPrivate archive of registered agent skills.\n",
            encoding="utf-8",
        )
    committed = git_commit_all(datastore, "Initialize skills datastore")
    pushed = push_if_remote(datastore) if args.push else False
    print(f"datastore: {datastore}")
    print(f"committed: {str(committed).lower()}")
    print(f"pushed: {str(pushed).lower()}")
    return 0


def command_sync(args: argparse.Namespace) -> int:
    total, committed, pushed = sync_all(push=not args.no_push)
    codex_count = copy_projects_skills_to_codex(prefix=args.codex_prefix) if not args.no_codex_sync else 0
    print(f"archived skills: {total}")
    print(f"codex copied skills: {codex_count}")
    print(f"committed: {str(committed).lower()}")
    print(f"pushed: {str(pushed).lower()}")
    return 0


def command_codex_sync(args: argparse.Namespace) -> int:
    count = copy_projects_skills_to_codex(prefix=args.prefix)
    print(f"copied skills: {count}")
    print(f"target: {CODEX_SKILLS}")
    return 0


def load_valid_graph_manifest_for_command(command: str) -> tuple[Path, Any]:
    manifest_path = default_manifest_path(datastore_path(read_state()))
    try:
        manifest = load_manifest(manifest_path)
    except GraphManifestError as error:
        raise KeeperError(command, str(error)) from error
    errors = validate_manifest(manifest)
    if errors:
        detail = "; ".join(error.format() for error in errors)
        raise KeeperError(command, f"graph manifest validation failed: {detail}")
    return manifest_path, manifest


def command_library_graph_rebuild(_args: argparse.Namespace) -> int:
    manifest_path, manifest = load_valid_graph_manifest_for_command("library graph rebuild")
    normalized = normalize_manifest(manifest)
    datastore = datastore_path(read_state())
    metadata = write_cache_metadata(datastore, normalized, manifest_path=manifest_path)
    print(f"manifest: {manifest_path}")
    print(f"cache metadata: {default_cache_metadata_path(datastore)}")
    print("status: rebuilt")
    print(f"schema version: {normalized.schema_version}")
    print(f"nodes: {len(normalized.nodes)}")
    print(f"edges: {len(normalized.edges)}")
    print(f"manifest hash: {metadata.manifest_hash}")
    print("cache written: true")
    return 0


def command_library_graph_status(_args: argparse.Namespace) -> int:
    status = graph_cache_status(datastore_path(read_state()))
    print(f"manifest: {status.manifest_path}")
    print(f"cache metadata: {status.metadata_path}")
    print(f"status: {status.status}")
    if status.schema_version is not None:
        print(f"schema version: {status.schema_version}")
    if status.nodes is not None:
        print(f"nodes: {status.nodes}")
    if status.edges is not None:
        print(f"edges: {status.edges}")
    if status.manifest_hash is not None:
        print(f"manifest hash: {status.manifest_hash}")
    if status.cached_manifest_hash is not None:
        print(f"cached manifest hash: {status.cached_manifest_hash}")
    if status.cached_schema_version is not None:
        print(f"cached schema version: {status.cached_schema_version}")
    print(f"message: {status.message}")
    return 0 if status.status == "fresh" else 1


def command_checkout_skill(args: argparse.Namespace) -> int:
    workspace = resolve_path(args.workspace)
    try:
        result = checkout_skill(workspace, args.skill_id, datastore_path(read_state()))
    except CheckoutLockfileError as error:
        raise KeeperError("checkout skill", str(error)) from error
    print(f"skill: {result.skill_id}")
    print("status: checked-out")
    print(f"source: {result.source_path}")
    print(f"materialized: {result.materialized_path}")
    print(f"lockfile: {result.lockfile_path}")
    print(f"source hash: {result.source_hash}")
    for warning in result.warnings:
        print(f"warning: {warning}")
    return 0


def command_skill_flag(args: argparse.Namespace) -> int:
    state = read_state()
    workspace = resolve_path(args.workspace) if args.workspace else None
    enabled = args.skill_command == "enable"
    state = set_skill_enabled(state, args.identity, enabled, workspace=workspace)
    write_state(state)
    reconciled: tuple[int, bool, bool, int] | None = None
    if not enabled:
        reconciled = reconcile_disabled_skills(
            state,
            workspace=workspace,
            codex_prefix=args.codex_prefix,
            push=not args.no_push,
        )
    scope = str(workspace) if workspace else "global"
    print(f"skill: {skill_identity(args.identity)}")
    print(f"scope: {scope}")
    print(f"enabled: {str(enabled).lower()}")
    if reconciled is not None:
        active_count, committed, pushed, codex_count = reconciled
        print(f"active skills copied: {active_count}")
        print(f"codex copied skills: {codex_count}")
        print(f"committed: {str(committed).lower()}")
        print(f"pushed: {str(pushed).lower()}")
    return 0


def command_skill_list(_args: argparse.Namespace) -> int:
    state = read_state()
    flags = state.get("skill_flags", {})
    print("global:")
    for key, value in sorted(flags.get("global", {}).items()):
        print(f"  {key}: enabled={str(value.get('enabled')).lower()}")
    print("workspaces:")
    for workspace, entries in sorted(flags.get("workspaces", {}).items()):
        print(f"  {workspace}:")
        for key, value in sorted(entries.items()):
            print(f"    {key}: enabled={str(value.get('enabled')).lower()}")
    return 0


def command_skill_validate(args: argparse.Namespace) -> int:
    failed = False
    for index, path in enumerate(args.paths):
        if index:
            print()
        result = validate_skill_dir(path)
        print(format_validation_result(result))
        failed = failed or not result.ok
    return 1 if failed else 0


def ensure_workspace_registered(state: dict[str, Any], workspace: Path) -> bool:
    resolved = resolve_path(workspace)
    existing = {resolve_path(item["path"]) for item in state.get("workspaces", [])}
    if resolved in existing:
        return False
    state.setdefault("workspaces", []).append({"path": str(resolved)})
    state["workspaces"] = sorted(state["workspaces"], key=lambda item: item["path"])
    write_state(state)
    return True


def target_root_for_scope(args: argparse.Namespace, *, state: dict[str, Any]) -> tuple[Path, Path, bool]:
    if getattr(args, "global_skill", False):
        return PROJECTS_SKILLS, PROJECTS_SKILLS.parent.parent, False
    workspace = resolve_path(getattr(args, "workspace", None) or Path.cwd())
    if not workspace.is_dir():
        raise KeeperError("skill", f"workspace is not a directory: {workspace}")
    registered = ensure_workspace_registered(state, workspace) if not getattr(args, "no_register", False) else False
    return workspace / ".agents" / "skills", workspace, registered


def sync_after_skill_change(args: argparse.Namespace) -> tuple[int, int, bool, bool]:
    archived_total, committed, pushed = sync_all(push=not getattr(args, "no_push", False))
    codex_count = (
        0
        if getattr(args, "no_codex_sync", False)
        else copy_projects_skills_to_codex(prefix=getattr(args, "codex_prefix", "keld"))
    )
    return archived_total, codex_count, committed, pushed


def print_sync_summary(archived_total: int, codex_count: int, committed: bool, pushed: bool) -> None:
    print(f"archived skills: {archived_total}")
    print(f"codex copied skills: {codex_count}")
    print(f"committed: {str(committed).lower()}")
    print(f"pushed: {str(pushed).lower()}")


def resolve_existing_skill(target_root: Path, identity: str) -> Path:
    direct = target_root / skill_identity(identity)
    if (direct / "SKILL.md").exists():
        return direct
    matches = [
        skill_file.parent
        for skill_file in sorted(target_root.glob("*/SKILL.md"))
        if skill_identity(parse_skill_name(skill_file)) == skill_identity(identity)
    ]
    if not matches:
        raise KeeperError("skill", f"target skill does not exist: {target_root / skill_identity(identity)}")
    if len(matches) > 1:
        joined = ", ".join(str(path) for path in matches)
        raise KeeperError("skill", f"multiple target skills match {identity!r}: {joined}")
    return matches[0]


def install_skill_to_root(
    source: Path,
    target_root: Path,
    identity: str,
    *,
    must_exist: bool = False,
    rewrite_name: bool = False,
) -> Path:
    target_dir = target_root / skill_identity(identity)
    if must_exist:
        target_dir = resolve_existing_skill(target_root, identity)
    elif target_dir.exists():
        raise KeeperError("skill-add", f"target skill already exists: {target_dir}; use `skillskeeper skill update`")
    if source.resolve() == target_dir.resolve():
        raise KeeperError("skill-add", f"source and target are the same directory: {source}")
    target_root.mkdir(parents=True, exist_ok=True)
    copy_tree_clean(source, target_dir)
    if rewrite_name:
        skill_file = target_dir / "SKILL.md"
        skill_file.write_text(
            rewrite_skill_name(skill_file.read_text(encoding="utf-8"), skill_identity(identity)),
            encoding="utf-8",
        )
    return target_dir


DIRECTIVE_SECTION = "## SkillsKeeper Directives"
DIRECTIVE_OPEN = "<!-- skillskeeper-directive:"
DIRECTIVE_CLOSE = "<!-- /skillskeeper-directive:"


def directive_slug(title: str) -> str:
    return slug(title).lower()


def directive_markers(title: str) -> tuple[str, str, str]:
    key = directive_slug(title)
    return key, f"{DIRECTIVE_OPEN} {key} -->", f"{DIRECTIVE_CLOSE} {key} -->"


def append_directive(skill_dir: Path, title: str, body: str) -> None:
    skill_file = skill_dir / "SKILL.md"
    text = skill_file.read_text(encoding="utf-8")
    key, open_marker, close_marker = directive_markers(title)
    if open_marker in text:
        raise KeeperError("directive", f"directive already exists: {key}")
    directive = f"{open_marker}\n### {title}\n\n{body.strip()}\n{close_marker}\n"
    if f"\n{DIRECTIVE_SECTION}\n" not in text:
        text = text.rstrip() + f"\n\n{DIRECTIVE_SECTION}\n\n{directive}"
    else:
        text = text.rstrip() + f"\n\n{directive}"
    skill_file.write_text(text, encoding="utf-8")


def remove_directive(skill_dir: Path, title: str) -> None:
    skill_file = skill_dir / "SKILL.md"
    text = skill_file.read_text(encoding="utf-8")
    key, open_marker, close_marker = directive_markers(title)
    pattern = re.compile(
        rf"\n*{re.escape(open_marker)}\n.*?\n{re.escape(close_marker)}\n*",
        re.DOTALL,
    )
    updated, count = pattern.subn("\n\n", text, count=1)
    if count == 0:
        raise KeeperError("directive", f"directive does not exist: {key}")
    skill_file.write_text(updated.rstrip() + "\n", encoding="utf-8")


def command_skill_add(args: argparse.Namespace) -> int:
    source = resolve_skill_dir(args.source)
    source_result = validate_skill_dir(source)
    if not source_result.ok:
        print(format_validation_result(source_result))
        return 1

    identity = args.name or source_result.name
    rewrite_name = bool(args.name) or skill_identity(identity) != identity
    state = read_state()
    target_root, workspace, registered = target_root_for_scope(args, state=state)

    target_dir = install_skill_to_root(
        source,
        target_root,
        identity,
        rewrite_name=rewrite_name,
    )
    target_result = validate_skill_dir(target_dir)
    print(format_validation_result(target_result))
    if not target_result.ok:
        return 1

    archived_total, codex_count, committed, pushed = sync_after_skill_change(args)
    print(f"installed: {target_dir}")
    print(f"workspace: {workspace}")
    print(f"registered workspace: {str(registered).lower()}")
    print_sync_summary(archived_total, codex_count, committed, pushed)
    return 0


def command_skill_update(args: argparse.Namespace) -> int:
    source = resolve_skill_dir(args.source)
    source_result = validate_skill_dir(source)
    if not source_result.ok:
        print(format_validation_result(source_result))
        return 1
    identity = args.name or source_result.name
    rewrite_name = bool(args.name) or skill_identity(identity) != identity
    state = read_state()
    target_root, workspace, registered = target_root_for_scope(args, state=state)
    target_dir = install_skill_to_root(
        source,
        target_root,
        identity,
        must_exist=True,
        rewrite_name=rewrite_name,
    )
    target_result = validate_skill_dir(target_dir)
    print(format_validation_result(target_result))
    if not target_result.ok:
        return 1
    archived_total, codex_count, committed, pushed = sync_after_skill_change(args)
    print(f"updated: {target_dir}")
    print(f"workspace: {workspace}")
    print(f"registered workspace: {str(registered).lower()}")
    print_sync_summary(archived_total, codex_count, committed, pushed)
    return 0


def command_skill_directive(args: argparse.Namespace) -> int:
    state = read_state()
    target_root, workspace, registered = target_root_for_scope(args, state=state)
    target_dir = resolve_existing_skill(target_root, args.identity)
    if args.directive_command == "add":
        body = read_text_arg(args.body, args.body_file, stage="directive")
        append_directive(target_dir, args.title, body)
        action = "added directive"
    elif args.directive_command == "remove":
        remove_directive(target_dir, args.title)
        action = "removed directive"
    else:
        raise KeeperError("directive", f"unknown command: {args.directive_command}")
    target_result = validate_skill_dir(target_dir)
    print(format_validation_result(target_result))
    if not target_result.ok:
        return 1
    archived_total, codex_count, committed, pushed = sync_after_skill_change(args)
    print(f"{action}: {directive_slug(args.title)}")
    print(f"skill: {target_dir}")
    print(f"workspace: {workspace}")
    print(f"registered workspace: {str(registered).lower()}")
    print_sync_summary(archived_total, codex_count, committed, pushed)
    return 0


def resolve_active_skill(datastore: Path, workspace: Path, source_kind: str, identity: str) -> Path:
    path = (
        datastore
        / REGISTERED_DIRNAME
        / workspace_key(workspace)
        / source_kind
        / slug(identity)
    )
    if not path.exists():
        raise KeeperError("skill", f"active skill does not exist: {path}")
    return path


def commit_and_maybe_push(datastore: Path, message: str, push: bool) -> tuple[bool, bool]:
    committed = git_commit_all(datastore, message)
    pushed = push_if_remote(datastore) if push and committed else False
    return committed, pushed


def archive_managed_global_skill(
    datastore: Path,
    workspace: Path,
    source_kind: str,
    identity: str,
    codex_prefix: str = "keld",
) -> ArchiveResult:
    active = resolve_active_skill(datastore, workspace, source_kind, identity)
    archived = move_active_skill_to_archive(datastore, active, reason="intentional")
    mirror_path = generated_codex_mirror_path(identity, prefix=codex_prefix)
    mirror_status: MirrorRemovalStatus = "skipped"
    if is_projects_global_skill(workspace, source_kind):
        mirror_path, mirror_status = remove_generated_codex_mirror(identity, prefix=codex_prefix)
    return ArchiveResult(archived, mirror_path, mirror_status)


def command_archive_skill(args: argparse.Namespace) -> int:
    state = read_state()
    datastore = datastore_path(state)
    workspace = resolve_path(args.workspace)
    result = archive_managed_global_skill(
        datastore,
        workspace,
        args.source_kind,
        args.identity,
        codex_prefix=args.codex_prefix,
    )
    committed, pushed = commit_and_maybe_push(
        datastore,
        f"Archive skill {args.identity} from {workspace_key(workspace)}",
        push=not args.no_push,
    )
    print(f"archived: {result.archive_path}")
    print(f"codex mirror: {result.mirror_path}")
    print(f"codex mirror status: {result.mirror_status}")
    print(f"committed: {str(committed).lower()}")
    print(f"pushed: {str(pushed).lower()}")
    return 0


def command_delete_current_skill(args: argparse.Namespace) -> int:
    state = read_state()
    datastore = datastore_path(state)
    workspace = resolve_path(args.workspace)
    active = resolve_active_skill(datastore, workspace, args.source_kind, args.identity)
    if args.confirm != "delete-current":
        raise KeeperError("delete-current", "pass --confirm delete-current")
    shutil.rmtree(active)
    committed, pushed = commit_and_maybe_push(
        datastore,
        f"Remove current skill {args.identity} from {workspace_key(workspace)}",
        push=not args.no_push,
    )
    print(f"removed from current set: {active}")
    print("history: preserved in git")
    print(f"committed: {str(committed).lower()}")
    print(f"pushed: {str(pushed).lower()}")
    return 0


def command_status(_args: argparse.Namespace) -> int:
    state = read_state()
    datastore = datastore_path(state)
    print(f"state: {STATE_PATH}")
    print(f"datastore: {datastore}")
    print(f"datastore exists: {datastore.exists()}")
    if datastore.exists() and (datastore / ".git").exists():
        print(f"datastore changes: {str(git_has_changes(datastore)).lower()}")
    print(f"projects skills: {PROJECTS_SKILLS}")
    print(f"codex skills: {CODEX_SKILLS}")
    print(f"registered workspaces: {len(registered_workspaces(state))}")
    return 0


def service_program(runtime_root: Path | None = None) -> Path:
    if runtime_root is None:
        return SERVICE_BIN
    return runtime_root / ".venv" / "bin" / "skillskeeper"


def service_python(runtime_root: Path | None = None) -> Path:
    root = runtime_root or SERVICE_RUNTIME
    return root / ".venv" / "bin" / "python"


def source_project_root() -> Path | None:
    candidate = Path(__file__).resolve().parents[1]
    if (candidate / "pyproject.toml").exists():
        return candidate
    return None


def resolve_install_package(value: str | None) -> Path | str:
    if value:
        path = Path(value).expanduser()
        return str(path.resolve()) if path.exists() else value
    root = source_project_root()
    if root is None:
        raise KeeperError(
            "install",
            "pass --package when installing from a non-source SkillsKeeper runtime",
        )
    return str(root)


def install_service_runtime(
    *,
    package: str | None,
    runtime_root: Path,
    runtime_python: str,
    replace: bool,
    skip: bool,
) -> Path:
    program = service_program(runtime_root)
    if skip:
        if not program.exists():
            raise KeeperError("install", f"service executable does not exist: {program}")
        return program

    venv = runtime_root / ".venv"
    if replace and venv.exists():
        shutil.rmtree(venv)
    runtime_root.mkdir(parents=True, exist_ok=True)
    if not (venv / "pyvenv.cfg").exists():
        run_install_command([runtime_python, "-m", "venv", str(venv)])

    python = service_python(runtime_root)
    package_source = resolve_install_package(package)
    run_install_command([str(python), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
    run_install_command([str(python), "-m", "pip", "install", "--force-reinstall", str(package_source)])
    if not program.exists():
        raise KeeperError("install", f"package install did not create service executable: {program}")
    return program


def install_launch_agent(args: argparse.Namespace, program: Path) -> Path | None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    backup = backup_existing_file(PLIST_PATH)
    plist = {
        "Label": LAUNCHD_LABEL,
        "ProgramArguments": [
            str(program),
            "watch",
            "--debounce",
            str(args.debounce),
        ],
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardOutPath": str(LOG_DIR / f"{LAUNCHD_LABEL}.out.log"),
        "StandardErrorPath": str(LOG_DIR / f"{LAUNCHD_LABEL}.err.log"),
        "EnvironmentVariables": {
            "PYTHONUNBUFFERED": "1",
            "PATH": DEFAULT_SERVICE_PATH,
        },
    }
    if args.no_push:
        plist["ProgramArguments"].append("--no-push")
    with PLIST_PATH.open("wb") as handle:
        plistlib.dump(plist, handle)
    return backup


def launchctl(args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["launchctl", *args], text=True, capture_output=True, check=check)


def command_install(args: argparse.Namespace) -> int:
    if args.load:
        launchctl(["bootout", f"gui/{os.getuid()}", str(PLIST_PATH)], check=False)
    state = read_state()
    if args.datastore_path:
        state["datastore"] = str(resolve_path(args.datastore_path))
    datastore = datastore_path(state)
    datastore_migration = "none"
    if args.migrate_datastore_from:
        datastore_migration = copy_datastore_for_install(
            Path(args.migrate_datastore_from),
            datastore,
            replace=args.replace_datastore,
        )
    ensure_git_repo(datastore, remote=args.datastore_remote)
    inferred = infer_workspaces_from_datastore(datastore) if datastore.exists() else []
    state, added = merge_registered_workspaces(state, inferred)
    state_backup = backup_existing_file(STATE_PATH)
    write_state(state)
    runtime_root = resolve_path(args.runtime_root)
    program = install_service_runtime(
        package=args.package,
        runtime_root=runtime_root,
        runtime_python=args.runtime_python,
        replace=args.replace_runtime,
        skip=args.skip_runtime_install,
    )
    plist_backup = install_launch_agent(args, program)
    if args.load:
        result = launchctl(["bootstrap", f"gui/{os.getuid()}", str(PLIST_PATH)], check=False)
        if result.returncode != 0:
            raise KeeperError("launchd", result.stderr.strip() or result.stdout.strip())
        launchctl(["enable", f"gui/{os.getuid()}/{LAUNCHD_LABEL}"], check=False)
        launchctl(["kickstart", "-k", f"gui/{os.getuid()}/{LAUNCHD_LABEL}"], check=False)
    print(f"state: {STATE_PATH}")
    print(f"state backup: {state_backup or ''}")
    print(f"datastore: {datastore}")
    print(f"datastore migration: {datastore_migration}")
    print(f"service runtime: {runtime_root}")
    print(f"service executable: {program}")
    print(f"plist: {PLIST_PATH}")
    print(f"plist backup: {plist_backup or ''}")
    print(f"inferred workspaces added: {added}")
    print(f"loaded: {str(args.load).lower()}")
    return 0


def command_service(args: argparse.Namespace) -> int:
    if args.service_command == "start":
        launchctl(["enable", f"gui/{os.getuid()}/{LAUNCHD_LABEL}"], check=False)
        result = launchctl(["bootstrap", f"gui/{os.getuid()}", str(PLIST_PATH)], check=False)
        already_loaded = "Bootstrap failed: 5" in result.stderr
        if result.returncode != 0 and not already_loaded:
            raise KeeperError("service", result.stderr.strip() or result.stdout.strip())
        launchctl(["kickstart", "-k", f"gui/{os.getuid()}/{LAUNCHD_LABEL}"], check=False)
        print(f"started: {LAUNCHD_LABEL}")
    elif args.service_command == "stop":
        launchctl(["bootout", f"gui/{os.getuid()}", str(PLIST_PATH)], check=False)
        launchctl(["disable", f"gui/{os.getuid()}/{LAUNCHD_LABEL}"], check=False)
        print(f"stopped: {LAUNCHD_LABEL}")
    elif args.service_command == "status":
        result = launchctl(["print", f"gui/{os.getuid()}/{LAUNCHD_LABEL}"], check=False)
        print(result.stdout if result.returncode == 0 else result.stderr, end="")
        return result.returncode
    else:
        raise KeeperError("service", f"unknown command: {args.service_command}")
    return 0


def command_watch(args: argparse.Namespace) -> int:
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError as error:
        raise KeeperError("watch", "watchdog is required; run `pip install -r requirements.txt`") from error

    state = read_state()
    roots = registered_workspaces(state)
    if not roots:
        raise KeeperError("watch", "no registered workspaces")

    class Handler(FileSystemEventHandler):
        def __init__(self) -> None:
            self.last_sync = 0.0

        def on_any_event(self, event: Any) -> None:
            path = Path(getattr(event, "src_path", ""))
            if ".agents" not in path.parts:
                return
            now = time.monotonic()
            if now - self.last_sync < args.debounce:
                return
            self.last_sync = now
            total, committed, pushed = sync_all(push=not args.no_push)
            codex_count = 0
            if not args.no_codex_sync:
                codex_count = copy_projects_skills_to_codex(prefix=args.codex_prefix)
            print(
                f"event sync: {total} skills, codex={codex_count}, "
                f"committed={committed}, pushed={pushed}",
                flush=True,
            )

    observer = Observer()
    handler = Handler()
    for root in roots:
        observer.schedule(handler, str(root), recursive=True)
        print(f"watching: {root}")
    observer.start()
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="skillskeeper")
    sub = parser.add_subparsers(dest="command", required=True)

    register = sub.add_parser("register", help="register a workspace to archive")
    register.add_argument("path")
    register.set_defaults(func=command_register)

    unregister = sub.add_parser("unregister", help="remove a registered workspace")
    unregister.add_argument("path")
    unregister.set_defaults(func=command_unregister)

    infer = sub.add_parser("infer", help="infer registered workspaces from datastore manifests")
    infer.add_argument("--datastore")
    infer.add_argument("--dry-run", action="store_true")
    infer.set_defaults(func=command_infer)

    sub.add_parser("list", help="list registered workspaces").set_defaults(func=command_list)
    sub.add_parser("status", help="show state and datastore status").set_defaults(func=command_status)

    sync = sub.add_parser("sync", help="archive registered skills now")
    sync.add_argument("--no-push", action="store_true", help="commit but do not push datastore changes")
    sync.add_argument("--no-codex-sync", action="store_true", help="do not update ~/.codex/skills")
    sync.add_argument("--codex-prefix", default="keld")
    sync.set_defaults(func=command_sync)

    watch = sub.add_parser("watch", help="watch registered workspaces using filesystem events")
    watch.add_argument("--debounce", type=float, default=1.0)
    watch.add_argument("--no-push", action="store_true", help="commit but do not push datastore changes")
    watch.add_argument("--no-codex-sync", action="store_true", help="do not update ~/.codex/skills")
    watch.add_argument("--codex-prefix", default="keld")
    watch.set_defaults(func=command_watch)

    codex = sub.add_parser("codex-sync", help="copy Projects-level skills into ~/.codex/skills with a namespace")
    codex.add_argument("--prefix", default="keld")
    codex.set_defaults(func=command_codex_sync)

    checkout_parser = sub.add_parser("checkout", help="materialize reusable library skills")
    checkout_sub = checkout_parser.add_subparsers(dest="checkout_command", required=True)
    checkout_skill_parser = checkout_sub.add_parser("skill", help="checkout one reusable library skill")
    checkout_skill_parser.add_argument("skill_id")
    checkout_skill_parser.add_argument("--workspace", required=True)
    checkout_skill_parser.set_defaults(func=command_checkout_skill)

    library = sub.add_parser("library", help="manage reusable skill library data")
    library_sub = library.add_subparsers(dest="library_command", required=True)
    graph = library_sub.add_parser("graph", help="manage the reusable skill graph")
    graph_sub = graph.add_subparsers(dest="graph_command", required=True)
    graph_sub.add_parser("rebuild", help="validate the graph manifest before cache rebuild").set_defaults(
        func=command_library_graph_rebuild
    )
    graph_sub.add_parser("status", help="show graph manifest validation status").set_defaults(
        func=command_library_graph_status
    )

    skill = sub.add_parser("skill", help="manage skill enablement flags")
    skill_sub = skill.add_subparsers(dest="skill_command", required=True)
    for name in ("enable", "disable"):
        flag = skill_sub.add_parser(name, help=f"{name} a skill globally or for one workspace")
        flag.add_argument("identity")
        flag.add_argument("--workspace", help="workspace path; omit for global")
        flag.add_argument("--no-push", action="store_true", help="commit but do not push datastore cleanup")
        flag.add_argument("--codex-prefix", default="keld")
        flag.set_defaults(func=command_skill_flag)
    validate = skill_sub.add_parser("validate", help="validate one or more skill directories")
    validate.add_argument("paths", nargs="+", help="skill directory or SKILL.md path")
    validate.set_defaults(func=command_skill_validate)
    add = skill_sub.add_parser("add", help="validate and install a skill into a managed skills folder")
    add.add_argument("source", help="source skill directory or SKILL.md path")
    target = add.add_mutually_exclusive_group()
    target.add_argument("--workspace", help="install into this workspace's .agents/skills; defaults to cwd")
    target.add_argument("--global", dest="global_skill", action="store_true", help="install into ~/Documents/Projects/.agents/skills")
    add.add_argument("--name", help="target skill identity; defaults to the source SKILL.md name")
    add.add_argument("--no-register", action="store_true", help="do not auto-register the target workspace")
    add.add_argument("--no-push", action="store_true", help="commit but do not push datastore changes")
    add.add_argument("--no-codex-sync", action="store_true", help="do not update ~/.codex/skills")
    add.add_argument("--codex-prefix", default="keld")
    add.set_defaults(func=command_skill_add)
    update = skill_sub.add_parser("update", help="validate and replace an existing managed skill")
    update.add_argument("source", help="source skill directory or SKILL.md path")
    target = update.add_mutually_exclusive_group()
    target.add_argument("--workspace", help="update this workspace's .agents/skills; defaults to cwd")
    target.add_argument("--global", dest="global_skill", action="store_true", help="update ~/Documents/Projects/.agents/skills")
    update.add_argument("--name", help="target skill identity; defaults to the source SKILL.md name")
    update.add_argument("--no-register", action="store_true", help="do not auto-register the target workspace")
    update.add_argument("--no-push", action="store_true", help="commit but do not push datastore changes")
    update.add_argument("--no-codex-sync", action="store_true", help="do not update ~/.codex/skills")
    update.add_argument("--codex-prefix", default="keld")
    update.set_defaults(func=command_skill_update)
    directive = skill_sub.add_parser("directive", help="add or remove managed directives in a skill")
    directive_sub = directive.add_subparsers(dest="directive_command", required=True)
    directive_add = directive_sub.add_parser("add", help="append a titled directive to a managed skill")
    directive_add.add_argument("identity")
    directive_add.add_argument("--title", required=True)
    body = directive_add.add_mutually_exclusive_group(required=True)
    body.add_argument("--body")
    body.add_argument("--body-file")
    target = directive_add.add_mutually_exclusive_group()
    target.add_argument("--workspace", help="target this workspace's .agents/skills; defaults to cwd")
    target.add_argument("--global", dest="global_skill", action="store_true", help="target ~/Documents/Projects/.agents/skills")
    directive_add.add_argument("--no-register", action="store_true", help="do not auto-register the target workspace")
    directive_add.add_argument("--no-push", action="store_true", help="commit but do not push datastore changes")
    directive_add.add_argument("--no-codex-sync", action="store_true", help="do not update ~/.codex/skills")
    directive_add.add_argument("--codex-prefix", default="keld")
    directive_add.set_defaults(func=command_skill_directive)
    directive_remove = directive_sub.add_parser("remove", help="remove a titled managed directive from a skill")
    directive_remove.add_argument("identity")
    directive_remove.add_argument("--title", required=True)
    target = directive_remove.add_mutually_exclusive_group()
    target.add_argument("--workspace", help="target this workspace's .agents/skills; defaults to cwd")
    target.add_argument("--global", dest="global_skill", action="store_true", help="target ~/Documents/Projects/.agents/skills")
    directive_remove.add_argument("--no-register", action="store_true", help="do not auto-register the target workspace")
    directive_remove.add_argument("--no-push", action="store_true", help="commit but do not push datastore changes")
    directive_remove.add_argument("--no-codex-sync", action="store_true", help="do not update ~/.codex/skills")
    directive_remove.add_argument("--codex-prefix", default="keld")
    directive_remove.set_defaults(func=command_skill_directive)
    skill_sub.add_parser("list", help="list skill enablement flags").set_defaults(func=command_skill_list)

    archive = sub.add_parser("archive", help="intentionally move an active datastore skill to archive")
    archive.add_argument("workspace")
    archive.add_argument("source_kind", choices=["agents-skills", "agents-local"])
    archive.add_argument("identity")
    archive.add_argument("--codex-prefix", default="keld")
    archive.add_argument("--no-push", action="store_true")
    archive.set_defaults(func=command_archive_skill)

    delete_current = sub.add_parser(
        "delete-current",
        help="remove a skill from the current datastore set; git history is preserved",
    )
    delete_current.add_argument("workspace")
    delete_current.add_argument("source_kind", choices=["agents-skills", "agents-local"])
    delete_current.add_argument("identity")
    delete_current.add_argument("--confirm", required=True)
    delete_current.add_argument("--no-push", action="store_true")
    delete_current.set_defaults(func=command_delete_current_skill)

    install = sub.add_parser("install", help="install SkillsKeeper service runtime, state, and LaunchAgent")
    install.add_argument(
        "--package",
        help="wheel, source tree, or package spec to install non-editably into the service runtime",
    )
    install.add_argument(
        "--runtime-root",
        default=str(SERVICE_RUNTIME),
        help="service runtime root; defaults to ~/Library/Application Support/SkillsKeeper/service-runtime",
    )
    install.add_argument(
        "--runtime-python",
        default=sys.executable,
        help="Python executable used to create the service runtime venv",
    )
    install.add_argument(
        "--replace-runtime",
        action="store_true",
        help="recreate the service runtime venv before installing the package",
    )
    install.add_argument(
        "--skip-runtime-install",
        action="store_true",
        help="write state/plist only; requires an existing service executable",
    )
    install.add_argument("--datastore-path")
    install.add_argument("--datastore-remote")
    install.add_argument(
        "--migrate-datastore-from",
        help="copy an existing datastore into --datastore-path before install",
    )
    install.add_argument(
        "--replace-datastore",
        action="store_true",
        help="replace --datastore-path when migrating from another datastore",
    )
    install.add_argument("--debounce", type=float, default=1.0)
    install.add_argument("--no-push", action="store_true")
    install.add_argument("--no-load", action="store_false", dest="load")
    install.set_defaults(func=command_install, load=True)

    service = sub.add_parser("service", help="manage the LaunchAgent")
    service_sub = service.add_subparsers(dest="service_command", required=True)
    for name in ("start", "stop", "status"):
        service_sub.add_parser(name).set_defaults(func=command_service)

    datastore = sub.add_parser("datastore", help="manage the backing git datastore")
    datastore_sub = datastore.add_subparsers(dest="datastore_command", required=True)
    init = datastore_sub.add_parser("init", help="initialize the private datastore repo")
    init.add_argument("--path")
    init.add_argument("--remote")
    init.add_argument("--push", action="store_true")
    init.set_defaults(func=command_datastore_init)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeeperError as error:
        print(f"skillskeeper: {error.stage}: {error.message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
