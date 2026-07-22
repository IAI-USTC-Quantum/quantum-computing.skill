# 云平台与真机实验参考

> ⚠️ 平台 extras 速查（uniqc ≥ 0.0.13）：所有 `originq` 提交路径（云端模拟器和真机）都需要 `pip install unified-quantum[originq]`（拉 `pyqpanda3`）；同理 `[quark]`（Quark, Python ≥ 3.12）。**IBM 与 chip-backed dummy backend `dummy:originq:<chip>` / `dummy:quark:<chip>` 的拓扑感知 compile 通道不再需要 extra**——qiskit / qiskit-aer / qiskit-ibm-runtime 已并入核心依赖（`[qiskit]` extra 已移除）。Quafu 已 archived：`[quafu]` extra **不存在**，需要时单独 `pip install pyquafu`，并接受 `numpy<2` 约束。
>
> 没装对应 extra 时，`submit_task(...)` 会抛 `MissingDependencyError`，且 0.0.13 起的报错消息会嵌入文档链接和具体修复提示。

## 目录

- 实验工作流
- 配置
- backend 发现与 cache
- Python task API
- RegionSelector 与芯片数据
- 平台建议
- 实验记录

## 实验工作流

把云端实验拆成固定步骤：

1. 构建或加载线路。
2. 本地模拟，确认概率分布符合预期。
3. dummy backend 跑通 submit/query/result。
4. 用 `uniqc backend list/show` 选择平台和 backend。
5. 需要真机时读取 chip characterization，选择 qubit region。
6. 小 shots 提交真实任务。
7. 查询结果并保存实验元数据。

这个顺序比直接提交真机更稳，也更容易定位失败发生在认证、线路、backend、任务队列还是结果解析。

## 配置

默认配置路径：

```text
~/.uniqc/config.yaml
```

CLI 配置：

```bash
uniqc config init
uniqc config set originq.token YOUR_ORIGINQ_TOKEN
uniqc config set quafu.token YOUR_QUAFU_TOKEN
uniqc config set quark.QUARK_API_KEY YOUR_QUARK_API_KEY
uniqc config set ibm.token YOUR_IBM_TOKEN
uniqc config set ibm.proxy.https http://127.0.0.1:7890
uniqc config set ibm.proxy.http http://127.0.0.1:7890
uniqc config always-ai-hint on
uniqc config validate
```

Python adapters 会读取配置。新代码优先通过顶级 `uniqc.config` 理解和操作项目级配置。IBM proxy 优先放进 `~/.uniqc/config.yaml`，这样 CLI、Python API 和测试路径能共用同一份网络配置。

> ⚠️ **环境变量真相**（破除常见误解）：uniqc 自己**只**读 `UNIQC_PROFILE` 以及 `HTTP(S)_PROXY`。它**不会**自动读取 `ORIGINQ_API_KEY` / `QUAFU_API_TOKEN` / `QUARK_API_KEY` / `IBM_TOKEN`。这些 token 必须写进 `~/.uniqc/config.yaml`：
>
> ```bash
> uniqc config set originq.token <TOKEN>
> uniqc config set quafu.token <TOKEN>
> uniqc config set quark.QUARK_API_KEY <TOKEN>
> uniqc config set ibm.token <TOKEN>
> ```
>
> 如果一定要用环境变量传 token，需要在自己的脚本里手动把 env → config 同步（参见 `examples/cloud_submission.py` 里的 `_sync_env_to_config` 辅助函数，那是脚本自己的便利封装，不是 uniqc 的内置行为）。
>
> 另外：旧版 `UNIQC_DUMMY` / `UNIQC_SKIP_VALIDATION` 环境变量在 0.0.11.dev10 起**已移除**。改用：
>   - **dummy 模式**：传 `backend="dummy"` / `backend="dummy:local:virtual-line-N"` / `backend="dummy:virtual:<name>"` / `backend="dummy:originq:WK_C180"` 等到 `submit_task` 即可激活，无需任何环境变量。
>   - **跳过提交前校验**：在 `submit_task(..., local_compile=0)` 上把本地 qiskit transpile 关掉；硬性的 IR 兼容性校验仍会执行（向 OriginQ 提交必须是 OriginIR、向 Quafu/IBM 提交必须是 OpenQASM 2.0）。同样地，`cloud_compile=0` 用来要求云端关闭自动编译。旧的 `auto_compile=` / `skip_validation=` 已删除。

