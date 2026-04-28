#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Iterable, List


ROOT = Path(__file__).resolve().parent.parent


def discover_skills() -> List[Path]:
    return sorted(
        [path for path in ROOT.iterdir() if path.is_dir() and (path / "SKILL.md").exists()],
        key=lambda p: p.name.lower(),
    )


def resolve_target(path_arg: str | None) -> Path:
    if path_arg:
        return Path(path_arg).expanduser().resolve()
    return (Path.home() / ".codex" / "skills").resolve()


def select_skills(all_skills: Iterable[Path], requested: List[str]) -> List[Path]:
    all_skills = list(all_skills)
    if not requested:
        return all_skills

    by_name = {path.name: path for path in all_skills}
    missing = [name for name in requested if name not in by_name]
    if missing:
        names = ", ".join(sorted(by_name))
        missing_names = ", ".join(missing)
        raise SystemExit(f"Unknown skill(s): {missing_names}\nAvailable: {names}")

    return [by_name[name] for name in requested]


def install_one(source: Path, target_root: Path, force: bool) -> None:
    destination = target_root / source.name
    if destination.exists():
        if not force:
            raise SystemExit(f"Destination already exists: {destination}\nUse --force to overwrite.")
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    print(f"Installed {source.name} -> {destination}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install skills from this repository into a target skills directory.")
    parser.add_argument("skills", nargs="*", help="Optional list of skill folder names to install.")
    parser.add_argument("--target", default=None, help="Target directory. Defaults to ~/.codex/skills")
    parser.add_argument("--force", action="store_true", help="Overwrite existing installed skills.")
    args = parser.parse_args()

    target_root = resolve_target(args.target)
    target_root.mkdir(parents=True, exist_ok=True)

    available = discover_skills()
    selected = select_skills(available, args.skills)
    for skill in selected:
        install_one(skill, target_root, args.force)

    print(f"Installed {len(selected)} skill(s) into {target_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
