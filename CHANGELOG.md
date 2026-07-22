# Changelog

All notable changes to the `quantum-computing.skill` package are documented here.

## [0.0.17] - 2026-07-22 — UnifiedQuantum 0.0.17 alignment

### Changed

- **TorchQuantum install → `torchquantum-ng`** — all skill docs/examples that
  referenced the old git fork
  (`torchquantum @ git+…/torchquantum.git@fix/optional-qiskit-deps`) now use
  the community fork [`torchquantum-ng`](https://pypi.org/project/torchquantum-ng/),
  which is pulled in by the `[pytorch]` extra. The import name is unchanged
  (`import torchquantum`), so `pip install unified-quantum[pytorch]` installs
  both `torch` and the TorchQuantum backend — the separate manual install step
  is removed from `uniqc-quantum-ml` (SKILL.md, `qnn_moons.py`,
  `qnn-classifier.md`), `uniqc-basic-usage` (`pytorch-integration.md`, SKILL.md).
- **v0.0.16–v0.0.17 backend lifecycle** — documented
  `dummy:virtual:<name>`, `uniqc backend virtual init/list/show/validate`,
  YAML thermal relaxation, and the unified backend cache root
  (`~/.uniqc/backend/backends.json`, `~/.uniqc/backend/chips/`).
- **Release gates** — added offline local-link/front-matter/reference checks,
  upstream contract parity checks, and fail-closed smoke aggregation with a
  machine-readable JSON summary.

## [0.0.15] - 2026-06-04 — UnifiedQuantum 0.0.15 alignment

UnifiedQuantum 0.0.15 introduced **no new breaking changes** on top of
0.0.14, but added two large feature surfaces (native PyTorch parameter
integration + OriginIR-ext as the default emitted dialect), tweaked one
silent behaviour (`Circuit.has_param` property), widened Python support
to 3.14, and formalised the 0.1.0 deprecation cliff. This release brings
the skill collection in lockstep with those additions.

### Aligned with UnifiedQuantum 0.0.15 changes (existing skills)

- **`uniqc-quantum-ml`** — added a Layer 0 row to the layer-selection
  table covering the new **native PyTorch params** workflow
  (`Circuit.param_map` / `Circuit.param_dict` / `Circuit.has_param`
  property / `Circuit.set_param_last`, auto-`nn.Parameter` registration
  in `add_gate`, top-level `uniqc.expectation()` for backend-agnostic
  differentiable expectation values). Added a complete cheat-sheet
  section and a new reference page `references/native-torch-params.md`
  with mental model, end-to-end training loop, state_dict round-trip,
  and an explicit gotcha box separating the `has_param` property from
  the `add_gate(..., has_param=True)` kwarg.
- **`uniqc-circuit-interop`** — `Circuit.originir` now emits
  **OriginIR-ext** (strict superset). Added a full "OriginIR-ext vs
  official OriginIR" section, the 12-gate `EXTENDED_GATES_ONLY`
  inventory, `Circuit.to_originir_official()` and
  `uniqc.compile.convert_originir_ext_to_originir(text)` converters,
  two new round-trip pitfall rows, and expanded "Names to remember".
- **`uniqc-cloud-submit`** — flagged that the existing pattern of
  writing `circuit.originir` to a `.originir` file before submitting to
  `originq:WK_C180` now serialises **OriginIR-ext**, which OriginQ
  cloud does not accept. Added Practical-defaults bullets covering
  `to_originir_official()`, the `convert_originir_ext_to_originir()`
  converter, the safer `submit_task(circuit_object, ...)` form (uniqc
  handles conversion), the `[all]` / `[quark]` / `[originq]` packaging
  changes, and the 0.1.0 deprecation cliff. Added an "OriginIR vs
  OriginIR-ext (uniqc ≥ 0.0.15)" subsection in
  `references/authoring-program-files.md`.
- **`uniqc-basic-usage`** — annotated the `originir` row in 常用属性
  to call out OriginIR-ext default emission and added an 输出建议
  reminder block (use `to_originir_official()` before posting to
  OriginQ cloud / sharing with non-uniqc tools).
- **`uniqc-doctor-config`** — added a "0.1.0 deprecation cliff"
  section listing every API that emits a `DeprecationWarning`
  containing the literal `"uniqc 0.1.0"` substring
  (`uniqc.simulator.get_backend()`, `IBMAdapter`, `quafu_adapter`
  module, in-place `*_circuit(circuit, ...)` algorithm builders,
  `grover_diffusion(..., ancilla=...)` kwarg, task lookup by platform
  task id). Updated the optional-dep group table (`[originq]` gated to
  Py < 3.14; `[quark]` no longer pulled by `[all]`) and added a
  matching row to the error → action table.

### `CLAUDE.md`

- Bumped baseline to **UnifiedQuantum v0.0.15** (2026-06-04).
- Added a "Key changes in v0.0.15" block covering native PyTorch
  params, OriginIR-ext default emission, the `has_param` semantic
  flip, Python 3.14, the `[all]` / `[quark]` / `[originq]` packaging
  changes, and the 0.1.0 deprecation cliff.
- Appended two Core Patterns bullets: OriginIR-ext default-emission
  and the new top-level `uniqc.expectation(circuit, observable,
  backend=...)`.

### `README.md`

- Bumped follow-up banner to UnifiedQuantum v0.0.15; layered the
  v0.0.15 additions on top of the existing v0.0.13 breaking-change
  list (which remains the authoritative breakage reference).

### Smoke harness (`uniqc-version-tracker`)

- `smoke_quantum_volume.py` — wrapped the qiskit import in
  `try/except` so a missing qiskit prints `SKIP: qiskit not installed`
  and exits 0, matching the `smoke_quantum_ml.py` (torch) pattern.
- `smoke_quantum_ml.py` — added v0.0.15 assertions:
  `hasattr(uniqc, "expectation")`, builds a 1-qubit `Circuit` with a
  `torch.Tensor` param, asserts the `has_param` property,
  `len(param_dict) >= 1`, `len(param_map) >= 1`.

### Verified

- Re-ran the full smoke aggregator against installed uniqc **0.0.15**:
  **12/13 PASS, 1 SKIP** (`smoke_quantum_ml.py` SKIP because torch is
  not installed in this env). Zero regressions vs the 0.0.14 baseline.

## [0.0.14] - 2026-05-18 — uniqc-version-tracker skill

### New skill (`skills/`)

- **`uniqc-version-tracker`** — automated UnifiedQuantum version tracking
  with a 5-phase workflow: DETECT version gap (installed uniqc vs CLAUDE.md
  baseline + git tags + PyPI), DIFF changelog/commits between releases,
  SMOKE-TEST all 13 skills in parallel via Claude Code sub-agents, AGGREGATE
  results cross-referenced with breaking changes, and REPORT with a markdown
  table + prioritized recommendations. Ships 13 minimal smoke-test scripts
  (~10-30 lines each) that exercise each skill's core API with dummy backends,
  plus helper scripts for version detection, changelog parsing, and result
  aggregation. Report-only by default — never auto-edits skill files without
  user approval.

### `CLAUDE.md`

- Key Skills list updated to include `uniqc-version-tracker`.

## [0.0.13] - 2026-05-14 — UnifiedQuantum 0.0.13 alignment + 5 new skills

This release aligns the entire skill collection with **UnifiedQuantum
0.0.13** and ships **5 new skills** focused on quantum-computing
applications, research, and platform-information validation.

### Aligned with UnifiedQuantum 0.0.13 changes (existing skills)

- **CLI** — every reference / example / script switched from
  `uniqc submit ... --platform <p> [--backend <b>]` to the single
  `uniqc submit ... --backend <provider>:<chip>` syntax (defaults to
  `dummy:local:simulator`; bare `dummy` accepted as an alias).
  `uniqc backend update --platform`, `uniqc task list --platform`,
  `uniqc result --platform` are unchanged.
- **Simulator** — replaced every `OriginIR_Simulator` /
  `QASM_Simulator` reference with `Simulator` / `NoisySimulator`
  (both from `uniqc.simulator`); dropped `program_type=`. Added the
  unified `AnyQuantumCircuit` input story (Circuit / OriginIR str /
  QASM2 str / `qiskit.QuantumCircuit` / pyqpanda3 circuit) plus
  `normalize_to_circuit()` / `NormalizedCircuit` (with the
  `original_format → type` rename).
- **`uniqc doctor`** — every "doctor doesn't exist, use `config
  validate`" stale guidance is **gone**. Doctor exists in 0.0.13 and
  is now the recommended first-line health check across
  `uniqc-basic-usage`, `uniqc-cloud-submit`, `uniqc-doctor-config`,
  and `uniqc-platform-verify`.
- **`submit_task` strict `provider:chip`** — examples updated
  (`backend="originq"` and `backend="ibm"` raise; use
  `originq:WK_C180`, `ibm:ibm_fez`, etc.).
- **qiskit core** — references to `pip install
  unified-quantum[qiskit]` removed everywhere; qiskit ships as a
  core dependency in 0.0.13.
- **Quafu archived** — references to `pip install
  unified-quantum[quafu]` updated to `pip install pyquafu` (with
  `numpy<2`); deprecation warning called out.
- **Async-style result API** — `uniqc.get_result` / `uniqc.poll_result`
  documented as top-level alternatives to `wait_for_result` /
  `query_task`.
- **Parallel-CZ XEB** — `uniqc.calibration.xeb.parallel_cz` and the
  strict pre-flight policy documented in `uniqc-xeb-qem`,
  `uniqc-platform-verify`, and `uniqc-noise-simulation`.
- **Bitstring `c[0]=LSB`** — Quafu / IBM endianness fix surfaced
  (drop hand-reversal in old code).
- **Other fixes** — `NoisySimulator` MRO, IBM backend cache refresh,
  Qiskit `query_batch` flatten, `dummy:originq:<chip>` compile
  always-runs, `UnifiedResult` JSON serialisation — each surfaced in
  the relevant skill.

### New skills (`skills/`)

- **`uniqc-doctor-config`** — environment / config diagnostics.
  Wraps `uniqc doctor`, walks the 6-section report (env / core deps /
  optional groups / config tokens / task DB / backend cache /
  connectivity), maps every uniqc public-error class to a one-line
  fix, and covers proxy / firewall / install-extras triage. Includes
  `examples/run_full_diagnostics.sh`.
- **`uniqc-platform-verify`** — verify that a platform's published /
  cached chip metadata is actually accurate today. Refresh the local
  backend cache, audit topology / available qubits / basis gates,
  measure 1q-2q-readout-parallel-CZ fidelities via XEB + readout
  calibration, compare to vendor-published numbers (Δ with sign),
  detect drift between snapshots. Includes `examples/audit_chip.py`.
- **`uniqc-noise-simulation`** — model and simulate quantum noise
  with `NoisySimulator` + `error_model` + `ErrorLoader_*`. Covers
  `Depolarizing` / `TwoQubitDepolarizing` / `BitFlip` / `PhaseFlip`
  / `AmplitudeDamping` / `PauliError1Q/2Q` / `Kraus1Q`,
  `ErrorLoader_GenericError|GateTypeError|GateSpecificError`,
  readout error, chip-backed dummy paths, and validation against a
  measured calibration. Includes `examples/noisy_bell.py`.
- **`uniqc-circuit-interop`** — convert across Circuit / OriginIR /
  QASM2 / `qiskit.QuantumCircuit` / pyqpanda3 via
  `AnyQuantumCircuit`, `normalize_to_circuit`,
  `Circuit.to_qiskit_circuit`, `Circuit.to_pyqpanda3_circuit`,
  `Circuit.from_qasm` / `OriginIR_BaseParser` /
  `OpenQASM2_BaseParser`. Covers per-platform IR expectations and
  round-trip pitfalls (UnitaryGate decomposition, empty creg, SX
  rewrite). Includes `examples/round_trip.py`.
- **`uniqc-classical-shadow`** — sample-efficient many-observable
  estimation via classical-shadow tomography. Covers
  `classical_shadow`, `shadow_expectation`, `ClassicalShadow` class,
  `run_classical_shadow_workflow(circuit, pauli_observables, ...)`
  → `ShadowWorkflowResult`, Hamiltonian-VQE integration, and
  shadow-vs-state-tomography selection. Includes
  `examples/bell_shadow.py`.

### `README.md`

- Bumped version banner to UnifiedQuantum 0.0.13 and listed every
  v0.0.13 alignment in the lede.
- "Current Skills" reorganised into 5 groups: 通用 / 环境与平台诊断 /
  流程类 / 线路 & 模拟 / 算法类 — with the 5 new skills placed in
  their respective groups.
- "仓库内容" updated with the 5 new skill directories.

## [Unreleased] — narrower skill batch (UnifiedQuantum 0.0.13.dev0)

This release adds the **first batch of narrower, scenario-focused skills**
alongside the existing `uniqc-basic-usage`. Each new skill follows the same
shape (`SKILL.md` + `references/` + `examples/` + `agents/openai.yaml`) and
is independently installable via `npx skills add ... --skill <name>`.

### New skills (`skills/`)

- **`uniqc-cloud-submit`** — end-to-end real-hardware / cloud submission
  workflow: API-key health check via `uniqc config validate` (the
  user-mentioned `uniqc doctor` does **not** exist), authoring `.originir`
  / `.qasm` from a Python `Circuit`, `dry_run_task` → `submit_task` →
  `query_task` → `wait_for_result`, plus the `uqt_*` task-id / `task_shards`
  story (uniqc ≥ 0.0.12).
- **`uniqc-result-analysis`** — parse `UnifiedResult`, build counts /
  probability tables, plot histograms with `uniqc.visualization.plot_histogram`
  and `plot_distribution`, compute Pauli expectations, render circuits +
  timelines via `circuit_to_html` / `plot_time_line_html`, compare two runs
  with TV / Hellinger.
- **`uniqc-xeb-qem`** — XEB benchmarking (`xeb_workflow.run_1q/2q/parallel/parallel_cz`)
  and QEM via `ReadoutEM.apply` / `M3Mitigator.apply`. Documents
  `find_cached_results(..., result_type=...)`, `StaleCalibrationError`
  inheriting directly from `Exception`, the `dummy:originq:<chip>` /
  `[qiskit]` extras requirement, the `~/.uniqc/calibration_cache/` layout,
  and that `run_readout_em_workflow` returns a `ReadoutEM` (not a
  `ReadoutCalibrationResult`).
- **`uniqc-qaoa`** — QAOA in three flavours: high-level
  `qaoa_workflow.run_qaoa_workflow`, hand-rolled
  `qaoa_ansatz` + `pauli_expectation` + SciPy, and a real-hardware
  compile / batch / decode flow. Documents the compact-vs-indexed Pauli
  form gotcha (`run_qaoa_workflow` requires compact, `qaoa_ansatz` requires
  indexed; they are not interchangeable).
- **`uniqc-quantum-ml`** — PyTorch QML: `QNNClassifier` / `QCNNClassifier` /
  `HybridQCLModel` (need torchquantum) and the lower-level
  `QuantumLayer(circuit, expectation_fn, n_outputs, init_params, shift=π/2)`
  with parameter-shift gradients. Documents the manual `torchquantum`
  install line, the `QuantumLayer`-needs-`circuit_def` brittleness on
  0.0.13.dev0, and a manual parameter-shift fallback.
- **`uniqc-algorithm-cases`** — catalog + runnable templates for canonical
  algorithms: GHZ / W / Dicke / cluster / thermal state, QFT, QPE
  (`uniqc.algorithms.core.circuits.qpe_circuit`, **not** at top-level),
  Grover, amplitude estimation, Deutsch-Jozsa, VQE / VQD, state tomography,
  classical shadow.
- **`uniqc-quantum-volume`** — Quantum Volume (QV) test using the standard
  Cross-2019 protocol. uniqc itself ships no QV implementation, so the
  skill builds the square QV circuits via `qiskit.circuit.library.quantum_volume`,
  loads them through `Circuit.from_qasm`, runs ideal statevector + hardware
  sampling, scores the heavy-output probability with the conventional 2/3
  + 2σ pass/fail rule, and reports `QV = 2^n_max`. Includes
  `protocol.md` (definition + decision rule), `circuit-construction.md`
  (qiskit interop pitfalls), `analysis.md` (scoring, bootstrap CI,
  plotting, troubleshooting), and a runnable `qv_demo.py`.

### `README.md`

- Lists the new skills under "Current Skills" with short descriptions.

## [0.0.13] - 2026-05-16 — UnifiedQuantum 0.0.13 + post-0.0.13 alignment

UnifiedQuantum 0.0.13 统一了模拟器 API（`Simulator` / `NoisySimulator` 替代 `OriginIR_Simulator` / `QASM_Simulator`）、将 Qiskit 提升为核心依赖、引入 `UnifiedOptions` 跨平台提交选项，并大幅扩展了 ansatz 模块（HVA、ADAPT-VQE、QAOA 变体、硬件感知配置）。Skill 已对齐：

### `SKILL.md`

- 版本字符串更新为 0.0.13。
- 模拟器片段改用 `Simulator` 替代 `OriginIR_Simulator`。
- `BackendOptions` 条目新增 `UnifiedOptions` 说明。
- Algorithm fragments 列表新增 `hea_param_count`、`hva`、`EntanglingGate`、`EntanglementTopology`、`RotationGate`。
- Simulation 模块说明更新为 `Simulator` / `NoisySimulator`。
- `decompose_for_qasm2()` 跨平台 IR 分解已记录。
- `[qiskit]` extra 标记为核心依赖，不再需要单独安装。
- Quafu 标记为已废弃（`[quafu]` extra 移除）。
- CLI `--platform` 更新为 `--backend` 语法。

### `references/variational-algorithms.md`

- 新增 "Ansatz 类型系统" 章节：`EntanglingGate`、`EntanglementTopology`、`RotationGate` 枚举。
- HEA 章节扩展：`hea_param_count`、自定义旋转门/纠缠门/拓扑、`backend_info` 硬件感知配置。
- 新增 HVA（Hamiltonian Variational Ansatz）章节。
- QAOA 章节更新支持 mixer Hamiltonian 和多轮 schedule。
- 新增 ADAPT-VQE 章节（算符池和 Pauli 单元构造）。
- 新增 `Parameter` / `Parameters` 符号参数章节。
- VQE 示例改用 `Simulator`。

### `references/simulators.md`

- 本地模拟器改用 `Simulator` 替代 `OriginIR_Simulator`。
- 含噪声模拟改用 `NoisySimulator` 替代 `OriginIR_NoisySimulator`。
- 新增 API 迁移说明（`OriginIR_Simulator` / `QASM_Simulator` 已删除）。
- 工厂入口更新推荐 `Simulator()` 直接构造。
- MPS 适用性表格更新。
- dummy CLI 示例改用 `--backend` 语法。

### `references/cloud-platforms.md`

- 平台 extras 速查更新：Qiskit 为核心依赖，`[qiskit]` 已移除；Quafu 已废弃。
- 新增 "UnifiedOptions 跨平台提交" 章节，含翻译表和用法示例。

### `references/cli-guide.md`

- 所有 `uniqc submit` CLI 示例改用 `--backend <provider>:<chip>` 语法。
- 新增 CLI 变更说明（`--platform` / `-p` 已从 `submit` 移除）。

### `references/best-practices.md`

- 最稳用户路径更新为 `Simulator()` 和 `--backend` 语法。

### `references/troubleshooting.md`

- MPS 错误表更新为 `Simulator`。

### `references/pytorch-integration.md`

- 期望值示例改用 `Simulator`。

### Examples & Scripts

- `basic_circuit.py`、`qaoa_maxcut.py`、`h2_hea_vqe.py`、`mnist_classifier.py` 改用 `Simulator`。
- `setup_uniqc.sh` 改用 `Simulator`。
- `cli_demo.sh` 改用 `--backend` 语法。

## [0.0.12] - 2026-05-07 — UnifiedQuantum 0.0.12 alignment

UnifiedQuantum 0.0.12 引入了**uniqc 自管理的任务 ID 间接层**（breaking）以及**原生批量提交**。Skill 已对齐：

### `SKILL.md`

- 顶部版本字符串改为 0.0.12。
- 新增 cloud-task 顶层注意事项条目，说明 `submit_task` / `submit_batch` 现在统一返回 `uqt_<32-hex>` 的 uniqc 任务 ID，以及 `get_platform_task_ids` / `uniqc task shards` / `GET /api/tasks/{uid}/shards` 三种查 shard 路径，以及 `submit_batch(..., return_platform_ids=True)` 兜底。

### `references/cloud-platforms.md`

- 新增 “uniqc 任务 ID（`uqt_*`）⚠ 0.0.12 起的改动” 章节，覆盖：
  - 为什么这么改（统一平台 ID 格式 + auto-sharding）
  - `get_platform_task_ids` Python API、`uniqc task shards` CLI、`GET /api/tasks/{uid}/shards` REST
  - 兼容性 / 迁移（旧本地缓存自动迁移、`query_task(<平台 ID>)` 仍可用但 `DeprecationWarning`、`return_platform_ids=True` 兜底）
- 批量任务示例改为 `uid = submit_batch(...)` + `wait_for_result(uid)` → `list[UnifiedResult]` 模式。

### `README.md`

- follow-up 版本说明从 0.0.11 升级到 0.0.12，并列出新引入的 IDL / 原生 batch 特性。

## [0.0.11] - 2026-05-07 — UnifiedQuantum 0.0.11 alignment

This release aligns the skill with the four-round audit fixes that landed in
UnifiedQuantum 0.0.11. Every reference page was reviewed against the live API.

### `SKILL.md`

- Added `qpe_circuit` to the algorithm fragments list.
- Documented `pauli_expectation` accepting three input forms (compact `'ZIZ'`,
  indexed `'Z0Z1'`, tuple list `[('Z',0),('Z',1)]`).
- Noted that `basis_rotation_measurement` raises `ValueError` when the input
  circuit is missing `MEASURE`.

### `references/circuit-building.md`

- Removed the stale `iswap` / `rphi` / `phase2q` / `xy` / `uu15`
  `NotImplementedError` warning — these gates now round-trip through QASM2
  via auto-generated `gate def` blocks.

### `references/simulators.md`

- Corrected `get_simulator` signature to `(backend_type, program_type)` to
  match `create_simulator`.
- Documented `dummy:mps:linear-N` MPS dummy backend.

### `references/cloud-platforms.md`

- `dry_run_task` example now uses single-string form `"originq:WK_C180"` and
  notes that the two-arg `(platform, backend)` form still works.
- Removed the deprecated `backend=` kwarg from `wait_for_result` examples.
- Added a note that `OriginQAdapter.translate_circuit` transparently rewrites
  `SX` / `SX.dagger` to `RX(±π/2)` so circuits in the SX basis are accepted
  by the OriginQ remote parser.
- Updated the OriginQ default backend everywhere from `origin:wuyuan:d5` to
  `originq:WK_C180`.
- Replaced `auto_compile` references with the `local_compile` /
  `cloud_compile` integer model and linked to `docs/guide/compile_levels.md`.

### `references/variational-algorithms.md`

- Added `qpe_circuit` to the fragment list.
- Documented `pauli_expectation` 3 input forms.
- Updated `vqd_circuit` references to `vqd_ansatz` (legacy alias still works).
- Added `vqe`, `qaoa`, and `classical_shadow` workflow drivers.

### `references/calibration-qem.md`

- `ReadoutCalibrator` example shows new `timeout=900.0` and
  `poll_interval=10.0` kwargs.
- Documented that `calibrate_1q` / `calibrate_2q` return
  `ReadoutCalibrationResult` dataclasses (with backward-compat dict access).
- Replaced `mitigate_counts` / `mitigate_probabilities` with the new
  `M3Mitigator.apply(UnifiedResult)` / `ReadoutEM.apply(UnifiedResult)`
  pipeline API.
- Noted that ZNE currently raises `NotImplementedError` (placeholder).

### `references/troubleshooting.md`

- Updated dummy / skip-validation guidance: env vars `UNIQC_DUMMY` and
  `UNIQC_SKIP_VALIDATION` are gone — use the `dummy:` backend prefix and the
  `skip_validation=True` kwarg.
- Updated exception names: `CompilationFailedException` →
  `CompilationFailedError`, `IRConversionFailedException` →
  `CircuitTranslationError`.

### Mirror

- `.agents/skills/uniqc-basic-usage/` mirror is kept in sync via rsync.

## [legacy 1.2.009] — UnifiedQuantum 0.0.9
- Initial coverage for `Circuit.get_matrix()`, calibration module, MPS
  simulator preview.

## [legacy 1.2.0] — UnifiedQuantum 0.0.8
- Refocus skill on UnifiedQuantum workflows.
