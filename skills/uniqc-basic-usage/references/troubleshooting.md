# 通用排错参考

## 目录

- 排错顺序
- 环境快照
- 安装与 extra
- CLI 与 Python 不一致
- 云端任务失败
- 结果看起来不对
- OriginIR 解析与门名陷阱
- MPS 模拟器排错
- 何时上报 issue

## 排错顺序

先解决用户正在做的具体工作流，不要一开始就展开版本历史。

1. 回到对应 feature reference：CLI、simulator、cloud、variational、PyTorch。
2. 拍环境快照，确认当前解释器和 `uniqc` 是同一套环境。
3. 用最小线路复现。
4. 区分解析错误、依赖错误、认证错误、backend 错误、平台队列/任务状态错误。
5. 如果最小复现仍像库问题，再查当前文档、GitHub issue 和源码。

## 环境快照

```bash
which python3
python3 --version
python3 -c "import uniqc, sys; print('uniqc', getattr(uniqc, '__version__', 'unknown')); print(uniqc.__file__); print(sys.executable)"
which uniqc || true
uniqc --help | head -40
```

如果 `python -m uniqc.cli` 和 `uniqc` 行为不同，优先处理 PATH/venv 问题。不要使用 `python -m uniqc` 作为排错入口（package root 不提供）。

## 安装与 extra

完整量子算法和云端开发环境：

```bash
uv pip install "unified-quantum[all]"
```

按功能拆分时（uniqc ≥ 0.0.13）：

- 核心：`pip install unified-quantum`（已自带 numpy / typer / rich / scipy / pyyaml / qiskit / qiskit-aer / qiskit-ibm-runtime——IBM、Qiskit、`dummy:originq:<chip>` / `dummy:quark:<chip>` 的 chip-backed compile 通道**都不再需要 extra**）
- 本地高级模拟（qutip）：`unified-quantum[simulation]`
- 可视化：`unified-quantum[visualization]`
- OriginQ：`unified-quantum[originq]`
- Quark：`unified-quantum[quark]`（Python ≥ 3.12）
- Quafu：**已 archived，`[quafu]` extra 不存在**——如必须用，单独 `pip install pyquafu` 并接受 `numpy<2`。
- PyTorch：`unified-quantum[pytorch]`

缺 `qutip`、`torch`、`pyqpanda3` 时，先判断是不是缺 extra，不要立刻当作核心库损坏。`qiskit` 装不上请按核心包重装：`pip install --upgrade unified-quantum`。0.0.13 起 `MissingDependencyError` 的报错消息会嵌入文档链接 + 具体修复指令，按提示操作即可。

体检入口：`uniqc doctor` 会一次性列出每个依赖组的安装状态、token 配齐情况、cache 状态，是首选自检命令。

## CLI 与 Python 不一致

常见原因：

- shell 里的 `uniqc` 来自另一个 Python 环境。
- Jupyter kernel 和终端不是同一个 venv。
- 用户改了 `~/.uniqc/config.yaml`，但进程环境里还有旧 token。
- 本地 backend/cache 过期。

处理：

```bash
python -m uniqc.cli --help
uniqc config validate
uniqc backend list --format json
uniqc backend chip-display originq/WK_C180 --update
```

必要时清楚地告诉用户当前命令实际用的是哪个解释器，不要含糊说“环境有问题”。

## 云端任务失败

按层定位：

1. 配置：`uniqc config validate`
2. backend：`uniqc backend list --platform ...`
3. 线路：先 `uniqc simulate` 或 dummy submit
4. 平台参数：OriginQ 用 `backend_name`，Quafu 用 `chip_id`
5. 任务状态：`query_task` / `uniqc task show TASK_ID`（不是 `task status`）
6. 结果：`wait_for_result` timeout 不等价于提交失败，继续查 `uniqc task show`；要等到完成再拿结果，用 `uniqc result TASK_ID --wait`

如果 timeout，先返回 task id 和查询命令，让用户能继续追踪。

## 结果看起来不对

先区分结果类型：

