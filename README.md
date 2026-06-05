# quantum-computing.skill

[![Quantum Computing | AI](https://img.shields.io/badge/Quantum_Computing-AI-58a6ff?style=flat-square)](https://github.com/IAI-USTC-Quantum)
[![ClawHub](https://img.shields.io/badge/ClawHub-published-9b59b6?style=flat-square)](https://clawhub.ai/agony5757/quantum-computing)
[![SkillHub](https://img.shields.io/badge/SkillHub-published-58a6ff?style=flat-square)](https://www.skillhub.cn/skills/quantum-computing)

面向 [UnifiedQuantum](https://github.com/IAI-USTC-Quantum/UnifiedQuantum) 的 Agent Skills 集合仓库。

当前版本已 follow-up **UnifiedQuantum v0.0.15**（2026-06-04 release），v0.0.14 → v0.0.15 没有新的破坏性变更，重点同步：

- **原生 PyTorch 参数集成**：`Circuit.param_map` / `Circuit.param_dict` / `Circuit.has_param` / `Circuit.set_param_last`，把 `torch.Tensor` 传入 `add_gate` 会自动注册为 `nn.Parameter`；顶层新增 `uniqc.expectation()` 提供跨后端可微期望值。
- **OriginIR-ext 超集语言**：`Circuit.originir` 默认输出 **OriginIR-ext**（严格超集，新增 `ECR` / `ISWAP` / `XX` / `YY` / `ZZ` / `XY` / `PHASE2Q` / `UU15` / `RPhi*`、`QRAM`、`DEF`/`ENDDEF` 子程序、内联 `dagger` / `controlled_by(...)`、错误信道）。本地 `Simulator` / `dummy:*` 后端原生兼容；提交到 **OriginQ 真实硬件**请先调用 `Circuit.to_originir_official()` 或 `uniqc.compile.convert_originir_ext_to_originir()`。
- **行为变更**：`Circuit.has_param`（property）现仅当 ≥1 个参数为 `torch.Tensor` 时返回 `True`；纯 float 参数返回 `False`。`add_gate(..., has_param=True)` kwarg 不受影响。
- **Python 3.14 支持**：core / `[simulation]` / `[visualization]` / `[pytorch]` 提供 cp310–cp314 wheel。`[originq]` extra 锁定 `python_version < '3.14'`（pyqpanda3 尚无 cp314 wheel）。
- **打包变更**：`[all]` extra **不再拉取 `[quark]`**（quarkstudio 没有 cp314 / win32 wheel）。需要 Quark 请显式 `pip install unified-quantum[quark]`（Linux/macOS, Py 3.12–3.13）。
- **0.1.0 deprecation cliff**：所有当前发 `DeprecationWarning` 的 API 会在 uniqc 0.1.0 移除（每条提示都包含 `"uniqc 0.1.0"` 字串）。重点：`uniqc.simulator.get_backend()`、`IBMAdapter`、`quafu_adapter` 模块、各算法 builder 的 in-place `*_circuit(circuit, ...)` 形式、`grover_diffusion(..., ancilla=...)` kwarg、按 platform task id 查询任务。

上一轮 follow-up（v0.0.13）的关键 breaking change（仍是当前的权威列表）：

- **CLI 改动**（breaking）：`uniqc submit` 移除 `--platform`，统一为单一 `--backend <provider>:<chip>`（裸 `dummy` / 不带 `--backend` 等价于 `dummy:local:simulator`）。
- **统一模拟器**（breaking）：`OriginIR_Simulator` / `QASM_Simulator` 移除，由 `Simulator` / `NoisySimulator` 统一接管，自动判别 OriginIR vs QASM 2.0。
- **`AnyQuantumCircuit` 输入类型**：所有 compile / simulate / submit 接口统一接受 `Circuit` / OriginIR str / QASM2 str / `qiskit.QuantumCircuit` / pyqpanda3 circuit。
- **qiskit 入核心依赖**：`[qiskit]` extra 移除。
- **Quafu archived**：`[quafu]` extra 移除，导入会发 `DeprecationWarning`。
- **`uniqc doctor`**：环境诊断 CLI（环境 / 依赖 / 配置 / 任务 DB / 后端缓存 / 平台连通性 一站式体检）。
- **`uniqc submit` 强制 `provider:chip`**：`backend="originq"` / `"ibm"` 不带 chip 直接报错。
- **Parallel-CZ XEB**：`uniqc.calibration.xeb.parallel_cz` 新模块，配合严格 pre-flight 策略。
- **`Circuit.to_qiskit_circuit()` / `to_pyqpanda3_circuit()`**：first-class circuit 互转。
- **顶层 `uniqc.get_result` / `uniqc.poll_result`**：异步风格 Result API 别名。
- **多个 fix**：`NoisySimulator` MRO、IBM backend cache 刷新、Qiskit `query_batch` 扁平化、`dummy:originq:<chip>` compile 强制走 transpile、`UnifiedResult` JSON 序列化、Quafu/IBM `c[0]=LSB` bitstring 约定。

本批同时新增 5 个面向应用 / 研究 / 平台校验的 skill：`uniqc-doctor-config`、`uniqc-platform-verify`、`uniqc-noise-simulation`、`uniqc-circuit-interop`、`uniqc-classical-shadow`。

通用入口仍是 `uniqc-basic-usage`，覆盖 UnifiedQuantum/uniqc 的基础使用路径，例如安装、`uniqc doctor`、线路构建、OriginIR / QASM 转换、本地模拟、CLI、config、dummy backend、dry-run、backend cache、简单提交、标定/QEM、timeline 可视化和通用排障。

## 当前 Skills

通用入口：

- `uniqc-basic-usage`: 通用、跨 Agent 的 UnifiedQuantum 基础使用 skill。

环境与平台诊断：

- `uniqc-doctor-config`: `uniqc doctor` 一站式诊断 + 配置 / 依赖 / 缓存 / proxy / token 问题排查。
- `uniqc-platform-verify`: 校验芯片元数据准确性 —— 拓扑 / 可用 qubit / 标定时效 / 1q-2q-parallel-CZ 测得 vs 厂商 published 比较 / 漂移检测。

流程类（按场景细分）：

- `uniqc-cloud-submit`: 真机 / 云端端到端提交 —— `uniqc doctor` 健康检查、把 Python `Circuit` 持久化为 `.originir` / `.qasm`、`dry_run_task` → `submit_task`（单 `--backend provider:chip` 标志）→ `query_task` / `poll_result` → `wait_for_result` / `get_result`，以及 `uqt_*` 任务 ID / shard 映射。
- `uniqc-result-analysis`: `UnifiedResult` 解析、counts / probability 表、histogram / distribution 可视化、Pauli 期望、circuit + timeline HTML、双跑对比（TV / Hellinger）。
- `uniqc-xeb-qem`: XEB 1q / 2q / parallel / parallel-CZ benchmarking、Readout 标定与 QEM（`ReadoutEM.apply` / `M3Mitigator.apply`），含 0.0.13 严格 pre-flight 策略 + `find_cached_results(result_type=...)`、`StaleCalibrationError` 注意事项、`~/.uniqc/calibration_cache/` 布局。

线路 & 模拟：

- `uniqc-circuit-interop`: 跨 `Circuit` / OriginIR / QASM2 / qiskit / pyqpanda3 互转 —— `AnyQuantumCircuit`、`normalize_to_circuit`、`Circuit.to_qiskit_circuit` / `Circuit.to_pyqpanda3_circuit`。
- `uniqc-noise-simulation`: `NoisySimulator` + `error_model` (Depolarizing / AmplitudeDamping / PauliError / Kraus / readout_error) + `ErrorLoader_GenericError|GateTypeError|GateSpecificError` + chip-backed dummy；含 0.0.13 NoisySimulator MRO fix。

算法类：

- `uniqc-qaoa`: 三层抽象的 QAOA —— `qaoa_workflow.run_qaoa_workflow` 一键、`qaoa_ansatz` + `pauli_expectation` + SciPy 手撸、以及真机 compile / batch / decode。
- `uniqc-quantum-ml`: PyTorch QML —— `QNNClassifier` / `QCNNClassifier` / `HybridQCLModel`（需 torchquantum）和 `QuantumLayer` parameter-shift 自动微分。
- `uniqc-algorithm-cases`: 规范化算法目录与模板 —— GHZ / W / Dicke / cluster / thermal state、QFT、QPE（位于 `uniqc.algorithms.core.circuits.qpe_circuit`，**不在顶层**）、Grover、amplitude estimation、Deutsch-Jozsa、VQE / VQD、state tomography、classical shadow。
- `uniqc-quantum-volume`: Quantum Volume (QV) 测试 —— 用 qiskit 构造方阵 QV 线路 → uniqc 加载 → ideal statevector + 真机采样 → heavy-output 概率 + 2/3 + 2σ pass/fail 判定，扫宽度并报告 `QV = 2^n_max`。
- `uniqc-classical-shadow`: 经典 shadow tomography —— `classical_shadow` / `shadow_expectation` / `run_classical_shadow_workflow` 单数据集、多 observable 估计；与 `state_tomography` / `pauli_expectation` 选型对比。

每个 skill 都遵循 `SKILL.md` + `references/` + `examples/` + `agents/openai.yaml` 的结构，可单独安装：`npx skills add ... --skill uniqc-cloud-submit`。

后续会继续在 `skills/` 下扩展更窄的专用 skill。

## 可以直接让 Agent 做什么

安装 `uniqc-basic-usage` 后，可以直接对 Agent 说这类请求：

- “帮我写一个 Bell state 的 UnifiedQuantum 示例，并导出 OriginIR。”
- “帮我把这段 QASM 转成更适合 `uniqc simulate` 的流程。”
- “帮我把这个线路先用 dummy 跑通。”
- “帮我打开 `uniqc config always-ai-hint` 并解释 CLI 的下一步提示。”
- “帮我根据 backend cache 看一下可用 backend。”

## 通过 npx skills 安装（推荐）

默认建议一次性安装本仓库下的所有 skills。当前只有 `uniqc-basic-usage`，后续新增算法开发、QEM、真机提交等专用 skills 后，下面的命令会一起安装。
这个命令与 `uniqc --help` 中展示的 AI 安装建议保持一致，是目前最推荐的安装方式。

### For Codex

安装到当前项目：

```bash
npx skills add IAI-USTC-Quantum/quantum-computing.skill \
  --agent codex \
  --skill '*'
```

全局安装到当前用户：

```bash
npx skills add IAI-USTC-Quantum/quantum-computing.skill \
  -g \
  --agent codex \
  --skill '*'
```

### For Claude Code

安装到当前项目：

```bash
npx skills add IAI-USTC-Quantum/quantum-computing.skill \
  --agent claude-code \
  --skill '*'
```

全局安装到当前用户：

```bash
npx skills add IAI-USTC-Quantum/quantum-computing.skill \
  -g \
  --agent claude-code \
  --skill '*'
```

### 安装到项目还是全局

不加 `-g` 时是项目级安装，适合只在当前仓库使用、或者希望团队通过仓库共享同一组 skills。项目级安装会写入当前目录下的 agent 配置目录：

- Codex: `.agents/skills/`
- Claude Code: `.claude/skills/`

加 `-g` 时是全局安装，适合个人常用、跨多个项目复用、不希望修改当前项目文件的情况。全局安装会写入用户目录：

- Codex: `~/.codex/skills/`
- Claude Code: `~/.claude/skills/`

如果你只想列出仓库里有哪些 skills，不安装，可以运行：

```bash
npx skills add IAI-USTC-Quantum/quantum-computing.skill --list
```

如果你确实想安装到所有已支持/检测到的 Agent，可以使用 `--all`；但日常更推荐显式写 `--agent codex` 或 `--agent claude-code`，避免安装到不需要的 Agent 目录。

## 仓库内容

- `skills/uniqc-basic-usage/`：通用 skill 主入口（基础使用、CLI、模拟、配置等）。
- `skills/uniqc-doctor-config/`：环境诊断 + 配置 / 依赖 / 缓存 / proxy / token 排查。
- `skills/uniqc-platform-verify/`：校验芯片元数据准确性（拓扑 / 标定 / 测得 vs 厂商）。
- `skills/uniqc-cloud-submit/`：流程类 —— 健康检查 + 真机提交 + 任务追踪。
- `skills/uniqc-result-analysis/`：流程类 —— 结果解析 + 可视化 + 期望值。
- `skills/uniqc-xeb-qem/`：流程类 —— XEB 标定（含 parallel-CZ） + 读出错误缓解。
- `skills/uniqc-circuit-interop/`：线路格式互转（Circuit / OriginIR / QASM2 / qiskit / pyqpanda3）。
- `skills/uniqc-noise-simulation/`：噪声建模 + `NoisySimulator` + chip-backed dummy。
- `skills/uniqc-qaoa/`：算法类 —— QAOA workflow / 手撸 / 真机。
- `skills/uniqc-quantum-ml/`：算法类 —— PyTorch QML（QNN / QCNN / Hybrid / QuantumLayer）。
- `skills/uniqc-algorithm-cases/`：算法类 —— 规范化算法目录与可运行模板。
- `skills/uniqc-quantum-volume/`：算法类 —— QV 测试（heavy-output 协议）。
- `skills/uniqc-classical-shadow/`：经典 shadow tomography（多 observable 单数据集估计）。

每个 skill 目录的内部结构：

- `SKILL.md`：skill 主入口（含 `description` front-matter）。
- `references/`：按主题整理的使用说明与排障参考。
- `examples/`：可独立运行的示例代码。
- `agents/openai.yaml`：SkillHub / OpenAI Agent 接口元数据。

## 通过 ClawHub 安装

```bash
# 访问 https://clawhub.ai/agony5757/quantum-computing 获取安装命令
```

ClawHub 支持直接从云端一键安装或克隆本 skill。

## 通过 SkillHub 发布

本 skill 已发布至 [SkillHub](https://www.skillhub.cn/skills/quantum-computing)，一个面向 AI Agent 的 Skill 市场，支持从云端直接安装。

## 许可证

Apache 2.0 许可证