不要把 token 写进示例代码、日志或 issue。

## backend 发现与 cache

首选 CLI：

```bash
uniqc backend list --platform originq
uniqc backend list --platform quafu
uniqc backend list --platform quark
uniqc backend list --platform ibm
uniqc backend list --format json
uniqc backend show originq:WK_C180
uniqc backend update --platform originq
uniqc backend chip-display originq/WK_C180 --update
```

Cache 位置：

- backend 列表 cache：`~/.uniqc/backend/backends.json`
- 芯片标定 cache：`~/.uniqc/backend/chips/`
- 任务 cache：`~/.uniqc/cache/tasks.sqlite`

用法建议：

- 开始实验时用 `--update` 强制刷新一次。
- 后续在同一轮开发里复用 cache。
- 如果 backend 不可用、排队太长或 topology 不适合，换 backend，不要硬提交。

## Python task API

公共入口：

```python
from uniqc import dry_run_task, submit_task, submit_batch, query_task, wait_for_result
from uniqc import UnifiedOptions
```

### UnifiedOptions 跨平台提交（uniqc ≥ 0.0.13）

`UnifiedOptions` 让你写 backend-agnostic 的提交代码：创建一次，在任何平台上复用：

```python
from uniqc import UnifiedOptions, submit_task, wait_for_result

# 跨平台选项
opts = UnifiedOptions(
    optimize_level=1,        # 0=不编译, >=1=启用编译（跨平台统一语义）
    error_mitigation=True,   # 读出纠错（平台不支持时自动 warn/raise）
    auto_mapping=True,       # 自动逻辑-物理 qubit 映射
    shots=1000,
    backend_name="originq:WK_C180",  # 可选，不填用平台默认
)

# 在任何平台上使用同一组选项
task_id = submit_task(circuit, backend="originq:WK_C180", options=opts)
task_id = submit_task(circuit, backend="ibm:ibm_fez", options=opts)
task_id = submit_task(circuit, backend="quark:Baihua", options=opts)
```

翻译表（`UnifiedOptions` → 平台 `BackendOptions`）：

| Unified 选项 | OriginQ | Quafu | Quark | IBM |
|---|---|---|---|---|
| `optimize_level=0` | `circuit_optimize=False` | 忽略 | `compile=False` | `circuit_optimize=False` |
| `optimize_level>=1` | `circuit_optimize=True` | `auto_mapping=True` | `compile=True` | `circuit_optimize=True` |
| `error_mitigation=True` | `measurement_amend=True` | warn/raise | `correct=True` | warn/raise |
| `auto_mapping=True` | `auto_mapping=True` | `auto_mapping=True` | warn/raise | `auto_mapping=True` |

不支持的选项默认发 `UserWarning`（`strict=True` 时抛 `BackendOptionsError`）。平台特定的 escape hatch（如 Quark 的 `open_dd`、IBM 的 `task_name`）仍然直接使用对应的 `BackendOptions` 子类。

dummy 排练：

```python
task_id = submit_task(circuit, backend="dummy", shots=1000)
result = wait_for_result(task_id, timeout=60)
```

### 自定义含噪虚拟机（v0.0.16）

`dummy:virtual:<name>` 从 `~/.uniqc/backend/virtual/<name>.yaml` 读取用户
定义的拓扑、门噪声、读出噪声和 T1/T2 热弛豫。离线生命周期是：

```bash
uniqc backend virtual init my-machine
# 编辑 ~/.uniqc/backend/virtual/my-machine.yaml
uniqc backend virtual list
uniqc backend virtual show my-machine
uniqc backend virtual validate my-machine
uniqc submit circuit.qasm --backend dummy:virtual:my-machine --shots 1000 --wait
```

