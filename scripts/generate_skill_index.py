#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "skills.json"


def parse_frontmatter(skill_file: Path) -> Dict[str, str]:
    text = skill_file.read_text(encoding="utf-8")
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        raise ValueError(f"Missing YAML frontmatter: {skill_file}")

    frontmatter: Dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip()

    if "name" not in frontmatter or "description" not in frontmatter:
        raise ValueError(f"Incomplete frontmatter: {skill_file}")
    return frontmatter


def build_index() -> List[Dict[str, object]]:
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


def main() -> int:
    skills = build_index()
    payload = {
        "count": len(skills),
        "skills": skills,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(skills)} skills to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
