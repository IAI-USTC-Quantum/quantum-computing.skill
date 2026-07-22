# CLI 使用参考

## 目录

- 基本工作流
- `uniqc doctor`：上手第一步
- 线路转换与检查
- 本地模拟
- dummy 与云端提交
- 任务查询
- 配置与 backend 发现
- 适合 CLI 的场景

## 基本工作流

CLI 入口是：

```bash
uniqc
```

备选模块入口：

```bash
python -m uniqc.cli
```

不要再推荐 `python -m uniqc` 作为入口；当前 release 中 package root 不提供该入口。

如果你要给当前环境下的 AI Agent（Codex/Claude Code）补齐基础技能，执行：

```bash
npx skills add IAI-USTC-Quantum/quantum-computing.skill --agent codex --skill '*'
npx skills add IAI-USTC-Quantum/quantum-computing.skill --agent claude-code --skill '*'
```

## `uniqc doctor`：上手第一步

uniqc ≥ 0.0.13 引入 `uniqc doctor` 子命令——一站式环境诊断：

```bash
uniqc doctor                # 默认完整体检
uniqc doctor --ai-hints     # 附 AI 渐进提示
```

它会按表打印：

1. **环境**：uniqc 版本、Python、OS、`~/.uniqc/config.yaml` 路径。
2. **依赖**：核心依赖（numpy / typer / rich / scipy / pyyaml）+ 可选组（originq / quafu / quark / qiskit / simulation / visualization / pytorch）的安装版本。
3. **配置**：每个平台的 token 是否配齐（脱敏显示前 6 字符）+ 缺失项给安装/配置命令提示。
4. **任务 DB**：`~/.uniqc/cache/tasks.sqlite` 的 schema 版本、行数、是否需要 migrate。
5. **后端 cache**：`~/.uniqc/backend/backends.json` 是否存在、最近一次 update 时间。
6. **平台连通性**：对配置过 token 的平台逐一做最低权限连通检查。

如果用户问「为什么 submit 一直失败」「环境是不是装坏了」「`pip install unified-quantum[qiskit]` 还需要吗」，**先让他跑 `uniqc doctor`**，再据其输出对症下药。深入的纯 config 校验仍可用 `uniqc config validate` 与 `uniqc config list`。

> ⚠ 小提醒：0.0.13 之前没有 `uniqc doctor`，老资料里写的「`uniqc doctor` 不存在，请用 `uniqc config validate`」已**过时**——两者并存，doctor 是上层入口，config validate 是下层细节。

CLI 的 AI 渐进式提示入口：

```bash
uniqc config list --ai-hint
uniqc backend list --ai-hints
UNIQC_AI_HINTS=1 uniqc config validate
uniqc config always-ai-hint on
```

`--ai-hints` 和 `--ai-hint` 等价。给弱一点的 agent 配环境时，推荐先运行 `uniqc config always-ai-hint on`，这样后续命令不用每次加参数也会显示下一步提示。不要推荐 `uniqc workflow --help`，除非当前版本 help 明确列出该子命令；通常 `workflow` 是文档页，不是 CLI 命令。

推荐 shell 工作流：

```bash
uniqc circuit input.qasm --format originir -o normalized.ir
uniqc simulate normalized.ir --backend statevector --shots 1024
uniqc submit normalized.ir --backend dummy:local:simulator --shots 1000 --wait
```

把 QASM、OriginIR 和 Python 线路先归一化成一个文件，可以减少不同入口之间的差异。

## 线路转换与检查

```bash
uniqc circuit bell.ir --info
uniqc circuit bell.ir --format qasm -o bell.qasm
uniqc circuit bell.qasm --format originir -o bell.ir
```

当用户只是想知道线路规模、门数、深度或格式是否能解析，先用 `uniqc circuit --info`。

## 本地模拟

常用后端：

```bash
uniqc simulate bell.ir --backend statevector --shots 1024 --format json
uniqc simulate bell.ir --backend density --shots 1024 --format json
```

用法建议：

- 先用 `statevector` 做快速功能验证。
- 需要噪声、混态或密度矩阵语义时用 `density`。
- 需要给后续脚本处理时加 `--format json`。
- 如果模拟命令提示缺依赖，安装 `unified-quantum[simulation]` 或 `unified-quantum[all]`。

## dummy 与云端提交

> ⚠ 0.0.13 breaking：`uniqc submit` 移除了 `--platform` / `-p` 标志，统一为单一 `--backend <provider>:<chip>`。
> 不带 `--backend` 默认 `dummy:local:simulator`；裸 `dummy` 等价于 `dummy:local:simulator`。
> 其它 CLI 子命令（`uniqc backend update --platform`、`uniqc task list --platform`、`uniqc result --platform`）**仍然**接受 `--platform`，那是按平台定位 cache/数据的旧语义，没动。

dummy 是本地任务管理和结果查询流程的首选排练后端：

```bash
uniqc submit bell.ir --backend dummy:local:simulator --shots 1000 --wait --format json
uniqc submit bell.ir --backend dummy:local:virtual-line-3 --shots 1000 --wait
uniqc submit bell.ir --backend dummy:originq:WK_C180 --shots 1000 --wait
uniqc submit bell.ir --backend dummy:local:mps-linear-12 --shots 500 --wait
```

