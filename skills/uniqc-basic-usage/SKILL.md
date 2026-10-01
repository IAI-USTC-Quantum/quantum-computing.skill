---
name: uniqc-basic-usage
description: "Use when the user asks about UnifiedQuantum or uniqc basic usage: installation, Python imports, Circuit construction (incl. AnyQuantumCircuit input across Circuit / OriginIR / QASM2 / qiskit / pyqpanda3), OriginIR/OpenQASM export, circuit drawing with the 0.1.1 rendering engine (`Circuit.draw(mode)` / `uniqc draw`, modes text/svg/png/mpl/latex/html/interactive), `Circuit.to_matrix()` full-unitary export, local simulation with the unified `Simulator` / `NoisySimulator` (incl. MPS / matrix-product-state / tensor network on linear topology), CLI help, config, `uniqc doctor` diagnostics, dummy backends (`dummy:local:virtual-line-N`, `dummy:local:mps-linear-N`, user YAML `dummy:virtual:<name>`), `uniqc submit --backend <provider>:<chip>` (single-flag CLI, no more `--platform`), dry-run, backend discovery/cache, simple cloud submission, result queries (`get_result` / `poll_result` / `wait_for_result`), calibration, QEM, timeline visualization, and first-pass troubleshooting. Provide practical runnable workflows for UnifiedQuantum v0.1.1."
---

# Uniqc Basic Usage Skill

Use this skill to help agents handle common UnifiedQuantum usage. Prefer direct, runnable workflows over package history. Keep the guidance broad enough for first-pass usage; deep algorithm development, QEM, and real-hardware operations can move into dedicated skills as they are added.

## Core Mental Model

UnifiedQuantum (current **0.1.1 release**) has six common surfaces:

1. **Circuit authoring**: build circuits with top-level `uniqc.Circuit`, then export OriginIR or OpenQASM. Public APIs (compile / simulate / submit) accept the unified `AnyQuantumCircuit` type — `Circuit` / OriginIR `str` / OpenQASM 2.0 `str` / `qiskit.QuantumCircuit` / pyqpanda3 circuit — and normalize internally via `normalize_to_circuit()`.
2. **Local simulation**: validate circuits with `uniqc simulate` or the unified `Simulator` / `NoisySimulator` before spending cloud quota. Format (OriginIR vs QASM 2.0) is auto-detected at runtime.
3. **Algorithm development**: compose ansatz helpers, simulators, analyzers, SciPy/PyTorch, and optimization loops.
4. **Compile and dummy workflows**: use explicit dummy backend ids to check task, topology, and chip-backed noisy paths locally.
5. **Calibration and QEM**: characterize chip errors with XEB (1q / 2q / parallel-CZ) and readout calibration, then mitigate measurement errors with ReadoutEM or M3Mitigator.
6. **Cloud experiments**: discover a backend, dry-run, map/select qubits, submit through CLI/API (OriginQ, Quark, IBM, TianYan, LogicalQubit; Quafu removed in 0.1.0), then query and record results.

For new projects, assume a current UnifiedQuantum release. Do not discuss old release history unless the user is explicitly debugging an old environment.

## First Decision

Choose the path from the user's goal:

- **Ask for current recommended usage or release-check paths**: read [references/best-practices.md](references/best-practices.md) first.
- **Learn or prototype a circuit**: read [references/circuit-building.md](references/circuit-building.md), then use [references/simulators.md](references/simulators.md).
- **Run shell workflows or convert formats**: read [references/cli-guide.md](references/cli-guide.md).
- **Develop VQE/QAOA/UCCSD-style algorithms**: read [references/variational-algorithms.md](references/variational-algorithms.md); use [references/h2-molecular-simulation.md](references/h2-molecular-simulation.md) for H2-style VQE.
- **Use PyTorch or batching helpers**: read [references/pytorch-integration.md](references/pytorch-integration.md).
- **Run dummy, cloud simulator, or real hardware**: read [references/cloud-platforms.md](references/cloud-platforms.md).
- **Calibrate, benchmark, or mitigate readout errors**: read [references/calibration-qem.md](references/calibration-qem.md).
- **Draw or render a circuit** (ASCII / SVG / PNG / LaTeX / HTML / interactive): `circuit.draw(mode, ...)` or the `uniqc draw <file>` CLI (0.1.1 engine); see [references/cli-guide.md](references/cli-guide.md).
- **Visualize circuit timelines or render to HTML**: read [references/timeline-visualization.md](references/timeline-visualization.md).
- **Something fails after following the feature reference**: read [references/troubleshooting.md](references/troubleshooting.md).

