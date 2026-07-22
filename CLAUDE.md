# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is an AI Agent Skills collection for **UnifiedQuantum** (quantum computing SDK). Skills provide practical, runnable guidance for quantum computing workflows including circuit building, simulation, calibration, cloud submission, and algorithm development.

## Skills Structure

Each skill follows a consistent directory structure:
```
skills/<skill-name>/
├── SKILL.md           # Main entry point with description, patterns, and examples
├── references/        # Topic-specific documentation (circuit-building.md, simulators.md, etc.)
├── examples/          # Runnable Python scripts demonstrating key workflows
└── agents/            # Agent metadata (openai.yaml for SkillHub/OpenAI interface)
```

## Key Skills

- **uniqc-basic-usage** — Entry point covering installation, circuit building, simulation, CLI, config, `uniqc doctor`
- **uniqc-cloud-submit** — Real device submission workflows (OriginQ, IBM, Quark)
- **uniqc-result-analysis** — UnifiedResult parsing, counts/probabilities, visualization
- **uniqc-xeb-qem** — XEB benchmarking (1q/2q/parallel-CZ) and readout error mitigation
- **uniqc-circuit-interop** — Cross-format conversion (Circuit/OriginIR/QASM2/qiskit/pyqpanda3)
- **uniqc-noise-simulation** — NoisySimulator with error models (Depolarizing, AmplitudeDamping, etc.)
- **uniqc-qaoa** — QAOA workflows and ansatz construction
- **uniqc-quantum-ml** — PyTorch QML (QNN, QCNN, HybridQCLModel, QuantumLayer)
- **uniqc-algorithm-cases** — Algorithm templates (GHZ, QFT, QPE, Grover, VQE, tomography)
- **uniqc-quantum-volume** — Quantum Volume testing with heavy-output protocol
- **uniqc-classical-shadow** — Shadow tomography for efficient multi-observable estimation
- **uniqc-doctor-config** — Environment diagnostics and config troubleshooting
- **uniqc-platform-verify** — Chip metadata validation against published specs

## Core Patterns

- **AnyQuantumCircuit input**: UnifiedQuantum APIs accept `Circuit` / OriginIR str / QASM2 str / `qiskit.QuantumCircuit` / pyqpanda3 circuit
- **Backend format**: `provider:chip` (e.g., `originq:WK_C180`, `ibm:ibm_fez`, `dummy:local:simulator`)
- **CLI submit**: `uniqc submit ... --backend <provider>:<chip>` (v0.0.13 breaking: `--platform` flag removed)
- **Local simulation**: `Simulator` / `NoisySimulator` from `uniqc.simulator` (replaces deprecated OriginIR_Simulator/QASM_Simulator)
- **Async result API**: `uniqc.get_result()`, `uniqc.poll_result()` (v0.0.13 top-level aliases)
- **OriginIR-ext default emission (v0.0.15)**: `Circuit.originir` returns OriginIR-ext. For OriginQ cloud use `Circuit.to_originir_official()`. Local `Simulator` / `NoisySimulator` accept both natively.
- **Differentiable expectation (v0.0.15)**: `from uniqc import expectation` for backend-agnostic differentiable expectation values across statevector / TorchQuantum simulators.

## Version Tracking

This repository follows UnifiedQuantum releases. Current alignment: **UnifiedQuantum v0.0.17**.

Current v0.0.17 contracts:

- **PyTorch extra**: `pip install "unified-quantum[pytorch]"` installs both
  `torch` and `torchquantum-ng`; Python code still imports `torchquantum`.
- **Custom noisy virtual machines** (v0.0.16): define
  `~/.uniqc/backend/virtual/<name>.yaml`, validate with
  `uniqc backend virtual validate <name>`, then submit with
  `dummy:virtual:<name>`. Backend discovery and chip caches live at
  `~/.uniqc/backend/backends.json` and `~/.uniqc/backend/chips/`.