`thermal_relaxation` 需要 `gate_times_ns`，T1/T2 用微秒表示且必须满足
`t2_us <= 2 * t1_us`。它与 `dummy:local:virtual-line-N` 不同：后者是内置
无噪拓扑 fixture；前者是具名的用户 YAML 含噪虚拟机。

拓扑和芯片标定路径：

```python
line_task = submit_task(circuit, backend="dummy:local:virtual-line-3", shots=1000)
noisy_task = submit_task(circuit, backend="dummy:originq:WK_C180", shots=1000)
```

> ⚠️ **历史问题已解决**：早期 `_route_with_fidelity` 的 `KeyError` 已在 `fix/audit-review` 上修复（NEW-U1）。`dummy:originq:<chip>` 路径已可正常使用。

`dummy:originq:WK_C180` 这类写法的设计初衷是按真实 backend compile/transpile，再本地含噪执行；它是**提交规则**（`submit_task(backend=...)` 专用），不是 `backend list` / `find_backend(...)` 里的枚举项。`find_backend('dummy:originq:WK_C180')` 直接抛 `ValueError: Backend ... not found`；`list_backends()` 只返回显式注册的后端（`dummy`、`dummy:local:virtual-line-N`、`dummy:local:virtual-grid-RxC`、`dummy:local:mps-linear-N`、`dummy:virtual:<name>`，加全部真实云后端）。**0.0.13 起**，chip-backed compile 通道直接走核心依赖中的 qiskit，不再需要 `[qiskit]` extra；并且 `_compile_for_chip_backed_dummy` 的早返回 bug 已修复，每条线路（即便 active qubits 全在 `available_qubits` 里）都会真正执行 basis-gate compile，避免 H/CNOT 直接喂给 simulator 触发 `TopologyError`。

> ⚠️ **OriginQ backend ID 大小写规则（务必严格遵守）**：
> - **真机 / `find_backend` / `submit_task` / `dry_run_task`**：必须使用大写 chip 名加 `originq:` 前缀，**不接受**小写或 `origin:` 前缀。例如 `originq:WK_C180` 可用，`originq:wk_c180` / `origin:WK_C180` / `origin:wk_c180` 全部抛 `ValueError`。
> - **`dummy:originq:<chip>` 路径**额外接受小写 alias（即 `dummy:originq:wk_c180` 也能解析为 `WK_C180`），但仅限 dummy 链路；不要把这个习惯带到真机入口。
> - 推荐做法：所有源码里写 chip 名一律大写，调用前用 `find_backend('originq:WK_C180')` 验证一次。

OriginQ 真机：

```python
from uniqc import Circuit, compile, find_backend, submit_task, wait_for_result

c = Circuit(2); c.h(0); c.cnot(0, 1); c.measure(0); c.measure(1)

backend_info = find_backend('originq:WK_C180')
c_native = compile(c, backend_info, level=2)         # H/CNOT → CZ/SX/RZ
# 0.0.13 breaking: backend 必须是 provider:chip 完整字符串。
# `submit_task(backend='originq', backend_name='WK_C180', ...)` 仍兼容；
# `submit_task(backend='originq', ...)`（无 chip）会抛 ValueError。
task_id = submit_task(c_native, backend='originq:WK_C180', shots=200)
result = wait_for_result(task_id, timeout=300)       # → UnifiedResult (dict-like over counts)
```

> 默认 `local_compile=1, cloud_compile=1`（uniqc ≥ 0.0.11.dev30）：本地用 qiskit `optimization_level=1` 编译并验证芯片 basis/topology，云端也开启自动编译。需要完全跳过本地编译可传 `local_compile=0`，需要本地深度优化可传 `local_compile=2` / `local_compile=3`。要让云端不再二次编译可传 `cloud_compile=0`。无论怎么设置，IR 语言兼容性的硬规则永远不会被绕过（OriginQ 必须 OriginIR、Quafu/IBM 必须 OpenQASM 2.0），不兼容直接抛 `UnsupportedGateError`。