## Practical Defaults

Use these defaults unless the user gives a reason not to:

- For CLI-only use, prefer `uv tool install unified-quantum`; for Python API use `uv pip install unified-quantum` inside the user's project environment.
- A plain `pip install unified-quantum` is now enough for **compile / IBM Quantum / chip-backed-dummy compile** paths — `qiskit`, `qiskit-aer`, and `qiskit-ibm-runtime` are **core dependencies** in 0.0.13 (the `[qiskit]` extra has been removed). If `import qiskit` fails after install, the environment is broken — `pip install --upgrade unified-quantum`.
- After install, run `uniqc doctor` first. It checks the Python version, dependency groups (originq / quark / tianyan / logicalqubit / qiskit / simulation / visualization / pytorch), configured platform tokens, cached backends, the local task DB, and known broken-import shims; this is the canonical first-line triage tool (added in 0.0.13). `uniqc config validate` / `uniqc config list` remain the deeper config-only checks.
- Import common objects from `uniqc` directly: `Circuit`, `AnyQuantumCircuit`, `normalize_to_circuit`, `compile`, `submit_task`, `wait_for_result`, `get_result`, `poll_result`, `dry_run_task`, `BackendInfo`, `Platform`, `QubitTopology`, ansatz helpers, and expectation helpers.
- Build circuits in Python with `Circuit` (or any `AnyQuantumCircuit` form), export `originir` / `qasm`, then run CLI or simulator workflows on the normalized file. `Circuit.to_qiskit_circuit()` and `Circuit.to_pyqpanda3_circuit()` are first-class converters when you need the other in-process types.
- Use explicit dummy backend ids:
  - `dummy` (alias for `dummy:local:simulator`): unconstrained, noiseless local virtual machine.
  - `dummy:local:virtual-line-N` / `dummy:local:virtual-grid-RxC`: constrained virtual topology, noiseless.
  - `dummy:virtual:<name>`: a user-defined YAML topology and noise model at `~/.uniqc/backend/virtual/<name>.yaml`; create and validate it with `uniqc backend virtual init|validate <name>` before submitting.
  - `dummy:local:mps-linear-N`: MPS (matrix-product state / tensor network) simulator on a linear-N topology — much better scaling for low-entanglement circuits.
  - `dummy:<platform>:<backend>` (e.g. `dummy:originq:WK_C180`): real backend topology and calibration, compile/transpile, then local noisy execution. As of 0.0.13 this **always** runs the basis-gate compile pass — the previous early-return that silently skipped transpile for in-region active qubits was removed (a Bell circuit no longer crashes with `TopologyError`).