- `dummy:local:simulator`（裸 `dummy` 是同义）：无约束、无噪声本地虚拟机。
- `dummy:local:virtual-line-N` / `dummy:local:virtual-grid-RxC`：内置虚拟拓扑，无噪声。
- `dummy:virtual:<name>`：`~/.uniqc/backend/virtual/<name>.yaml` 声明的用户含噪虚拟机。
- `dummy:local:mps-linear-N`：MPS / 张量网络模拟器（一维链）。
- `dummy:<platform>:<backend>`：复用真实 backend 拓扑和标定数据做本地含噪执行。

真实平台提交前，先列出 backend（这些 `backend` 子命令的 `--platform` 仍保留）：

```bash
uniqc backend list --platform originq
uniqc backend list --platform quark
uniqc backend list --platform ibm
# Quafu 已弃用：仅当用户明确需要时使用
uniqc backend list --platform quafu
```

OriginQ 示例：

```bash
uniqc submit bell.ir --backend originq:WK_C180 --shots 100 --wait
```

Quafu 示例（已 deprecated，仅做兼容支持）：

```bash
uniqc submit bell.ir --backend quafu:ScQ-Sim10 --shots 100 --wait
```

Quark 示例（需配置 `QUARK_API_KEY`）：

```bash
uniqc submit bell.ir --backend quark:Baihua --shots 100 --wait
```

IBM 示例：

```bash
uniqc submit bell.ir --backend ibm:ibm_fez --shots 100 --wait
```

如果不想立即提交真实任务，先做 dry run：

```bash
uniqc submit bell.ir --backend dummy:local:simulator --shots 100 --dry-run
uniqc submit bell.ir --backend originq:WK_C180 --shots 100 --dry-run
uniqc submit bell.ir --backend quark:Baihua --shots 100 --dry-run
```

## 任务查询

```bash
uniqc result TASK_ID --format json
uniqc task show TASK_ID         # 子命令是 `show`，不是 `status`（`uniqc task --help` 验证）
uniqc task list
```

如果想**等任务跑完并直接拿结果**，用 `uniqc result TASK_ID --wait`。`uniqc task show` 只读 cache 中的快照，不会主动等待或刷新远端状态。

结果通常会进入本地任务 cache。给用户写实验记录时，保留：

- circuit 文件或生成脚本
- platform/backend
- shots
- task id
- submission time
- result counts/probabilities

## 配置与 backend 发现

配置文件默认是 `~/.uniqc/config.yaml`。

Python 侧配置模块是顶级 `uniqc.config`，因为配置已经覆盖 profile、token、proxy、AI hints 等项目级状态，不再只是 backend adapter 的内部配置。旧的 `uniqc.backend_adapter.config` 可兼容旧代码，但新示例不要优先推荐它。

```bash
uniqc config init
uniqc config set originq.token YOUR_ORIGINQ_TOKEN
uniqc config set quafu.token YOUR_QUAFU_TOKEN
uniqc config set quark.QUARK_API_KEY YOUR_QUARK_API_KEY
uniqc config set ibm.token YOUR_IBM_TOKEN
uniqc config set ibm.proxy.https http://127.0.0.1:7890
uniqc config set ibm.proxy.http http://127.0.0.1:7890
uniqc config validate
```

Quark 必须用 **`QUARK_API_KEY` 字段名**（不是 `token`），`uniqc config validate` 通过 `PLATFORM_REQUIRED_FIELDS` 强制校验这一点；写成 `quark.token` 会被报错。

Backend 发现：

```bash
uniqc backend update
uniqc backend list --format table
uniqc backend list --format json
uniqc backend show originq:WK_C180
uniqc backend chip-display originq/WK_C180 --update
```

用 `uniqc backend update` 刷新 backend 列表 cache；用 `chip-display ... --update` 刷新芯片标定 cache。不用时优先复用本地 cache，避免反复打云端 API。

## 标定与 QEM

CLI 标定命令（结果自动缓存到 `~/.uniqc/calibration_cache/`）：

```bash
# XEB benchmarking（1q / 2q / parallel）
uniqc calibrate xeb --qubits 0 1 2 3 --type 1q --backend dummy --shots 1000 --depths 5 10 20 40
uniqc calibrate xeb --qubits 0 1 --type 2q --backend dummy --shots 1000

# Readout 标定（1q / 2q joint）
uniqc calibrate readout --qubits 0 1 --backend dummy --shots 1000

# Pattern 分析（DSatur 并行分组）
uniqc calibrate pattern --qubits 0 1 2 3 4 5
uniqc calibrate pattern --type circuit --circuit my_circuit.ir
```

标定后可用 Python API 做 QEM（见 [references/calibration-qem.md](calibration-qem.md)）。

## 适合 CLI 的场景

优先用 CLI：

- 格式转换
- 快速模拟
- 配置检查
- backend 列表和芯片标定查看
- 单个任务提交与结果拉取

优先用 Python API：

- 参数化线路
- 批量任务
- VQE/QAOA 优化循环
- 自动选择 qubit region
- 需要把结果接入 pandas、SciPy、PyTorch 或自定义分析代码
