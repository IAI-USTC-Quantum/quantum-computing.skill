# Install & extras layout (uniqc 0.0.13)

## What plain `pip install unified-quantum` already gives you

Core dependencies (always installed):

- `numpy`, `scipy`, `typer`, `rich`, `pyyaml`
- **`qiskit`, `qiskit-aer`, `qiskit-ibm-runtime`** — promoted to core in
  0.0.13 (the old `[qiskit]` extra has been **removed**).

Net effect: a plain install is enough for **compile**, **IBM Quantum**,
and **chip-backed dummy backends** (`dummy:originq:<chip>`,
`dummy:quark:<chip>`).

## Optional extras to install on demand

| Use case                                | Command                                              |
| --------------------------------------- | ---------------------------------------------------- |
| OriginQ real hardware / cloud sim       | `pip install unified-quantum[originq]`              |
| Quark real hardware (Python ≥ 3.12)     | `pip install unified-quantum[quark]`                |
| TianYan real hardware / cloud sims      | `pip install unified-quantum[tianyan]`              |
| LogicalQubit real hardware              | `pip install unified-quantum[logicalqubit]`         |
| Density-matrix sim with `qutip`         | `pip install unified-quantum[simulation]`           |
| Plotting (matplotlib / pandas)          | `pip install unified-quantum[visualization]`        |
| PyTorch QML (`torch`)                   | `pip install unified-quantum[pytorch]`              |
| Everything (all extras above)           | `pip install unified-quantum[all]`                  |

Quafu has no install path: the platform was **removed in 0.1.0**. Since
0.1.0 `unified-quantum` is a pure-Python wheel — the C++ simulator kernel
ships as the `uniqc-cppsimulator` dependency, so no CMake or C++
toolchain is needed to install or build.

## Workflow

1. `uniqc doctor` — see which group is "not installed".
2. Pick the matching `pip install ...` line above.
3. Re-run `uniqc doctor` — the table line for that group should now
   show the installed version.
4. If the group involves a cloud platform, `uniqc backend update
   --platform <p>` to refresh the local chip cache.
5. `uniqc config validate` — last sanity check.

## Common install pitfalls

- **`qiskit` not importable after install** — the env is broken; `pip
  install --upgrade unified-quantum`. Don't reach for `[qiskit]` —
  that extra no longer exists.
- **`pyqpanda3` wheel not available for your Python** — check the
  doctor's "Python" line; OriginQ wheels lag the latest minor Python.
  Pin Python to 3.10–3.12 if needed.
- **`numpy<2` constraint (historical)** — this was a `pyquafu` problem;
  Quafu support is gone in 0.1.0 and the constraint no longer applies to
  any supported extra.
- **CLI `uniqc` not on PATH** — you used `pip install` instead of `uv
  tool install`, and the venv isn't activated. Activate, or
  `python -m uniqc.cli ...`.
- **`uv tool install unified-quantum`** is the cleanest CLI install
  (isolated environment, no leakage into the project venv).

## Inside-Python fallback

If the user really cannot run `uniqc doctor` (e.g., remote node, no
TTY), do this:

```python
from importlib.metadata import version, PackageNotFoundError

GROUPS = {
    "core":          ["numpy", "scipy", "typer", "rich", "pyyaml",
                      "qiskit", "qiskit-aer", "qiskit-ibm-runtime"],
    "originq":       ["pyqpanda3"],
    "quark":         ["quarkstudio", "quarkcircuit"],
    "tianyan":       ["cqlib"],
    "logicalqubit":  ["lqcloud"],
    "simulation":    ["qutip"],
    "visualization": ["matplotlib"],
    "pytorch":       ["torch"],
}

for group, pkgs in GROUPS.items():
    print(f"== {group} ==")
    for pkg in pkgs:
        try:
            print(f"  {pkg:<24} {version(pkg)}")
        except PackageNotFoundError:
            print(f"  {pkg:<24} NOT INSTALLED")
```