> OriginQ 提交链路：`OriginQAdapter` 在把 OriginIR 喂给云端 pyqpanda3 解析器之前，会把 `SX q[i]` / `SX q[i].dagger` 自动改写成等价的 `RX q[i],(±π/2)`（NEW-U2.b fix, uniqc ≥ 0.0.11.dev30）。原因：尽管 OriginQ basis gate 集合声明含 SX，远端 OriginIR 解析器目前不接受 SX token。这次重写对用户透明，无需手动改电路。

真实提交前先 dry-run（与 `submit_task` 等价，两种 backend 写法都接受）：

```python
# 推荐统一写法：单字符串
check = dry_run_task(circuit, backend="originq:WK_C180", shots=100)
# 二元写法同样工作（D-U4 已对齐）
check = dry_run_task(circuit, backend="originq", backend_name="WK_C180", shots=100)
if not check.success:
    raise RuntimeError(check.error or check.details)
```

> `dry_run_task` 与 `submit_task` 现在 backend 写法**完全等价**（D-U4 fix, uniqc ≥ 0.0.11.dev22）：
> 都接受 `backend="originq:WK_C180"` 单字符串形式，也接受 `backend="originq"` + `backend_name="WK_C180"` 二元形式。推荐前者，更简洁。

Quafu simulator 或真机（**0.0.13 deprecated**：仅供兼容；新用户推荐 OriginQ / Quark / IBM）：

```python
# 提交前需要 `pip install pyquafu`（[quafu] extra 已移除），
# 并接受 `numpy<2` 约束。导入时会发 DeprecationWarning。
task_id = submit_task(
    circuit,
    backend="quafu:ScQ-Sim10",
    shots=100,
)
result = wait_for_result(task_id, timeout=300)
```

Quark 真机（需配置 `QUARK_API_KEY`，Python ≥ 3.12）：

```python
from uniqc import QuarkOptions

opts = QuarkOptions(chip_id="Baihua", compile=True)
task_id = submit_task(
    circuit,
    backend="quark:Baihua",
    shots=100,
    options=opts,
)
result = wait_for_result(task_id, timeout=300)
```

批量任务：

```python
# uniqc ≥ 0.0.12: submit_batch 返回单个 uniqc 任务 ID（uqt_*），
# 内部映射到一个或多个平台 task ID。wait_for_result 自动聚合。
uid = submit_batch(circuits, backend="dummy", shots=1000)
results = wait_for_result(uid, timeout=60)   # → list[UnifiedResult]
```

批量真机任务要更保守：先用 1 到 2 个小任务确认 backend、认证和线路都正常，再提交更大的批次。

### uniqc 任务 ID（`uqt_*`）⚠ 0.0.12 起的改动

`submit_task` 与 `submit_batch` 现在统一返回一个 **uniqc 自管理的任务 ID**，格式为 `uqt_<32 位 16 进制>`（共 36 字符）。它在内部映射到一个或多个平台原生的 task ID（保存在本地 sqlite 缓存的 `task_shards` 表里）。

为什么这么改：

- 不同平台返回的 ID 格式各异（OriginQ MD5、IBM `cp...`、Quafu UUID、dummy `0x...`），下游脚本经常因为格式假设而踩坑；现在统一成一种可识别格式。
- 当一个 batch 超过适配器的 `max_native_batch_size`（OriginQ 默认 200，可通过 `originq.task_group_size` 配置；IBM 默认 100；其他平台 1）时，uniqc 自动拆分为多次提交，对外仍然只暴露一个 task ID。
- 不支持原生批量的平台（Quafu/Quark/Dummy）会被视作 `max=1`，N 个线路对应 N 个 shard，但用户依然只拿到一个 ID。

#### 查看 shard 映射

```python
from uniqc import get_platform_task_ids
shards = get_platform_task_ids(uid)
for s in shards:
    print(s.shard_index, s.platform_task_id, s.circuit_count, s.status)
```

或在命令行：

```bash
uniqc task shards uqt_xxxxxxxx...           # 表格输出
uniqc task shards uqt_xxxxxxxx... -f json   # 机读
```

或通过 gateway HTTP：`GET /api/tasks/{uniqc_id}/shards`。

