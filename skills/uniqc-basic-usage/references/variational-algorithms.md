# 变分算法参考

## 目录

- 当前公开 ansatz
- Ansatz 类型系统（uniqc ≥ 0.0.13）
- HEA（含硬件感知配置）
- HVA（Hamiltonian Variational Ansatz）
- QAOA ansatz（含变体）
- UCCSD ansatz
- ADAPT-VQE
- Parameter / Parameters 符号参数
- 一个典型 VQE 结构
- 一个典型 QAOA 结构
- 使用这些 ansatz 时记住

当前 UnifiedQuantum 对变分算法更适合从”ansatz 构造器 + 自己的目标函数 / 优化器”来理解，而不是依赖一套过度封装的旧接口。

## 当前公开 ansatz

```python
from uniqc import hea, hea_param_count, hva, qaoa_ansatz, uccsd_ansatz
from uniqc import EntanglingGate, EntanglementTopology, RotationGate
```

注意：

- 把这些函数当作线路生成器；优化器、目标函数和测量策略由任务决定。
- 参数维度要和 ansatz 层数、qubit 数、Hamiltonian 结构匹配。
- 生成线路后先本地模拟，再考虑 dummy 或真机任务。
- `hea_param_count(n_qubits, depth, ...)` 可以在构造电路前计算所需参数数量。

