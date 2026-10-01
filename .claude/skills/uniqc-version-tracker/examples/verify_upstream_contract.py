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
    parser.add_argument(
        "--expected-commit",
        default="d93372448e369bb0e33635f387e0aa5307d42601",
        help="v0.1.1 release contract commit",
    )
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
    checks["v0.1.1_contract_commit"] = ancestor.returncode == 0

    pyproject_text = read_text(pyproject)
    upstream_text = source_index(repo)
    cli_text = source_index(repo / "uniqc" / "cli")
    config_text = read_text(repo / "uniqc" / "config.py")
    python_match = re.search(r'^requires-python\s*=\s*"([^"]+)"', pyproject_text, re.MULTILINE)
    pytorch_match = re.search(r'^pytorch\s*=\s*\[([^\]]*)\]', pyproject_text, re.MULTILINE)
    requires_python = python_match.group(1) if python_match else ""
    pytorch_extra = pytorch_match.group(1) if pytorch_match else ""
    checks["python_range"] = requires_python == ">=3.10,<3.15"
    checks["pytorch_extra"] = '"torch"' in pytorch_extra and '"torchquantum-ng"' in pytorch_extra

    # C++ kernel split: pure-Python wheel + standalone uniqc-cppsimulator dep.
    checks["cppsimulator_dep"] = '"uniqc-cppsimulator>=1.0.1,<2"' in pyproject_text
    checks["no_cmake"] = not (repo / "CMakeLists.txt").exists()

    # 0.1.0 removals: Quafu gone (no quafu-named module, no Platform.QUAFU, no pyquafu dep).
    package_text = "\n".join(
        read_text(path) for path in (repo / "uniqc").rglob("*.py")
    )
    checks["quafu_removed"] = (
        "quafu" not in pyproject_text.lower()
        and not any("quafu" in path.name.lower() for path in (repo / "uniqc").rglob("*.py"))
        and "Platform.QUAFU" not in package_text
    )

    # New platforms + extras (tianyan / logicalqubit).
    checks["new_platform_extras"] = 'tianyan = ["cqlib"]' in pyproject_text and 'logicalqubit = ["lqcloud"]' in pyproject_text

    # Config schema versioning.
    checks["config_version"] = "CURRENT_CONFIG_VERSION" in config_text and "config_version" in config_text

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
    checks["deprecation_policy"] = "0.1.0" in upstream_text and "DeprecationWarning" in upstream_text

    # 0.1.1: self-developed circuit rendering engine behind one layout core.
    render_pkg = repo / "uniqc" / "visualization" / "circuit_render"
    render_init_text = read_text(render_pkg / "__init__.py")
    render_options_text = read_text(render_pkg / "options.py")
    qcircuit_text = read_text(repo / "uniqc" / "circuit_builder" / "qcircuit.py")
    cli_main_text = read_text(repo / "uniqc" / "cli" / "main.py")
    legacy_viz_text = read_text(repo / "uniqc" / "visualization" / "circuit.py")
    checks["render_engine"] = "def render(" in render_init_text and "from uniqc.visualization.circuit_render import render" in qcircuit_text
    checks["render_modes"] = 'MODES = ("text", "svg", "png", "mpl", "latex", "html", "interactive")' in render_options_text
    checks["circuit_to_matrix"] = "def to_matrix" in qcircuit_text and "NotMatrixableError" in qcircuit_text
    checks["draw_cli"] = 'app.command("draw"' in cli_main_text and (repo / "uniqc" / "cli" / "draw.py").is_file()
    checks["legacy_draw_deprecated"] = "warn_removed_in_0_2_0" in legacy_viz_text and "0.2.0" in legacy_viz_text

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
