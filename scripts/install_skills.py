#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import Iterable, List


ROOT = Path(__file__).resolve().parent.parent


def safe_print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        encoded = text.encode(sys.stdout.encoding or "utf-8", errors="replace")
        decoded = encoded.decode(sys.stdout.encoding or "utf-8", errors="replace")
        print(decoded)


def discover_skills() -> List[Path]:
    return sorted(
        [path for path in ROOT.iterdir() if path.is_dir() and (path / "SKILL.md").exists()],
        key=lambda p: p.name.lower(),
    )


def parse_frontmatter(skill_file: Path) -> dict[str, str]:
    frontmatter: dict[str, str] = {}
    lines = skill_file.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return frontmatter

    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip()
    return frontmatter


def default_target_root() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return (Path(codex_home).expanduser().resolve() / "skills").resolve()
    return (Path.home() / ".codex" / "skills").resolve()


def resolve_target(path_arg: str | None) -> Path:
    if path_arg:
        return Path(path_arg).expanduser().resolve()
    return default_target_root()


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
    safe_print(f"Installed {source.name} -> {destination}")


def print_skill_list(skills: Iterable[Path]) -> None:
    for skill in skills:
        meta = parse_frontmatter(skill / "SKILL.md")
        description = meta.get("description", "")
        safe_print(f"{skill.name}: {description}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install skills from this repository into a target skills directory.")
    parser.add_argument("skills", nargs="*", help="Optional list of skill folder names to install.")
    parser.add_argument(
        "--target",
        default=None,
        help="Target directory. Defaults to $CODEX_HOME/skills when CODEX_HOME is set, otherwise ~/.codex/skills",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing installed skills.")
    parser.add_argument("--list", action="store_true", help="List available skills and exit.")
    args = parser.parse_args()

    available = discover_skills()
    if args.list:
        print_skill_list(available)
        return 0

    target_root = resolve_target(args.target)
    target_root.mkdir(parents=True, exist_ok=True)

    selected = select_skills(available, args.skills)
    for skill in selected:
        install_one(skill, target_root, args.force)

    safe_print(f"Installed {len(selected)} skill(s) into {target_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
