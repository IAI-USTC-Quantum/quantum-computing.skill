"""Validate local links and required Skill metadata without network access."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)\s]+)(?:\s+['\"][^)]*['\"])?\)")
REQUIRED_FRONT_MATTER = ("name", "description")


def find_skill_files(root: Path) -> list[Path]:
    return sorted(
        path
        for directory in (root / "skills", root / ".claude" / "skills")
        if directory.is_dir()
        for path in directory.rglob("SKILL.md")
    )


def parse_front_matter(path: Path) -> tuple[dict[str, str], list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        return {}, ["missing YAML front matter"]
    try:
        end = lines.index("---", 1)
    except ValueError:
        return {}, ["unterminated YAML front matter"]

    fields: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line or line.startswith((" ", "\t", "#")):
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip("\"'")

    errors = [
        f"front matter field {field!r} is missing or empty"
        for field in REQUIRED_FRONT_MATTER
        if not fields.get(field)
    ]
    return fields, errors


def local_link_errors(root: Path, path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    for raw_target in LINK_RE.findall(text):
        target = unquote(raw_target.strip("<>"))
        parsed = urlparse(target)
        if parsed.scheme or parsed.netloc or target.startswith(("#", "/", "mailto:")):
            continue
        local_path = parsed.path
        if not local_path:
            continue
        destination = (path.parent / local_path).resolve()
        try:
            destination.relative_to(root)
        except ValueError:
            errors.append(f"{path.relative_to(root)}: link escapes repository: {raw_target}")
            continue
        if not destination.exists():
            errors.append(f"{path.relative_to(root)}: missing local link target: {raw_target}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-path",
        type=Path,
        default=Path(__file__).resolve().parents[4],
        help="Skill repository root (defaults to this script's repository)",
    )
    parser.add_argument("--json", action="store_true", help="Emit only a JSON summary.")
    args = parser.parse_args()

    root = args.repo_path.resolve()
    errors: list[str] = []
    skill_files = find_skill_files(root)
    if not skill_files:
        errors.append("no SKILL.md files found under skills/ or .claude/skills/")

    for path in skill_files:
        _, front_matter_errors = parse_front_matter(path)
        errors.extend(f"{path.relative_to(root)}: {error}" for error in front_matter_errors)

    for path in sorted(root.rglob("*.md")):
        if ".git" not in path.parts:
            errors.extend(local_link_errors(root, path))

    summary = {
        "ok": not errors,
        "skill_files": len(skill_files),
        "markdown_files": sum(1 for path in root.rglob("*.md") if ".git" not in path.parts),
        "errors": errors,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    else:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
