"""Report version alignment between installed uniqc and repo CLAUDE.md.

Usage:
    python detect_version.py [--repo-path /path/to/quantum-computing.skill]
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description="Detect uniqc version alignment.")
    ap.add_argument("--repo-path", default=".")
    args = ap.parse_args()

    repo = Path(args.repo_path).resolve()
    claude_md = repo / "CLAUDE.md"
    if not claude_md.exists():
        sys.exit(f"CLAUDE.md not found at {claude_md}")

    text = claude_md.read_text()
    m = re.search(r"UnifiedQuantum\s+v?(\d+\.\d+\.\d+)", text)
    baseline = m.group(1) if m else "unknown"

    r = subprocess.run(
        [sys.executable, "-c", "import uniqc; print(uniqc.__version__)"],
        capture_output=True,
        text=True,
    )
    installed = r.stdout.strip() if r.returncode == 0 else "NOT INSTALLED"

    print(f"Repo CLAUDE.md baseline: v{baseline}")
    if installed != "NOT INSTALLED":
        print(f"Installed uniqc:         v{installed}")
    else:
        print(f"Installed uniqc:         {installed}")

    if installed == "NOT INSTALLED":
        print("\nuniqc is not installed. Install it to detect version gaps.")
        sys.exit(1)
    elif baseline == "unknown":
        print("\nCannot determine repo baseline.")
    elif installed != baseline:
        print(f"\nGAP: repo claims v{baseline}, installed is v{installed}")
    else:
        print("\nAligned.")


if __name__ == "__main__":
    main()