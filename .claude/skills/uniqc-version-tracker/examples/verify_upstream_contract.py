"""Verify the Skill's release contracts against an upstream UnifiedQuantum checkout."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from functools import cache
from pathlib import Path


@cache
def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def source_index(root: Path) -> str:
    return "\n".join(
        read_text(path)
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.parts and path.suffix in {".md", ".py", ".toml", ".yml", ".yaml"}
    )


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-path", required=True, type=Path, help="UnifiedQuantum checkout")
    parser.add_argument("--expected-commit", default="d1794d1", help="v0.0.17 contract commit")
    args = parser.parse_args()

    repo = args.repo_path.resolve()
    checks: dict[str, bool] = {}
    details: dict[str, str] = {}
    pyproject = repo / "pyproject.toml"

    if not (repo / ".git").exists() or not pyproject.is_file():
        summary = {"ok": False, "checks": {}, "error": f"not a UnifiedQuantum checkout: {repo}"}
        print(json.dumps(summary, sort_keys=True))
        return 1

    head = git(repo, "rev-parse", "HEAD")
    details["head"] = head.stdout.strip() if head.returncode == 0 else "unknown"
    ancestor = git(repo, "merge-base", "--is-ancestor", args.expected_commit, "HEAD")
    checks["v0.0.17_contract_commit"] = ancestor.returncode == 0

    pyproject_text = read_text(pyproject)
    upstream_text = source_index(repo)
    cli_text = source_index(repo / "uniqc" / "cli")
    python_match = re.search(r'^requires-python\s*=\s*"([^"]+)"', pyproject_text, re.MULTILINE)
    pytorch_match = re.search(r'^pytorch\s*=\s*\[([^\]]*)\]', pyproject_text, re.MULTILINE)
    requires_python = python_match.group(1) if python_match else ""
    pytorch_extra = pytorch_match.group(1) if pytorch_match else ""
    checks["python_range"] = requires_python == ">=3.10,<3.15"
    checks["pytorch_extra"] = '"torch"' in pytorch_extra and '"torchquantum-ng"' in pytorch_extra
    checks["cmake_minimum"] = "cmake_minimum_required(VERSION 3.22)" in read_text(repo / "CMakeLists.txt")

    checks["cache_and_config_paths"] = all(
        value in upstream_text
        for value in ("~/.uniqc/config.yaml", "~/.uniqc/backend/backends.json", "~/.uniqc/backend/chips/")
    )
    checks["backend_grammar"] = "dummy:virtual:<name>" in upstream_text
    checks["virtual_lifecycle"] = all(
        f'@app.command("{command}")' in cli_text
        for command in ("init", "list", "show", "validate")
    )
    checks["submit_cli_backend"] = "--backend" in cli_text
    checks["cloud_tests_opt_in"] = "--real-cloud-test" in upstream_text and 'not cloud' in upstream_text
    checks["deprecation_cliff"] = "0.1.0" in upstream_text and "DeprecationWarning" in upstream_text

    summary = {
        "ok": all(checks.values()),
        "expected_commit": args.expected_commit,
        "details": details,
        "checks": checks,
    }
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