- Run `dry_run_task(...)` or `uniqc submit --dry-run` before real-device submission.
- **`uniqc submit` CLI** (0.0.13 breaking): `--platform` / `-p` is **gone**. Use a single `--backend <provider>:<chip>` flag (e.g. `--backend originq:WK_C180`, `--backend ibm:ibm_fez`, `--backend dummy:local:simulator`, `--backend dummy:originq:WK_C180`, `--backend dummy:local:virtual-line-3`, `--backend dummy:virtual:my-machine`, `--backend dummy:local:mps-linear-12`). Omitting `--backend` defaults to `dummy:local:simulator`. Bare `dummy` is accepted as an alias. Other CLI subcommands (`uniqc backend update --platform`, `uniqc task list --platform`, `uniqc result --platform`) **still accept** `--platform` — they scope cache/storage operations.
- For CLI-heavy AI-agent work, enable progressive hints once with `uniqc config always-ai-hint on`, or pass `--ai-hints` / `--ai-hint` on individual commands.
- Use `uniqc backend update`, `list`, `show`, and `chip-display` before real-device submission. As of 0.0.13, `uniqc backend update --platform ibm|quark` actually refreshes the on-disk chip cache via each adapter's `get_chip_characterization` (previously raised "Cache refresh not implemented for provider …" for IBM and the others); 0.1.0 extends the same to `tianyan` / `logicalqubit` via `chip-display --update`.
- Use `RegionSelector` or backend characterization data when hardware quality and topology matter.
- Use `uniqc calibrate xeb/readout/pattern` CLI commands for chip characterization experiments; results are cached to `~/.uniqc/calibration_cache/`. The XEB family includes `1q`, `2q`, `parallel`, and (new in 0.0.13) `parallel_cz` — the latter targets the parallel-CZ benchmarking module and ships a strict pre-flight policy (it refuses to dispatch experiments whose chip-level prerequisites are not met instead of failing silently downstream).
- Use `ReadoutEM` or `M3Mitigator` from `uniqc.qem` for readout error mitigation on measurement results.
- Quark platform requires `QUARK_API_KEY` in config (not `token`); install with `pip install unified-quantum[quark]` (Python ≥ 3.12).
- Keep shot counts low for initial real-device checks; increase only after the workflow and backend choice are verified.
- **Quafu is deprecated and archived** as of 0.0.13: the `[quafu]` extra is gone, `import` of any Quafu adapter emits `DeprecationWarning`, and the public doc-site hides Quafu (only `originq` / `ibm` / `quark` / `dummy` are recommended). If a user explicitly wants Quafu, install `pyquafu` directly with `pip install pyquafu` and pin `numpy<2`. Future releases do not guarantee correctness or completeness of Quafu code.
- Configure IBM proxy through `uniqc config set ibm.proxy.https <URL>` / `ibm.proxy.http <URL>` when the network path requires it.
- Real `originq` paths (cloud simulator AND hardware AND chip-backed dummy compile) require `pip install unified-quantum[originq]` (pulls `pyqpanda3`); likewise `[quark]` for Quark. IBM/Qiskit/chip-backed dummy backends (`dummy:originq:<chip>` / `dummy:quark:<chip>`) need **no extra** in 0.0.13 — qiskit ships in core.
- `UNIQC_DUMMY` and `UNIQC_SKIP_VALIDATION` env vars have been **removed** (uniqc ≥ 0.0.11.dev10). Activate dummy mode by passing `backend="dummy"` / `backend="dummy:..."` to `submit_task`. Compile/validation behavior is now controlled per-call by `local_compile: int` (0=skip qiskit transpile; 1-3=qiskit `optimization_level`) and `cloud_compile: int` (0=ask cloud to skip optimization; >0=ask cloud to optimize). The legacy `auto_compile=` / `skip_validation=` kwargs are gone (pre-release breaking change).
- **`submit_task` requires `provider:chip` (0.0.13 breaking)**: `submit_task(backend="originq")` or `backend="ibm"` now raises — pass `originq:WK_C180`, `ibm:ibm_fez`, etc. (or a `dummy:...` rule string). `auto_compile` is also fixed to actually run when no `compile_options` are provided.
- **uniqc-managed task IDs (uqt_*)** — uniqc ≥ 0.0.12: `submit_task` and `submit_batch` always return a single opaque uniqc task id of the form `uqt_<32-hex>` (36 chars). It maps internally to one or more platform-issued task ids via the `task_shards` table. `submit_batch` returns one `uqt_*` (not a list), and `wait_for_result(uid)` / `get_result(uid)` returns a single `UnifiedResult` for single-circuit tasks or a `list[UnifiedResult]` for batches. To recover the underlying platform ids, call `uniqc.get_platform_task_ids(uid) -> list[TaskShard]` (also: `uniqc task shards <uid>` CLI / `GET /api/tasks/{uid}/shards` REST). The implicit raw-platform-id → `uqt_*` lookup was **removed in 0.1.0** — always keep the `uqt_*` id. `submit_batch(..., return_platform_ids=True)` returns the platform-id list when explicitly needed. Auto-sharding kicks in when a batch exceeds the adapter's `max_native_batch_size` (OriginQ default 200 via `originq.task_group_size`, IBM 100, others 1) — the user still sees one task id.
- **Async-style result API (0.0.13)** — `uniqc.get_result(task_id, timeout=300, poll_interval=5, raise_on_failure=True)` is a blocking convenience alias for `wait_for_result` ("I want the answer"). `uniqc.poll_result(task_id)` is a non-blocking single-shot status check that returns `TaskInfo` immediately (call it in your own loop). All three are re-exported from `uniqc` directly.
- **Bitstring convention (0.0.13)** — every adapter enforces `c[0] = LSB` end-to-end (matches OriginQ / dummy / simulator). Existing pre-0.0.13 code that hand-reversed bitstrings for IBM should drop the reversal.

## Core Snippets

Circuit:

```python
from uniqc import Circuit

circuit = Circuit()
circuit.h(0)
circuit.cnot(0, 1)
circuit.measure(0, 1)
print(circuit.originir)
```

Drawing and unitary export (uniqc ≥ 0.1.1):