- statevector/probability：理想模拟
- local shots counts：本地采样
- dummy counts：任务流程排练结果
- hardware counts：真实设备实验结果

检查项：

- measurement 是否覆盖了需要的 qubit
- bitstring 顺序是否符合用户后处理假设
- shots 是否太少
- 是否对线路做了 remapping
- 真机是否开启平台级 mapping、optimization、measurement amend
- 是否混用了概率和 counts

## OriginIR 解析与门名陷阱

来自 floquet-pump 实验（2026-05）的实战教训：

| 错误信息 / 症状 | 原因 | 处理 |
|---|---|---|
| `NotImplementedError: A invalid line: RXX(...) q[a],q[b]` | OriginIR 里 Ising 旋转门是 `XX/YY/ZZ`，**不是** `RXX/RYY/RZZ`（Qiskit 风格） | 用 `XX q[a],q[b],(theta)` 等写法；如果是从 Qiskit 转过来的电路，先在导出阶段统一名字 |
| `NotImplementedError: A invalid line: XX(theta) q[a],q[b]` | 参数语法错了 | OriginIR 是 `GATE q[..],q[..],(p1,...)`，参数永远在末尾的圆括号里，不在门名后 |
| `OriginIR input does not have correct CREG statement.` | 直接拼字符串时漏了 `CREG N` | `QINIT N` 后面**必须**紧跟 `CREG N`（或对应宽度），即使用不到经典寄存器 |
| `ValueError: Qubit exceeds the maximum (QINIT n)` | 直接生成 IR 时 `QINIT` 宽度小于实际用到的 qubit 索引 | 把 `QINIT` 设成 `max(qubit_index)+1` 或交给 `Circuit` 自动算 |
| `Circuit.measure(q, c)` 在 IR 里出现两次 MEASURE 同一 q | 当前 `Circuit` 对每次 measure 都生成一条 OriginIR 行 | 多次 measure 不会损坏统计，但 result counts 的位宽会变（每条 MEASURE 对应一位 cbit），后处理时按 cbit 顺序解码而不是按 qubit |
| `ReadoutCalibrator(adapter=BackendInfo)` 报错或返回空 | calibrator 期望一个**带 `submit` 方法的 adapter**，而 `BackendInfo` 只是元数据容器 | 传具体平台 adapter，如 `OriginQAdapter`、`QuafuAdapter`，或在 dummy 流程里传 `DummyAdapter` 实例 |

## MPS 模拟器排错

| 症状 | 原因 | 处理 |
|---|---|---|
| `MPSSimulator: long-range 2q gate 'CNOT' on (0,3) is not supported` | MPS 不接受跨距 > 1 的双比特门 | 先 SWAP 到最近邻；或换 `Simulator(backend_type="statevector")` |
| `NotImplementedError: MPSSimulator does not support CONTROL...` | 任意控制门不在 MPS 引擎支持范围内 | 把控制门展开到 `CNOT/CZ` 加单比特门，或换稠密模拟器 |
| `MPSSimulator.simulate_pmeasure refuses to materialise a 2**N probability vector` | N > 24 时不允许展平 | 改用 `simulate_shots(...)`；或通过 `submit_task(..., backend="dummy:local:mps-linear-N")`，dummy adapter 内部自动走 shots 路径 |
| `dummy:local:mps-linear-N` 跟 `noise_model` 一起用时报错 | MPS 路径强制无噪声 | 想要含噪 + 大 N？目前没有 tractable 的开箱方案；要么缩小 N 用 `dummy:<platform>:<chip>`，要么手动在测量后做 readout error mitigation |
| `sim.truncation_errors` 的最大值很大（≫ 1e-4） | `chi_max` 设小了，电路真实键维超过它 | 加大 `chi_max`（成本 O(χ³)）；或者承认这个电路对 MPS 不友好，换稠密 |
| 结果跟预期相反，比如 GHZ 出来全 0 | bitstring 顺序约定 | uniqc 整体采用 **q0 = LSB** 约定；从右往左数第 0 位才是 q0。MPS 输出的 statevector 与 counts 都遵守这条 |



