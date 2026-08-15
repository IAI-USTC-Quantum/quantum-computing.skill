# 模拟器与 dummy 参考

## 目录

- 选择哪种执行方式
- 本地模拟器
- shots 与 counts
- MPS 模拟器（大规模一维链）
- dummy backend
- 拓扑与 qubit remapping
- 从模拟走向真机

## 选择哪种执行方式

- **本地模拟器**：用于算法开发、概率分布、statevector/density matrix、优化循环。
- **dummy backend**：用于 task-manager、CLI submit/result、任务缓存和云端流程排练。
- **云平台 simulator**：用于检查平台 adapter、排队/任务查询接口和云端执行路径。
- **真机 backend**：用于最终硬件实验，提交前要检查 topology、qubit 质量、shots 和任务成本。

## 本地模拟器

安装：

```bash
pip install "unified-quantum[simulation]"
```

Python 用法（uniqc ≥ 0.0.13 — 统一 `Simulator`）：

```python
from uniqc import Circuit
from uniqc.simulator import Simulator

circuit = Circuit(2)
circuit.h(0)
circuit.cnot(0, 1)
circuit.measure(0)
circuit.measure(1)
# 注意：`circuit.measure(0, 1)` 把两个参数都当 qubit 列表，会变成 4 条 MEASURE，
# 触发 `simulate_pmeasure` 的 `measure_list size = 4` 错误。请逐个 qubit 调用。

sim = Simulator(backend_type="statevector")
# 0.0.13: 输入是 AnyQuantumCircuit —— Circuit / OriginIR str / QASM2 str / qiskit.QuantumCircuit / pyqpanda3
# 都可直接传，OriginIR/QASM 在运行时自动判别，program_type= 已废除。
probs = sim.simulate_pmeasure(circuit)
state = sim.simulate_statevector(circuit)
counts = sim.simulate_shots(circuit, shots=1000)

# 仍可直接传字符串：
probs2 = sim.simulate_pmeasure(circuit.originir)
probs3 = sim.simulate_pmeasure(circuit.qasm)
```

> ⚠ 0.0.13 breaking：`OriginIR_Simulator` / `QASM_Simulator` / `OriginIR_NoisySimulator` / `QASM_NoisySimulator` 全部移除；统一为
> `Simulator` / `NoisySimulator`（位于 `uniqc.simulator`）。`get_simulator(...)` / `create_simulator(...)` 也不再需要 `program_type=`。
> 旧代码做最小迁移：`from uniqc.simulator import OriginIR_Simulator` → `from uniqc.simulator import Simulator`，
> 构造函数去掉 `program_type=`，其余调用一致。

### 统一工厂入口（`get_simulator` / `create_simulator`）

```python
from uniqc.simulator import create_simulator, get_simulator

sim = create_simulator("statevector")
sim = create_simulator("mps", chi_max=128)
sim = get_simulator("statevector")     # 0.0.13：第二参数 program_type 已移除
```

### 含噪声本地模拟（`NoisySimulator` + `error_model.*`）

```python
from uniqc.simulator import NoisySimulator
from uniqc.simulator.error_model import (
    Depolarizing,
    AmplitudeDamping,
    ErrorLoader_GenericError,
)

# 在每个 gate 之后注入 1% depolarizing + 0.5% amplitude damping
loader = ErrorLoader_GenericError(generic_error=[
    Depolarizing(0.01),
    AmplitudeDamping(0.005),
])
sim = NoisySimulator(
    backend_type="density_matrix",  # 必须用 density matrix
    error_loader=loader,
    readout_error={0: [0.01, 0.02], 1: [0.01, 0.02]},
)
counts = sim.simulate_shots(circuit, shots=2000)
```

> 0.0.13 fix：之前的 `NoisySimulator` MRO 在某些路径上**绕过**了噪声注入；本版本恢复了正确顺序。如需更细粒度噪声建模，参见 `uniqc-noise-simulation` skill。

密度矩阵：

```python
sim = Simulator(backend_type="densitymatrix")
rho = sim.simulate_density_matrix(circuit)
```

### `Simulator` 方法速查