```python
from uniqc.visualization import render

print(circuit)                      # text art (self-developed renderer, no pyqpanda3)
svg = circuit.draw("svg")           # modes: text/svg/png/mpl/latex/html/interactive
render(circuit, mode="html", filename="circuit.html")

bell = Circuit(2); bell.h(0); bell.cnot(0, 1)
u = bell.to_matrix()                # (4, 4) complex unitary; raises NotMatrixableError
                                    # if the circuit has measurements / QRAM calls
```

Local simulation (uniqc ≥ 0.0.13 — unified `Simulator`):

```python
from uniqc.simulator import Simulator, NoisySimulator

sim = Simulator(backend_type="statevector")           # auto-detects OriginIR vs QASM2
probs = sim.simulate_pmeasure(circuit)                 # AnyQuantumCircuit accepted

# Noisy variant (density-matrix backend)
from uniqc.simulator.error_model import Depolarizing, ErrorLoader_GenericError
noisy = NoisySimulator(
    backend_type="density_matrix",
    error_loader=ErrorLoader_GenericError([Depolarizing(0.01)]),
    readout_error={0: [0.01, 0.02], 1: [0.01, 0.02]},
)
probs_noisy = noisy.simulate_pmeasure(circuit)
```

`OriginIR_Simulator` and `QASM_Simulator` were **removed** in 0.0.13. Drop the `program_type=` kwarg.

Dummy/cloud task API:

```python
from uniqc import dry_run_task, submit_task, get_result, poll_result, wait_for_result

dry_run = dry_run_task(circuit, backend="dummy", shots=1000)   # bare 'dummy' == 'dummy:local:simulator'
task_id = submit_task(circuit, backend="dummy", shots=1000)
result = wait_for_result(task_id, timeout=60)                  # blocking
# Equivalents:
# result = get_result(task_id, timeout=60)                     # blocking, "I want the answer" alias
# info   = poll_result(task_id)                                # non-blocking single status check
```

Variational building blocks:

```python
from uniqc import calculate_expectation, hea, qaoa_ansatz, uccsd_ansatz
```

Compile:

```python
from uniqc import compile, find_backend
backend_info = find_backend('originq:WK_C180')
compiled = compile(circuit, backend_info, level=2,
                   basis_gates=['cz', 'sx', 'rz'])  # returns a Circuit
```

`compile()` returns a `Circuit` directly. `TranspilerConfig` still exists for advanced flows but `compile()` does not accept `config=`. `compile()` accepts any `AnyQuantumCircuit` input. The chip-backed compile pass uses qiskit, which is now a **core dependency** (no `[qiskit]` extra needed in 0.0.13).

QEM:

```python
from uniqc import ReadoutEM

em = ReadoutEM(adapter, max_age_hours=24.0, shots=1000)
corrected_counts = em.mitigate_counts(raw_counts, measured_qubits=[0, 1])
```

## Environment Guidance

Do not silently modify a user's Python environment. If setup is needed, first identify whether they are using `venv`, Conda, Pixi, uv, or system Python. For a fresh project, recommend:

```bash
uv venv
source .venv/bin/activate
uv pip install unified-quantum
```

If the user only needs the CLI, use `uv tool install unified-quantum`. If the user is debugging an existing project, inspect the active interpreter, `uniqc` path, package version, and import path before changing dependencies. The package root no longer supports `python -m uniqc`; the module fallback is `python -m uniqc.cli` (still true on the current release).

## Names To Remember