#### 兼容性与迁移

- 本地缓存里旧的平台 ID 行会在第一次访问时自动迁移成 `uqt_*` 父行 + 一个 shard（原 ID 保留在 `metadata.legacy_platform_id` 里）。
- `query_task(<平台 ID>)` 仍然可以用，但会触发 `DeprecationWarning` 并通过 shard 索引解析回父 ID。新代码请始终使用 `uqt_*`。
- 如果你**确实需要拿到底层平台 ID**（例如要在云控制台手动查询），传 `submit_batch(..., return_platform_ids=True)`，这会返回 `list[str]` 而不是 `uqt_*`。但 `query_task` / `wait_for_result` 仍以 `uqt_*` 为准。

### `wait_for_result` 的返回结构

`wait_for_result(task_id, ...)` 返回一个 **`UnifiedResult`** dataclass（uniqc ≥ 0.0.11.dev10）。它**同时**实现了 dict-like 协议（`result["00"]`、`for k in result`、`result.get(...)`、`len(result)`、`result.values()`），所以旧的"当 counts dict 用"的代码继续可用——counts 通过 dict 接口暴露：

```python
result = wait_for_result(task_id, timeout=300)
result["00"]            # 直接当 counts dict 索引（推荐）
sum(result.values())    # 总 shots
result.counts           # 显式拿 counts dict
result.probabilities    # 显式拿概率（同样 dict）
result.shots            # int
result.platform         # 'originq' / 'quafu' / 'quark' / 'ibm' / 'dummy'
result.task_id          # str
result.backend_name     # str | None
result.raw()            # 拿到平台原始 payload（用于 debug 或访问平台特有字段）
```

`result == {"00": 512, "11": 488}` 这样的等值比较（与普通 dict 比较 counts）也保持向后兼容。failure 路径返回 `None`，所以仍要做 `if result is None: ...` 判断。

如果只想要平台原始格式（不经 normalize），用 `result.raw()`。`normalize_*` 系列辅助函数（如 `normalize_originq_result`）依然存在，行为等价于 `wait_for_result` 内部逻辑。

## RegionSelector 与芯片数据

RegionSelector 用于把逻辑线路放到质量更好的物理 qubit 区域上。典型使用场景：

- 线路需要连续耦合区域。
- 目标 backend 的 qubit 质量差异明显。
- 希望避开不可用 qubit 或高错误率边。
- 需要在多个 candidate region 中做可重复选择。

推荐流程：

1. 刷新 backend/chip cache。
2. 读取目标 backend 的 topology 和 characterization。
3. 根据线路宽度、连通性和质量指标选择 region。
4. 对 circuit 做 remapping。
5. 把 remapping 信息写进实验记录。

不要把芯片表格截图当成唯一真值；在自动化流程里优先使用结构化 cache/API 数据。

最小代码示例：

```python
from uniqc.cli.chip_info import ChipCharacterization
from uniqc import RegionSelector, find_backend

backend = find_backend('originq:PQPUMESH8')                  # 小型 3-qubit 芯片
chip = ChipCharacterization.from_backend_info(backend)       # 或 from_dict(json) 加载缓存
sel = RegionSelector(chip)
chain = sel.find_best_1D_chain(length=3)
```

> 性能提示：`find_best_1D_chain` 现在**支持** `max_search_seconds` 参数（uniqc ≥ 0.0.11.dev10）。在 `originq:WK_C180`（169 qubit）这种大芯片上，建议传 `max_search_seconds=10.0` 限制搜索时间；超时会回退到当前最优解。`find_best_2D_from_circuit(circuit, min_qubits=N, max_search_seconds=10.0)` 也同样支持。

## 平台建议

### OriginQ

- 常用真机 backend 名可通过 `uniqc backend list --platform originq` 获取。
- 提交时使用 `backend_name=...`。
- 云端 simulator 适合验证平台任务路径，但不一定适合作为快速 smoke test。

### Quafu (deprecated 0.0.13)

