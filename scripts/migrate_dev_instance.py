#!/usr/bin/env python3
"""Migrate a development-coupled SkillsKeeper instance into app support.

The script is intentionally conservative. It copies stateful data by default,
backs up state.json before changing it, and refuses to replace an existing
non-empty destination unless explicitly requested.
"""

from __future__ import annotations

import argparse
import json
import plistlib
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


HOME = Path.home()
APP_SUPPORT = HOME / "Library" / "Application Support" / "SkillsKeeper"
STATE_PATH = APP_SUPPORT / "state.json"
DEFAULT_SOURCE_DATASTORE = HOME / "Documents" / "Projects" / "skillsKeeper-datastore"
DEFAULT_DEST_DATASTORE = APP_SUPPORT / "datastore"
PLIST_PATH = HOME / "Library" / "LaunchAgents" / "com.kellyjanderson.skillskeeper.plist"
DEFAULT_RELEASE_BIN = APP_SUPPORT / "service-runtime" / ".venv" / "bin" / "skillskeeper"
LOG_DIR = HOME / "Library" / "Logs" / "SkillsKeeper"
SERVICE_LABEL = "com.kellyjanderson.skillskeeper"
DEFAULT_SERVICE_PATH = f"{HOME}/.local/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"


def timestamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def read_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "version": 1,
            "datastore": str(DEFAULT_DEST_DATASTORE),
            "workspaces": [],
            "skill_flags": {"global": {}, "workspaces": {}},
        }
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def non_empty(path: Path) -> bool:
    return path.exists() and any(path.iterdir())


def copy_datastore(source: Path, dest: Path, *, replace: bool, dry_run: bool) -> str:
    if not source.exists():
        return "source-missing"
    if non_empty(dest):
        if not replace:
            return "destination-exists"
        if not dry_run:
            shutil.rmtree(dest)
    if dry_run:
        return "would-copy"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, dest, symlinks=True)
    return "copied"


def backup_file(path: Path, *, dry_run: bool) -> Path | None:
    if not path.exists():
        return None
    backup = path.with_name(f"{path.name}.backup-{timestamp()}")
    if not dry_run:
        shutil.copy2(path, backup)
    return backup


def install_plist(release_bin: Path, *, dry_run: bool) -> Path | None:
    backup = backup_file(PLIST_PATH, dry_run=dry_run)
    plist = {
        "Label": SERVICE_LABEL,
        "ProgramArguments": [
            str(release_bin),
            "watch",
            "--debounce",
            "1.0",
        ],
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardOutPath": str(LOG_DIR / f"{SERVICE_LABEL}.out.log"),
        "StandardErrorPath": str(LOG_DIR / f"{SERVICE_LABEL}.err.log"),
        "EnvironmentVariables": {
            "PYTHONUNBUFFERED": "1",
            "PATH": DEFAULT_SERVICE_PATH,
        },
    }
    if not dry_run:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
        with PLIST_PATH.open("wb") as handle:
            plistlib.dump(plist, handle)
    return backup


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-datastore", type=Path, default=DEFAULT_SOURCE_DATASTORE)
    parser.add_argument("--dest-datastore", type=Path, default=DEFAULT_DEST_DATASTORE)
    parser.add_argument("--release-bin", type=Path, default=DEFAULT_RELEASE_BIN)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--replace-datastore", action="store_true")
    parser.add_argument("--write-plist", action="store_true")
    parser.add_argument("--manifest", type=Path, default=APP_SUPPORT / "migration-manifest.json")
    args = parser.parse_args(argv)

    state = read_state(STATE_PATH)
    original_datastore = state.get("datastore")
    datastore_result = copy_datastore(
        args.source_datastore.expanduser(),
        args.dest_datastore.expanduser(),
        replace=args.replace_datastore,
        dry_run=args.dry_run,
    )
    if datastore_result == "destination-exists":
        print(f"destination datastore already exists: {args.dest_datastore}", file=sys.stderr)
        print("rerun with --replace-datastore if replacing it is intended", file=sys.stderr)
        return 2

    state_backup = backup_file(STATE_PATH, dry_run=args.dry_run)
    state["datastore"] = str(args.dest_datastore.expanduser())
    if not args.dry_run:
        write_json(STATE_PATH, state)

    plist_backup = install_plist(args.release_bin.expanduser(), dry_run=args.dry_run) if args.write_plist else None

    manifest = {
        "timestamp": timestamp(),
        "dry_run": args.dry_run,
        "source_datastore": str(args.source_datastore.expanduser()),
        "dest_datastore": str(args.dest_datastore.expanduser()),
        "datastore_action": datastore_result,
        "state_path": str(STATE_PATH),
        "state_backup": str(state_backup) if state_backup else None,
        "original_datastore": original_datastore,
        "new_datastore": state["datastore"],
        "plist_path": str(PLIST_PATH) if args.write_plist else None,
        "plist_backup": str(plist_backup) if plist_backup else None,
        "release_bin": str(args.release_bin.expanduser()),
    }
    if not args.dry_run:
        write_json(args.manifest.expanduser(), manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