- PyPI package: `unified-quantum`
- Python import package: `uniqc`
- CLI command: `uniqc`
- CLI module fallback: `python -m uniqc.cli`
- Config file: `~/.uniqc/config.yaml`
- Python config module: `uniqc.config` (canonical; `uniqc.backend_adapter.config` is a pure re-export shim)
- Compile entry point: `uniqc.compile` (`compile()`, `TranspilerConfig`, `CompilationResult`)
- Calibration module: `uniqc.calibration` (XEB, readout calibration, `XEBResult`, `ReadoutCalibrationResult`)
- QEM module: `uniqc.qem` (`M3Mitigator`, `ReadoutEM`, `StaleCalibrationError`, `ZNE`). All mitigators expose a `.apply(unified_result)` pipeline-style API that returns a new `UnifiedResult` with mitigated counts/probabilities — feed it directly into the rest of the workflow. Legacy `mitigate_counts` / `mitigate_probabilities` still exist for raw-dict input. **`ZNE` is a placeholder** that raises `NotImplementedError`; only readout mitigation is currently implemented.
- Visualization module: `uniqc.visualization` — circuit rendering (0.1.1 engine): `render(circuit, mode=...)` / `Circuit.draw(...)` with modes `text/svg/png/mpl/latex/html/interactive` (+ CLI `uniqc draw <file>`; legacy `draw` / `draw_html` deprecated, removed in 0.2.0). Timelines / report pages: `circuit_to_html`, `plot_time_line_html`, `schedule_circuit`.
- Full-unitary export (≥ 0.1.1): `Circuit.to_matrix()` — `(2**n, 2**n)` complex ndarray, convention `state_out = U @ state_in` with qubit 0 as the LSB; raises `NotMatrixableError` for measurements or non-unitary opcodes (e.g. QRAM).
- Algorithms workflows: `uniqc.algorithms.workflows` (`xeb_workflow`, `readout_em_workflow`). Note: VQE/QAOA/QNN training loops live in `uniqc.algorithms.core.training` (needs `[pytorch]`, which installs `torch` + `torchquantum-ng`).
- Algorithm fragments (return new `Circuit`): `hea`, `qaoa_ansatz`, `uccsd_ansatz`, `qft_circuit`, `qpe_circuit`, `ghz_state`, `w_state`, `dicke_state_circuit`, `cluster_state`, `grover_oracle`, `grover_diffusion`, `amplitude_estimation_circuit`, `vqd_ansatz`, `thermal_state_circuit`, `deutsch_jozsa_circuit`. Fragment-only since 0.1.0 (the legacy `fn(circuit, ...)` in-place form is removed — compose with `circuit.add_circuit(fragment)`). `qpe_circuit(n_precision, unitary_circuit, *, state_prep=None, controlled_power=None, measure=True)` returns a fresh `Circuit` with `n_system + n_precision` qubits and (by default) measurements on the precision register; the integer ``m`` decoded from the measured cbits gives ``φ ≈ m / 2**n_precision``. (uniqc ≥ 0.0.11.dev30, C-U9.)
- Measurement helpers: `uniqc.algorithms.core.measurement` — functions (`pauli_expectation`, `basis_rotation_measurement`, `classical_shadow`, `shadow_expectation`, `state_tomography`, `tomography_summary`) **and** classes (`PauliExpectation`, `StateTomography`, `ClassicalShadow`, `BasisRotationMeasurement`) with `.get_readout_circuits()` + `.execute(backend)` API. `pauli_expectation` / `PauliExpectation` accept three Pauli-string forms (C-U2, uniqc ≥ 0.0.11.dev30): compact `"ZIZ"` (length = n_qubit), indexed `"Z0Z1"`, and tuple-list `[("Z", 0), ("Z", 1)]`. `basis_rotation_measurement` now raises `ValueError` if the input circuit has no `MEASURE` instructions (C-U5, was previously a silent no-op for X/Y bases). `tomography_summary` is pure NumPy/SciPy (no qutip) and returns a dict with `eigenvalues / purity / trace / is_pure / fidelity`; pass `print_summary=False` to suppress the formatted stdout output.
- BackendOptions hierarchy: `BackendOptions`, `OriginQOptions`, `QuarkOptions`, `IBMOptions`, `DummyOptions` (`QuafuOptions` left this list when the platform was removed in 0.1.0). Use `BackendOptionsFactory().create_default('originq')` for a sane default; `BackendOptionsFactory().from_kwargs(platform, **kwargs)` builds from explicit kwargs.
- Gateway / web UI: `uniqc gateway start [--port N --host HOST]` starts the local task dashboard; manage it with `uniqc gateway status / stop / restart`.
- AI CLI hints: `--ai-hints` / `--ai-hint`, `UNIQC_AI_HINTS=1`, or `uniqc config always-ai-hint on`
- Local task cache: `~/.uniqc/cache/tasks.sqlite`
- Backend cache: `~/.uniqc/backend/backends.json`
- Chip characterization cache: `~/.uniqc/backend/chips/`
- Calibration cache: `~/.uniqc/calibration_cache/`

## Response Style

- Give the user a runnable path first, then mention optional refinements.
- Prefer small complete examples over long API inventories.
- For hardware work, include backend selection, shots, wait/query flow, and where results are cached.
- For algorithm work, include the objective function shape, simulator/analyzer choice, and optimizer loop.
- For suspected library bugs, reduce to a minimal reproducer, check current docs/issues, and only then suggest filing an upstream issue.