| 方法 | 返回类型 | 说明 |
|------|---------|------|
| `simulate_shots(circuit, shots) -> dict[int, int]` | counts dict | 有限采样结果，key 是按 cbit 顺序解码出的整数 |
| `simulate_pmeasure(circuit) -> list[float]` | 长度 `2**n_measured` 的概率向量 | 仅测量子集，向量长度按测量数决定 |
| `simulate_statevector(circuit) -> np.ndarray` | 复数 statevector，长度 `2**n_qubit` | 任何 `backend_type` 下都可用 |
| `simulate_density_matrix(circuit) -> np.ndarray` | `(2**n, 2**n)` 复矩阵 | **仅** `backend_type="density_matrix"` (或 `"densitymatrix"`) 时可用 |

**没有** `simulate(...)` 这种"统一入口"——必须显式调用上面四个方法之一。

CLI 用法：

```bash
uniqc simulate bell.ir --backend statevector --shots 1024 --format json
uniqc simulate bell.ir --backend density --shots 1024 --format json
```

## shots 与 counts

算法调试时优先看精确概率或 statevector；准备上云前再看有限 shots 的 counts。

```python
probabilities = sim.simulate_pmeasure(circuit.originir)
counts = sim.simulate_shots(circuit.originir, shots=4096)
```

解释结果时说明它们代表不同对象：

- probability/statevector：理想模拟分布
- counts：有限采样结果
- hardware counts：带有设备噪声、排队状态和平台后处理的真实实验结果

## MPS 模拟器（大规模一维链）

`MPSSimulator` 是 v0.0.11 起新增的纯 Python 矩阵乘积态模拟器，适合**大量比特、纠缠适中、一维最近邻**的电路（典型场景：Trotterized TFIM/Heisenberg、Floquet pump、QSP/QSVT）。

适用判定：

| 你的电路 | 推荐 |
|---|---|
| ≤ 24 比特、任意拓扑、要 statevector | `Simulator(backend_type="statevector")` |
| ≤ 28 比特、任意拓扑、要噪声 | `NoisySimulator` 或 `dummy:<platform>:<chip>` |
| > 28 比特、一维 NN、纠缠浅 | **`MPSSimulator` / `dummy:local:mps-linear-N`** |
| > 28 比特、深随机电路 | 没有 tractable 方案，请缩小比特数 |

直接 API：

```python
from uniqc import Circuit
from uniqc.simulator import MPSSimulator, MPSConfig

c = Circuit(64)
c.h(0)
for i in range(63):
    c.cnot(i, i + 1)

sim = MPSSimulator(MPSConfig(chi_max=64, svd_cutoff=1e-12, seed=42))
# Note: MPSConfig() defaults to chi_max=64. For high-entanglement / mid-depth
# random circuits pass chi_max=256 (or higher). [Some older docs claim 256 is
# the default — that is incorrect for current 0.0.11.x; the default is 64.]
counts = sim.simulate_shots(c.originir, shots=1000)   # ≤ 数百比特都可行
print(sim.max_bond, sim.truncation_errors[-3:])
# 仅 ≤ 24 比特时使用：
# psi = sim.simulate_statevector(c.originir)
# probs = sim.simulate_pmeasure(c.originir)
```

通过 dummy 后端调用（推荐用法，能走完整 task pipeline）：

```python
from uniqc import submit_task, wait_for_result

task = submit_task(circuit, backend="dummy:local:mps-linear-32:chi=64:cutoff=1e-10", shots=500)
result = wait_for_result(task, timeout=60)
```

后端 identifier 语法：

```
dummy:local:mps-linear-<N>[:chi=<int>][:cutoff=<float>][:seed=<int>]
```

约束（dry-run 阶段就会检查）：

