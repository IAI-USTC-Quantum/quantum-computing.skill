"""Parse upstream CHANGELOG.md for a specific version's change sections.

Usage:
    python parse_changelog.py <version> --changelog-path ../UnifiedQuantum/CHANGELOG.md
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def extract_section(text: str, version: str) -> dict[str, list[str]]:
    """Extract Added/Fixed/Changed/Breaking bullet lists for a version block."""
    pattern = rf"^## \[{re.escape(version)}\].*$.*?(?=^## \[|\Z)"
    m = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    if not m:
        return {}
    block = m.group(0)

    sections: dict[str, list[str]] = {}
    for label, key in [
        ("### ⚠ BREAKING", "breaking"),
        ("### Added", "added"),
        ("### Fixed", "fixed"),
        ("### Changed", "changed"),
    ]:
        sec_m = re.search(rf"{re.escape(label)}\n(.*?)(?=### |\Z)", block, re.DOTALL)
        if sec_m:
            bullets = re.findall(
                r"^- \*?\*?(.+?)(?:\n|$)", sec_m.group(1), re.MULTILINE
            )
            sections[key] = [b.strip() for b in bullets]
    return sections


def main() -> None:
    ap = argparse.ArgumentParser(description="Parse changelog for a version.")
    ap.add_argument("version", help="Version number, e.g. 0.0.14")
    ap.add_argument("--changelog-path", required=True, help="Path to upstream CHANGELOG.md")
    args = ap.parse_args()

    cl = Path(args.changelog_path)
    if not cl.exists():
        sys.exit(f"CHANGELOG.md not found at {cl}")

    sections = extract_section(cl.read_text(), args.version)
    for key, label in [
        ("breaking", "BREAKING"),
        ("added", "Added"),
        ("fixed", "Fixed"),
        ("changed", "Changed"),
    ]:
        items = sections.get(key, [])
        if items:
            print(f"\n### {label} ({len(items)} items)")
            for item in items:
                print(f"  - {item[:120]}{'...' if len(item) > 120 else ''}")
        else:
            print(f"\n### {label} (none)")

    if not sections:
        print(f"\nVersion [{args.version}] not found in changelog.")


if __name__ == "__main__":
    main()