"""Smoke test for uniqc-doctor-config.
Tests: uniqc doctor CLI, config module imports.
"""
import sys
import subprocess
from pathlib import Path


def main() -> int:
    uniqc_bin = str(Path(sys.executable).parent / "uniqc")
    try:
        r = subprocess.run([uniqc_bin, "doctor"], capture_output=True, text=True, timeout=25)
        assert r.returncode == 0, f"uniqc doctor exited {r.returncode}: {r.stderr[:200]}"
        assert "Environment" in r.stdout, "Doctor missing Environment section"
        assert "dependencies" in r.stdout.lower(), "Doctor missing dependencies section"
    except subprocess.TimeoutExpired:
        raise AssertionError("uniqc doctor timed out") from None

    from uniqc.config import SUPPORTED_PLATFORMS, has_platform_credentials

    assert len(SUPPORTED_PLATFORMS) > 0, "No supported platforms in config"
    assert callable(has_platform_credentials), "has_platform_credentials not callable"

    print("PASS: uniqc doctor CLI + config module imports OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())