- 双比特门必须最近邻 `(i, i+1)`，跨距 > 1 直接拒绝（请先编译为 SWAP-NN 形式）。
- 不支持 `controlled_by(...)` 与 `CONTROL/ENDCONTROL`。
- **不支持任何噪声**（`dummy:mps:*` 总是理想模拟）；要噪声请改 `dummy:<platform>:<chip>`。
- 支持的门：`H X Y Z S T SX I` / `RX RY RZ U1 U2 U3 RPhi RPhi90 RPhi180` / `CNOT CZ SWAP ISWAP ECR` / `XX(θ) YY(θ) ZZ(θ) XY(θ) PHASE2Q`.
- OriginIR 参数语法是 `XX q[0],q[1],(theta)`，**不是** `XX(theta) q[0],q[1]`。
- `simulate_pmeasure` 与 `simulate_statevector` 仍然会展平为 2^N 向量，因此在 N > 24 时会拒绝；请改用 `simulate_shots`（或 `submit_task` + `dummy:local:mps-linear-N`，后者内部就走 shots 路径）。

诊断字段：

- `sim.max_bond` — 实际达到的最大键维（理想 GHZ ≤ 2，深随机电路会顶到 `chi_max`）。
- `sim.truncation_errors` — 每次 SVD 截断丢掉的奇异值平方和；如果 max ≫ 1e-6 说明 χ 设小了。

## dummy backend

dummy backend 用于验证 task API、缓存、结果查询、拓扑约束和本地含噪执行流程。

```python
from uniqc import submit_task, submit_batch, wait_for_result

task_id = submit_task(circuit, backend="dummy", shots=1000)
result = wait_for_result(task_id, timeout=60)

line_task = submit_task(circuit, backend="dummy:local:virtual-line-3", shots=1000)
noisy_task = submit_task(circuit, backend="dummy:originq:WK_C180", shots=1000)
quark_noisy = submit_task(circuit, backend="dummy:quark:Baihua", shots=1000)

task_ids = submit_batch([circuit, circuit], backend="dummy", shots=1000)
results = [wait_for_result(task_id, timeout=60) for task_id in task_ids]
```

CLI（uniqc ≥ 0.0.13：单一 `--backend` 标志，`--platform` 已移除；不带 `--backend` 默认 `dummy:local:simulator`，裸 `dummy` 等价）：

```bash
uniqc submit bell.ir --backend dummy:local:simulator --shots 1000 --wait --format json
uniqc submit bell.ir --backend dummy:local:virtual-line-3 --shots 1000 --wait
uniqc submit bell.ir --backend dummy:originq:WK_C180 --shots 1000 --wait
uniqc submit bell.ir --backend dummy:quark:Baihua --shots 1000 --wait
```

Python API 中使用 `DummyOptions` 控制噪声模型：

```python
from uniqc import DummyOptions

opts = DummyOptions(noise_model={"depol_1q": 0.001, "depol_2q": 0.01})
task_id = submit_task(circuit, backend="dummy", shots=1000, options=opts)
```

使用建议：

- 写 cloud workflow 示例时，先给 dummy，再给 OriginQ/Quafu/Quark/IBM。
- `dummy` 通过后，如果关心拓扑，先换 `dummy:virtual-*`；如果关心真实芯片标定噪声，再换 `dummy:<platform>:<backend>`。
- chip-backed dummy 是规则型写法，不会出现在 `uniqc backend list` 中。
- 不要把无约束 `dummy` counts 当成硬件噪声模型结论。

## 拓扑与 qubit remapping

从本地模拟走向真实芯片时，要考虑可用 qubit 和耦合关系。优先使用 backend/chip characterization 或 RegionSelector，而不是手写固定 qubit 编号。

常见流程：

1. `uniqc backend list --platform originq`
2. `uniqc backend show originq:WK_C180`
3. `uniqc backend chip-display originq/WK_C180 --update`
4. 在 Python 中基于 topology/characterization 选择 region
5. 对线路做 qubit remapping，再提交

如果只是把逻辑线路重映射到一组可用 qubit，可查 `least_qubit_remapping`：

```python
from uniqc.remapper import least_qubit_remapping
```

## 从模拟走向真机

推荐检查清单：

1. 本地模拟给出合理概率分布。
2. dummy submit/result 跑通。
3. backend list/show 确认目标设备可用。
4. 根据 topology 和 qubit 质量选择 region。
5. 小 shots 真机试跑。
6. 保存 task id、backend、shots、线路源码和结果。
