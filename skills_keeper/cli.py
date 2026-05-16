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
LAUNCHD_LABEL = "com.kellyjanderson.skillskeeper"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"
LOG_DIR = Path.home() / "Library" / "Logs" / "SkillsKeeper"
ARCHIVED_DIRNAME = "archived"
REGISTERED_DIRNAME = "registered"
DEFAULT_SERVICE_PATH = "/Users/k/.local/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"


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


def timestamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


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


def workspace_key(workspace: Path) -> str:
    try:
        rel = workspace.relative_to(Path.home())
        return slug(str(rel))
    except ValueError:
        return slug(str(workspace))


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


def archive_workspace(datastore: Path, workspace: Path) -> int:
    count = 0
    root = datastore / REGISTERED_DIRNAME / workspace_key(workspace)
    sources = discover_skill_sources(workspace)
    seen: set[tuple[str, str]] = set()
    for source in sources:
        key = (source.source_kind, slug(source.identity))
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
        if key not in seen and active_path.exists():
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


def command_archive_skill(args: argparse.Namespace) -> int:
    state = read_state()
    datastore = datastore_path(state)
    workspace = resolve_path(args.workspace)
    active = resolve_active_skill(datastore, workspace, args.source_kind, args.identity)
    archived = move_active_skill_to_archive(datastore, active, reason="intentional")
    committed, pushed = commit_and_maybe_push(
        datastore,
        f"Archive skill {args.identity} from {workspace_key(workspace)}",
        push=not args.no_push,
    )
    print(f"archived: {archived}")
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


def service_program() -> Path:
    return Path(sys.argv[0]).resolve()


def install_launch_agent(args: argparse.Namespace) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    program = str(service_program())
    plist = {
        "Label": LAUNCHD_LABEL,
        "ProgramArguments": [
            program,
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


def launchctl(args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["launchctl", *args], text=True, capture_output=True, check=check)


def command_install(args: argparse.Namespace) -> int:
    state = read_state()
    datastore = datastore_path(state)
    ensure_git_repo(datastore, remote=args.datastore_remote)
    if args.datastore_path:
        state["datastore"] = str(resolve_path(args.datastore_path))
        datastore = datastore_path(state)
        ensure_git_repo(datastore, remote=args.datastore_remote)
    inferred = infer_workspaces_from_datastore(datastore) if datastore.exists() else []
    state, added = merge_registered_workspaces(state, inferred)
    write_state(state)
    install_launch_agent(args)
    if args.load:
        launchctl(["bootout", f"gui/{os.getuid()}", str(PLIST_PATH)], check=False)
        result = launchctl(["bootstrap", f"gui/{os.getuid()}", str(PLIST_PATH)], check=False)
        if result.returncode != 0:
            raise KeeperError("launchd", result.stderr.strip() or result.stdout.strip())
        launchctl(["enable", f"gui/{os.getuid()}/{LAUNCHD_LABEL}"], check=False)
    print(f"state: {STATE_PATH}")
    print(f"datastore: {datastore}")
    print(f"plist: {PLIST_PATH}")
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

    archive = sub.add_parser("archive", help="intentionally move an active datastore skill to archive")
    archive.add_argument("workspace")
    archive.add_argument("source_kind", choices=["agents-skills", "agents-local"])
    archive.add_argument("identity")
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

    install = sub.add_parser("install", help="install SkillsKeeper state and LaunchAgent")
    install.add_argument("--datastore-path")
    install.add_argument("--datastore-remote")
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