只有在满足这些条件后再建议上报：

- 当前环境和版本已经明确。
- 最小线路能复现。
- 不是缺 extra、token、PATH、cache 或 backend 当前不可用。
- 行为与当前 README/API 文档明显冲突。

Issue 内容应包含：

- 安装方式和版本
- Python 版本与 OS
- 最小代码或最小 CLI 命令
- 完整 traceback 或任务状态
- 期望行为与实际行为
- 是否涉及真实云端 task id，注意不要泄露 token

## 标定与 QEM 排错

| 症状 | 原因 | 处理 |
|------|------|------|
| `StaleCalibrationError` | 标定数据超过 `max_age_hours` TTL | 重新执行 `uniqc calibrate readout` 或 `uniqc calibrate xeb`，或在 Python API 中增大 `max_age_hours`。注意 `StaleCalibrationError` 直接继承自 `Exception`（不是 `UnifiedQuantumError`），需要显式 `except StaleCalibrationError:` 才能捕获。 |
| `FileNotFoundError` in `M3Mitigator` | 标定 cache 文件不存在 | 先执行 `uniqc calibrate readout` |
| 在 dummy backend 上做 QEM 结果全零 | DummyAdapter 返回的 counts 默认是无噪声的 | QEM 在 dummy 上无实际意义；用含噪 dummy（`dummy:originq:WK_C180`）或真机才有校准效果 |
| `TimelineDurationError` | 逻辑线路没有门时长数据 | 传入 `gate_durations` dict，或使用 `backend_info` 带时长信息的 backend |

## 常见异常速查（uniqc.exceptions）

`uniqc/exceptions.py` 公开导出以下异常，用于在 `try / except` 分支中精准捕获。除 `StaleCalibrationError` 外，所有都继承自 `UnifiedQuantumError`，可一并捕获。

| 异常 | 触发场景 |
|------|----------|
| `UnifiedQuantumError` | 所有 uniqc 自定义异常的基类（除 `StaleCalibrationError`） |
| `BackendNotFoundError` | `find_backend()` / `_get_adapter()` 找不到后端；通常是平台名错或缺 extras |
| `CompilationFailedError` | `compile()` / `compile_for_backend()` 失败；最常见原因是目标不在 basis set 或 qiskit transpile 路径出错（0.0.13 起 qiskit 是核心依赖，不再可能因缺 `[qiskit]` extra 而触发） |
| `UnsupportedGateError` | 提交时 IR 语言或门集不在芯片白名单（IR 不兼容时硬抛，与 `local_compile` / `cloud_compile` 无关；门集不兼容且 `local_compile=0` 时抛） |
| `CircuitTranslationError` | OriginIR ↔ QASM/适配器格式转换失败 |
| `TaskFailedError` | `wait_for_result` 看到 task 在云端进入 failed 状态 |
| `TaskNotFoundError` | `query_task` / `wait_for_result` 找不到 task id（已 GC 或拼错） |
| `TaskTimeoutError` | `wait_for_result(timeout=...)` 超时 |
| `AuthenticationError` | adapter 收到 401 / unauthorized；检查 `~/.uniqc/config.yaml` 里的 token |
| `InsufficientCreditsError` | 平台返回余额不足/billing 错误 |
| `QuotaExceededError` | 平台返回限流/配额超出 |
| `NetworkError` | 连接失败、DNS、超时、refused |
| `ConfigValidationError` | `uniqc config validate` 检测到 schema 不符 |
| `NotMatrixableError` | `Circuit.get_matrix()` 在含测量/经典控制等不可矩阵化的线路上调用 |
| `TimelineDurationError` | timeline 调度缺门时长（详见上节） |
| `StaleCalibrationError` | 标定数据 TTL 超时（**继承自 `Exception`，不是 `UnifiedQuantumError`**） |

`AuthenticationError / InsufficientCreditsError / QuotaExceededError / NetworkError` 由 `_map_adapter_error` 在 originq adapter 路径上根据底层异常关键字映射；其他平台 adapter 暂未走这条映射，可能直接抛 `RuntimeError / ValueError`。
