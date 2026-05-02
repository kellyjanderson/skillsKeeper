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
from typing import Any, Iterable


APP_SUPPORT = Path.home() / "Library" / "Application Support" / "SkillsKeeper"
STATE_PATH = APP_SUPPORT / "state.json"
DEFAULT_DATASTORE = APP_SUPPORT / "datastore"
PROJECTS_SKILLS = Path.home() / "Documents" / "Projects" / ".agents" / "skills"
CODEX_SKILLS = Path.home() / ".codex" / "skills"
SKIP_FILENAMES = {".system-skills-composer.json", ".composer-state.json"}


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


def slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    return cleaned or "workspace"


def read_state(path: Path = STATE_PATH) -> dict[str, Any]:
    if not path.exists():
        return {
            "version": 1,
            "datastore": str(DEFAULT_DATASTORE),
            "workspaces": [],
        }
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise KeeperError("state-read", f"failed to read {path}: {error}") from error


def write_state(state: dict[str, Any], path: Path = STATE_PATH) -> None:
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


def run_git(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=check)


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


def copy_tree_clean(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    def ignore(_dir: str, names: list[str]) -> set[str]:
        return {name for name in names if ignore_copy_entry(Path(name))}
    shutil.copytree(src, dst, ignore=ignore)


def workspace_key(workspace: Path) -> str:
    try:
        rel = workspace.relative_to(Path.home())
        return slug(str(rel))
    except ValueError:
        return slug(str(workspace))


def archive_workspace(datastore: Path, workspace: Path) -> int:
    count = 0
    root = datastore / "registered" / workspace_key(workspace)
    for source in discover_skill_sources(workspace):
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
    return count


def sync_all(push: bool = True) -> tuple[int, bool, bool]:
    state = read_state()
    datastore = datastore_path(state)
    ensure_git_repo(datastore)
    total = 0
    for workspace in registered_workspaces(state):
        total += archive_workspace(datastore, workspace)
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


def copy_projects_skills_to_codex(prefix: str = "keld") -> int:
    if not PROJECTS_SKILLS.is_dir():
        raise KeeperError("codex-sync", f"projects skills root does not exist: {PROJECTS_SKILLS}")
    CODEX_SKILLS.mkdir(parents=True, exist_ok=True)
    count = 0
    for skill_file in sorted(PROJECTS_SKILLS.glob("*/SKILL.md")):
        src_dir = skill_file.parent
        source_name = parse_skill_name(skill_file)
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
    print(f"archived skills: {total}")
    print(f"committed: {str(committed).lower()}")
    print(f"pushed: {str(pushed).lower()}")
    return 0


def command_codex_sync(args: argparse.Namespace) -> int:
    count = copy_projects_skills_to_codex(prefix=args.prefix)
    print(f"copied skills: {count}")
    print(f"target: {CODEX_SKILLS}")
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
            print(f"event sync: {total} skills, committed={committed}, pushed={pushed}", flush=True)

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

    sub.add_parser("list", help="list registered workspaces").set_defaults(func=command_list)
    sub.add_parser("status", help="show state and datastore status").set_defaults(func=command_status)

    sync = sub.add_parser("sync", help="archive registered skills now")
    sync.add_argument("--no-push", action="store_true", help="commit but do not push datastore changes")
    sync.set_defaults(func=command_sync)

    watch = sub.add_parser("watch", help="watch registered workspaces using filesystem events")
    watch.add_argument("--debounce", type=float, default=1.0)
    watch.add_argument("--no-push", action="store_true", help="commit but do not push datastore changes")
    watch.set_defaults(func=command_watch)

    codex = sub.add_parser("codex-sync", help="copy Projects-level skills into ~/.codex/skills with a namespace")
    codex.add_argument("--prefix", default="keld")
    codex.set_defaults(func=command_codex_sync)

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
