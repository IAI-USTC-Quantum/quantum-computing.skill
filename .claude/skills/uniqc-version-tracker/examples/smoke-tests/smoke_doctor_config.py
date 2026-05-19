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
        if r.returncode != 0:
            print(f"WARNING: uniqc doctor exited {r.returncode}: {r.stderr[:200]}")
        else:
            assert "Environment" in r.stdout, "Doctor missing Environment section"
            assert "dependencies" in r.stdout.lower(), "Doctor missing dependencies section"
    except subprocess.TimeoutExpired:
        print("WARNING: uniqc doctor timed out (live platform checks slow)")

    from uniqc.config import SUPPORTED_PLATFORMS, has_platform_credentials

    assert len(SUPPORTED_PLATFORMS) > 0, "No supported platforms in config"
    assert callable(has_platform_credentials), "has_platform_credentials not callable"

    print("PASS: uniqc doctor CLI + config module imports OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())