- **Build/runtime range**: Python is `>=3.10,<3.15`; native builds require
  CMake 3.22 or newer. Real cloud-execution tests are opt-in with
  `--real-cloud-test`; the default suite excludes `cloud`.

Historical v0.0.15 highlights:
- **Native PyTorch parameter integration**: `Circuit.param_map`, `Circuit.param_dict`, `Circuit.has_param`, `Circuit.set_param_last`; tensor params auto-register as `nn.Parameter` in `add_gate`; new top-level `uniqc.expectation()` for backend-agnostic differentiable expectation values.
- **OriginIR-ext superset language**: `Circuit.originir` now emits OriginIR-ext by default (extra gates `ECR`/`ISWAP`/`XX`/`YY`/`ZZ`/`XY`/`PHASE2Q`/`UU15`/`RPhi*`, `QRAM`, `DEF`/`ENDDEF` subroutines, inline `dagger`/`controlled_by(...)`, error channels). For OriginQ cloud submission call `Circuit.to_originir_official()` (or `uniqc.compile.convert_originir_ext_to_originir()` on raw text) first. Inventory: `uniqc.circuit_builder.available_originir_ext_gates`, `EXTENDED_GATES_ONLY`.
- **Behavior change**: `Circuit.has_param` (property) now returns `True` only when ≥1 parameter is a `torch.Tensor` (pure-float params → `False`). The `has_param=` kwarg on `add_gate(...)` is unrelated and unchanged.
- **Python 3.14 support**: cp310–cp314 wheels for core + `[simulation]` / `[visualization]` / `[pytorch]`. `[originq]` extra is gated to `python_version < '3.14'` (pyqpanda3 has no cp314 wheel yet).
- **Packaging**: `[all]` extra **no longer pulls in `[quark]`** (quarkstudio has no cp314/win32 wheels). Install Quark explicitly with `[quark]` on Linux/macOS Python 3.12–3.13.
- **0.1.0 deprecation cliff**: every API currently emitting `DeprecationWarning` will be removed at `0.1.0`. Notable: `uniqc.simulator.get_backend()` → `get_simulator()` / `create_simulator()`; `IBMAdapter` → `QiskitAdapter`; entire `uniqc.backend_adapter.task.adapters.quafu_adapter` module; in-place `*_circuit(circuit, ...)` forms of all algorithm builders (use fragment form + `circuit.add_circuit(fragment)`); `grover_diffusion(..., ancilla=...)` kwarg (unused); task lookup by platform task id (use `uqt_*` id). See `docs/source/7_releases/deprecation_policy.md` in upstream.

Historical v0.0.13 breaking changes:
- `--platform` CLI flag removed (use `--backend <provider>:<chip>`)
- `OriginIR_Simulator`/`QASM_Simulator` → `Simulator`/`NoisySimulator`
- `qiskit` is now a core dependency (no `[qiskit]` extra)
- Quafu archived (`[quafu]` extra removed, use `pip install pyquafu` with `numpy<2`)
- `submit_task` requires full `provider:chip` (bare `"originq"` raises)

## Common Workflows

1. **Install**: `pip install unified-quantum` (qiskit included in core)
2. **Health check**: `uniqc doctor`
3. **Build circuit**: `Circuit().h(0).cnot(0,1).measure(0,1)`
4. **Local simulate**: `Simulator().simulate_shots(circuit, shots=1000)`
5. **Dry run**: `uniqc submit --dry-run --backend dummy`
6. **Real device**: `submit_task(circuit, backend="originq:WK_C180", shots=1000)`
7. **Get result**: `uniqc.get_result(task_id)` or `wait_for_result(task_id)`

## Documentation Files

- `README.md` — Overview and installation instructions
- `CHANGELOG.md` — Version history and breaking changes
- `skill-report.md` — Verification report against uniqc API
- `skill-fix-summary.md` — Applied fixes and verification commands