> ⚠️ **API 风格 caveat**：`hea / qaoa_ansatz / uccsd_ansatz` 都**返回新 `Circuit`**，与本节其余 ansatz 工厂保持一致。但 `uniqc` 顶层导出的电路构造器在历史上有两套风格：
> - **fragment 风格（推荐 / 当前默认）**：返回新 `Circuit`，可与 `add_circuit` 拼接 —— `hea / qaoa_ansatz / uccsd_ansatz / qft_circuit / qpe_circuit / ghz_state / w_state / dicke_state_circuit / cluster_state / grover_oracle / grover_diffusion / amplitude_estimation_circuit / vqd_ansatz / thermal_state_circuit / deutsch_jozsa_circuit`（见 `uniqc/algorithms/core/circuits/`）。
> - **in-place 风格（已弃用，仍可调）**：`fn(circuit, ...)` 第一个参数传现有 `Circuit` 时**就地修改**并返回 `None`，调用时会发 `DeprecationWarning`。新代码请只用 fragment 风格。
> 
> 完整测量类（`PauliExpectation / StateTomography / ClassicalShadow / BasisRotationMeasurement`）的设计见 [Algorithm Design](https://github.com/IAI-USTC-Quantum/UnifiedQuantum/blob/main/docs/source/2_advanced/algorithm_design.md) 或 `from uniqc import PauliExpectation, StateTomography, ClassicalShadow, BasisRotationMeasurement`。

## Ansatz 类型系统（uniqc ≥ 0.0.13）

```python
from uniqc import EntanglingGate, EntanglementTopology, RotationGate

# 旋转门选择
rotation = [RotationGate.RY, RotationGate.RZ]  # 每层每 qubit 的旋转

# 纠缠门选择
entangling = EntanglingGate.CZ                  # CNOT, CZ, ISWAP, CRX, CRY, CRZ, XX, YY, ZZ

# 拓扑选择
topology = EntanglementTopology.LINEAR           # LINEAR, RING, FULL, STAR, BRICKWORK, CUSTOM
```

- `EntanglingGate` 有两个子类：非参数化（CNOT, CZ, ISWAP，每边 0 额外参数）和参数化（CRX, CRY, CRZ, XX, YY, ZZ，每边 1 参数）。
- `EntanglementTopology` 决定纠缠层的连接方式；`CUSTOM` 需要传 `custom_edges`。
- `backend_info` 参数可以自动从硬件连接和 basis gates 选择最优拓扑和纠缠门（通过 `select_ansatz_config`）。

## HEA（含硬件感知配置）

```python
from uniqc import hea, hea_param_count
from uniqc import EntanglingGate, EntanglementTopology, RotationGate

# 基础用法（与旧版兼容）
circuit = hea(n_qubits=4, depth=2, params=params)

# 预计算参数数量
n_params = hea_param_count(n_qubits=4, depth=2)
params = np.random.randn(n_params) * 0.1
circuit = hea(n_qubits=4, depth=2, params=params)

# 自定义旋转门和纠缠门
circuit = hea(
    n_qubits=4,
    depth=3,
    params=params,
    rotation_gates=[RotationGate.RY, RotationGate.RZ],
    entangling_gate=EntanglingGate.CZ,
    topology=EntanglementTopology.RING,
)

# 硬件感知配置（自动选择拓扑和纠缠门）
from uniqc import find_backend
backend_info = find_backend("originq:WK_C180")
n_params = hea_param_count(n_qubits=4, depth=2, backend_info=backend_info)
params = np.random.randn(n_params) * 0.1
circuit = hea(n_qubits=4, depth=2, params=params, backend_info=backend_info)
```

特点：

- NISQ 友好，常用于 VQE / VQC
- 支持自定义旋转门集、纠缠门类型和拓扑
- `hea_param_count` 允许在构造电路前精确计算参数数量
- 传 `backend_info` 时自动根据硬件连接选择最优配置

## HVA（Hamiltonian Variational Ansatz）

```python
from uniqc import hva

# Hubbard 模型示例：hopping 和 interaction 两组
hopping = [("X0X1", 1.0), ("Y0Y1", 1.0)]
interaction = [("Z0Z1", 0.5)]
groups = [hopping, interaction]

circuit = hva(groups, p=2)
```

要点：

- `hamiltonian_groups` 是对易项组的列表，每组内算符互相对易
- `p` 是 ansatz 层数（完整组循环的重复次数）
- 参数长度 = `len(hamiltonian_groups) * p`
- `hf_state` 可指定 Hartree-Fock 初态（哪些 qubit 初始化为 |1⟩）
- 适合量子化学和凝聚态物理中的 Hamiltonian 模拟

## QAOA ansatz（含变体）

```python
from uniqc import qaoa_ansatz

cost_hamiltonian = [
    ("Z0Z1", 1.0),
    ("Z1Z2", 1.0),
]

circuit = qaoa_ansatz(
    cost_hamiltonian,
    p=2,
    betas=betas,
    gammas=gammas,
)
```

要点：

- `cost_hamiltonian` 形如 `[(pauli_string, coefficient), ...]`
- `betas`、`gammas` 长度都应等于 `p`
- 如果不给，构造器会随机初始化
- 支持问题特定的 mixer Hamiltonian 和多轮 schedule（uniqc ≥ 0.0.13）

## UCCSD ansatz

```python
from uniqc import uccsd_ansatz

circuit = uccsd_ansatz(
    n_qubits=4,
    n_electrons=2,
    params=params,
)
```

要点：

- 适合量子化学风格任务
- 默认先准备 Hartree-Fock 初态
- 参数长度取决于单激发 / 叫激发计数

## ADAPT-VQE

ADAPT-VQE（Adaptive Derivative-Assembled Pseudo-Trotter）是一种自适应变分算法，通过贪心选择 Pauli 算符池中最能降低能量的算符来逐步构建 ansatz。

```python
# ADAPT-VQE 基础设施已在 uniqc ≥ 0.0.13 中引入
# 核心组件：算符池（operator pool）和 Pauli 单元构造
from uniqc.algorithms.core.ansatz._operator_pool import OperatorPool
from uniqc.algorithms.core.ansatz._pauli_unitary import PauliUnitary
```

要点：

- 从预定义的 Pauli 算符池中迭代选择梯度最大的算符
- 适合量子化学问题，比固定 ansatz（如 UCCSD）更紧凑
- 算符池构建和 Pauli-string 解析（紧凑格式如 `"ZIZ"`）已在内部修复

## Parameter / Parameters 符号参数

```python
from uniqc.circuit_builder.parameter import Parameters

# 创建命名参数集
params = Parameters(n=6)  # 6 个参数
circuit = hea(n_qubits=2, depth=2, params=params)

# 参数可索引、可命名，支持符号优化
params[0]  # 访问第一个参数
```

要点：

- `Parameters` 是符号参数容器，替代原始 float 列表
- 支持索引访问、命名和符号优化（如与 PyTorch/autograd 集成）
- `hea`、`hva`、`qaoa_ansatz` 等 ansatz 工厂都接受 `Parameters` 或 `np.ndarray`

## 一个典型 VQE 结构

推荐这样组织 VQE：

1. 选 ansatz
2. 写一个目标函数
3. 在目标函数里调用模拟器得到概率或态矢
4. 用 `scipy.optimize.minimize` 或你自己的优化器迭代

示意：

```python
import numpy as np
from scipy.optimize import minimize
from uniqc import calculate_expectation, hea
from uniqc.simulator import Simulator

sim = Simulator(backend_type="statevector")

def objective(params):
    circuit = hea(n_qubits=2, depth=1, params=params)
    for q in range(2):
        circuit.measure(q)            # 显式测量，避免依赖 simulate_pmeasure 的隐式行为
    probs = sim.simulate_pmeasure(circuit)   # AnyQuantumCircuit input — 直接传 Circuit 即可
    return calculate_expectation(probs, "ZZ")

result = minimize(objective, x0=np.zeros(4), method="COBYLA")
```

### `calculate_expectation` 的 Hamiltonian 格式

`calculate_expectation(measured_result, hamiltonian)` 接受**位置式 `Z`/`I` 字符串**，长度必须等于 `n_qubit`，例如 `"ZZII"`（对前两个 qubit 取 ⟨Z⊗Z⟩，后两个忽略）。

它**不接受** `qaoa_ansatz.cost_hamiltonian` 那种带索引的 Pauli-string 写法（例如 `"Z0 Z1"`、`"Z0Z1"`）。如果你已经在用索引格式，需要先转成位置式字符串再传入；或者改用 `pauli_expectation(circuit, hamiltonian, ...)`，后者从 uniqc ≥ 0.0.11.dev22 起同时接受三种写法（C-U2 fix）：

- 紧凑位置式 `"ZIZ"`（长度 = `n_qubit`）
- 带索引 `"Z0Z1"` / `"Z0Z2"`
- 元组列表 `[("Z", 0), ("Z", 1)]`

### `calculate_multi_basis_expectation` 的语义陷阱

`calculate_multi_basis_expectation(measured_result, basis_label)` 只看 `basis_label` 的**第一个字符**，并在 **qubit 0** 上计算单比特期望：传 `"XX"` 等价于 `⟨X⟩` on qubit 0，**不是** `⟨X⊗X⟩`。要算多比特 Pauli 期望请改用 `pauli_expectation(...)`。

## 一个典型 QAOA 结构

1. 从图构造 cost Hamiltonian
2. 用 `qaoa_ansatz()` 生成电路
3. 用概率分布评估 cut value
4. 优化 `betas` / `gammas`

## 使用这些 ansatz 时记住

- 把 ansatz 当作“线路生成器”来解释
- 把优化器和目标函数当作用户可替换部分
- 不要把示例当成“唯一正确范式”
- 如果示例依赖本地模拟，明确标出 `simulation` extra
