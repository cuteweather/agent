#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parent.parent
SKILLS_JSON = ROOT / "skills.json"
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"Authorization:\s*[A-Za-z0-9._-]{16,}"),
]


def parse_frontmatter(skill_file: Path) -> Dict[str, str]:
    text = skill_file.read_text(encoding="utf-8")
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        raise ValueError(f"Missing YAML frontmatter: {skill_file}")

    frontmatter: Dict[str, str] = {}
    closed = False
    for line in lines[1:]:
        if line.strip() == "---":
            closed = True
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip()

    if not closed:
        raise ValueError(f"Unclosed YAML frontmatter: {skill_file}")
    if "name" not in frontmatter or "description" not in frontmatter:
        raise ValueError(f"Incomplete frontmatter: {skill_file}")
    return frontmatter


def collect_skills() -> List[Dict[str, object]]:
    skills = []
    for entry in sorted(ROOT.iterdir(), key=lambda p: p.name.lower()):
        if not entry.is_dir():
            continue
        skill_file = entry / "SKILL.md"
        if not skill_file.exists():
            continue
        meta = parse_frontmatter(skill_file)
        skills.append(
            {
                "folder": entry.name,
                "name": meta["name"],
                "description": meta["description"],
                "has_scripts": (entry / "scripts").is_dir(),
                "has_references": (entry / "references").is_dir(),
                "has_assets": (entry / "assets").is_dir(),
            }
        )
    return skills


def check_skills_json(expected_skills: List[Dict[str, object]]) -> None:
    if not SKILLS_JSON.exists():
        raise ValueError("Missing skills.json")
    payload = json.loads(SKILLS_JSON.read_text(encoding="utf-8"))
    if payload.get("count") != len(expected_skills):
        raise ValueError("skills.json count does not match current skills")
    if payload.get("skills") != expected_skills:
        raise ValueError("skills.json is out of date; run scripts/generate_skill_index.py")


def scan_for_secrets() -> None:
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf"}:
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            match = pattern.search(text)
            if match:
                raise ValueError(f"Potential secret pattern in {path}: {match.group(0)[:24]}...")


def main() -> int:
    skills = collect_skills()
    check_skills_json(skills)
    scan_for_secrets()
    print(f"Repository check passed for {len(skills)} skill(s).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