- Quafu 在 0.0.13 起被 archived：`[quafu]` extra **不存在**；导入 Quafu adapter 会触发 `DeprecationWarning`；公共文档站默认隐藏 Quafu 卡片，仅推荐 `originq` / `ibm` / `quark` / `dummy`。
- 如确需使用：`pip install pyquafu`，并接受 `numpy<2` 约束。后续版本不保证 Quafu 路径的功能完整与正确性。
- `ScQ-Sim10` 适合做云端 simulator 级别检查；真机提交时用当前 backend list 里的 chip id。
- 如果线路不满足拓扑，优先启用 mapping 或先 remap。
- **0.0.13 fix**：Quafu adapter 现在端到端强制 `c[0]=LSB` bitstring 约定（与 OriginQ / dummy / simulator 一致）；之前自己写的字符串反转逻辑请删掉。

### Quark

- 配置 `QUARK_API_KEY`（不是 `token`）：`uniqc config set quark.QUARK_API_KEY <KEY>`。
- 安装：`unified-quantum[quark]`（Python ≥ 3.12）。
- 常用 backend：`Baihua`、`Dongling`，通过 `uniqc backend list --platform quark` 查看完整列表。
- 支持 compile、compiler selection、dynamical decoupling 和 readout correction 选项。
- 电路格式为 OpenQASM 2.0，UnifiedQuantum 自动从 OriginIR 转换。

### IBM

- 先确认本地 qiskit runtime 依赖和账号实例可用（0.0.13 起 qiskit / qiskit-ibm-runtime 已是核心依赖，不再需要 `[qiskit]` extra）。
- 如果直连 IBM Quantum 不稳定，先配置 `ibm.proxy.https` / `ibm.proxy.http`，再跑 `uniqc backend update --platform ibm`。`uniqc backend update --platform ibm` 在 0.0.13 实际上会刷新本地芯片 cache（之前由于 `_build_adapter(Platform.IBM)` 返回未实现 `list_backends` 的 `QiskitAdapter`，会被通用 `except Exception` 吞掉，号称成功但 cache 多日不刷新）。
- backend 可用性、region、排队状态会变化，提交前必须重新查 backend。
- **0.0.13 fix**：IBM/qiskit `query_batch` 之前在 `Sampler` 单 job 跨多个 PUB 时返回嵌套 `list[list[dict]]`，现已扁平化为 `list[dict]`，与 OriginQ adapter 一致。
- **0.0.13 fix**：Qiskit adapter 端到端强制 `c[0]=LSB` bitstring 约定，与 OriginQ / dummy / simulator 一致。

## 实验记录

每次真实提交都记录：

- UnifiedQuantum 版本和 Python 环境
- circuit 生成脚本或 OriginIR/QASM 文件
- platform/backend/chip id
- selected qubits / remapping
- shots
- task id
- submit/query/result 时间
- counts/probabilities
- 是否开启优化、measurement amend、auto mapping 等平台选项

如果要写论文式或报告式结果，保留原始 counts，不只保留归一化概率。

## 审计已配置后端（fetch_all_backends_with_status）

`audit_backends(...)` 与 `fetch_all_backends()` 不会告诉你哪个 platform 在 fetch 时失败（缺 SDK / token 错误等都被吞掉，得到空列表）。需要可见的失败信息时改用：

```python
from uniqc.backend_adapter.backend_registry import fetch_all_backends_with_status
from uniqc.backend_adapter.backend_info import Platform

result = fetch_all_backends_with_status()
print(result.backends.keys())     # 成功 fetch 的 platform → list[BackendInfo]
print(result.fetch_failures)      # 失败 platform → 异常信息
```

当前局限（uniqc 0.0.11.dev22）：

- `fetch_all_backends_with_status` 暂未在 `uniqc.*` 顶层导出，必须从 `uniqc.backend_adapter.backend_registry` 导入。
- 对 `Platform.QUARK / Platform.QUAFU` 的聚合分支当前可能直接跳过（即便 SDK 已装），因此 `fetch_all_backends_with_status()` 看不到这两个 platform。需要单独枚举时用 `fetch_platform_backends(Platform.QUARK)` / `fetch_platform_backends(Platform.QUAFU)` 直接拿。
