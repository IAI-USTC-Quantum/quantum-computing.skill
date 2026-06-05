# 线路构建参考

## 目录

- 快速开始
- 初始化方式
- 常用属性、常用门与测量
- 控制与 dagger 上下文
- 命名寄存器、参数与可复用电路
- 复制、拼接、重映射、屏障
- 输出建议

当前 UnifiedQuantum 的核心对象仍然是 `Circuit`。新代码优先从 `uniqc` 顶层导入常用对象；只有需要底层类型时才进入 `uniqc.circuit_builder`。

最常见的工作流是：

1. 构建 `Circuit`
2. 导出 `originir` 或 `qasm`
3. 交给 `uniqc` CLI、模拟器或 `task_manager`

## 快速开始

```python
from uniqc import Circuit

c = Circuit()
c.h(0)
c.cnot(0, 1)
c.measure(0, 1)

print(c.originir)
print(c.qasm)
```

## 初始化方式

```python
from uniqc import Circuit

c = Circuit()          # 自动按使用到的 qubit 推断
c = Circuit(4)         # 固定 qubit 数
c = Circuit(qregs={"data": 4, "ancilla": 2})  # 命名寄存器
```

## 常用属性

| 属性 | 含义 |
|------|------|
| `originir` | OriginIR 文本（uniqc ≥ 0.0.15: 默认输出 **OriginIR-ext**，OriginQ 云提交前用 `to_originir_official()` 转换） |
| `qasm` | OpenQASM 2.0 文本 |
| `circuit` | 一般可视为 `originir` 别名 |
| `qubit_num` | 当前线路的 qubit 数 |
| `cbit_num` | 当前线路的 classical bit 数 |
| `depth` | 线路深度 |
| `used_qubit_list` | 实际用到的 qubit |
| `measure_list` | 已加入测量的 qubit |
| `opcode_list` | 内部 opcode 列表 |

## 常用门

### 单比特门

```python
c.h(0)
c.x(0)
c.y(0)
c.z(0)
c.s(0)
c.t(0)
c.sx(0)
c.sxdg(0)
c.identity(0)
```

### 旋转门

```python
c.rx(0, theta)
c.ry(0, theta)
c.rz(0, theta)
c.rphi(0, theta, phi)
c.u1(0, lam)
c.u2(0, phi, lam)
c.u3(0, theta, phi, lam)
```

### 双比特 / 三比特门

```python
c.cnot(0, 1)
c.cx(0, 1)
c.cz(0, 1)
c.swap(0, 1)
c.iswap(0, 1)
c.xx(0, 1, theta)
c.yy(0, 1, theta)
c.zz(0, 1, theta)
c.phase2q(0, 1, t1, t2, tzz)
c.uu15(0, 1, params)

c.toffoli(0, 1, 2)
c.cswap(0, 1, 2)
```

> `iswap / rphi / phase2q / xy / uu15` 没有 OpenQASM 2.0 内建等价表达，但 `c.qasm` 会**自动**为它们生成 `gate ... { ... }` 自定义定义并 inline 调用，所以 export → re-parse 的 round-trip 现在能完整工作（uniqc ≥ 0.0.11.dev22, A-U3）。如果导出 QASM 后给的目标工具链（如旧版 IBM Quantum）不支持自定义 gate def，可先 `from uniqc.compile import compile; compile(c, level=0)` 编译到 basis gates 后再导出。

## 测量

```python
c.measure(0)
c.measure(0, 1, 2)
```

测量会按调用顺序分配 classical bit。

## 控制与 dagger 上下文

```python
with c.control(0):
    c.x(1)
    c.z(2)

with c.dagger():
    c.h(0)
    c.rx(1, 0.5)
```

## 命名寄存器

```python
c = Circuit(qregs={"data": 4, "anc": 2})
data = c.get_qreg("data")

c.h(data[0])
c.cnot(data[0], data[1])
```

常用类型：

```python
from uniqc import Qubit, QReg, QRegSlice
```

## 参数与可复用电路

可复用子线路一般通过 `circuit_def` / `NamedCircuit` 表达：

```python
from uniqc import Circuit, circuit_def

@circuit_def(name="bell_pair", qregs={"q": 2})
def bell_pair(circ, q):
    circ.h(q[0])
    circ.cnot(q[0], q[1])
    return circ

c = Circuit(2)
bell_pair(c, qreg_mapping={"q": [0, 1]})
```

如果用户需要参数化子线路，优先沿这条路径组织，而不是手工约定一套外部模板格式。

## 复制、拼接、重映射

```python
c2 = c.copy()
c2.add_circuit(other)

mapped = c.remapping({0: 3, 1: 5})
```

`remapping()` 返回新线路，不会原地改动。

## 屏障

```python
c.barrier(0, 1, 2)
```

## 输出建议

最稳妥的导出方式通常是：

- 需要 CLI、云提交、dummy 模式时：优先 `originir`
- 需要和第三方工具交换时：使用 `qasm`

如果后续步骤涉及 `uniqc simulate`，建议先把输入统一到 OriginIR，再继续执行。

> Gotcha: `Circuit.originir` 是 **property**，不是方法。写 `c.originir`（不是 `c.to_originir()` / `c.originir()`）。同理 `c.qasm` 也是 property。

> **uniqc ≥ 0.0.15 提醒**：`c.originir` 现在默认输出 **OriginIR-ext**（官方 OriginIR 的严格超集，新增 `ECR` / `ISWAP` / `XX` / `YY` / `ZZ` / `XY` / `PHASE2Q` / `UU15` / `RPhi*`、`QRAM`、`DEF`/`ENDDEF`、内联 `dagger` / `controlled_by(...)`、错误信道）。
> - 本地 `Simulator` / `NoisySimulator` 与 `dummy:*` 后端都原生支持，无需转换。
> - 提交到 **OriginQ 真实硬件** 时只接受官方 OriginIR——若线路用到 ext-only 构造，请改写 `c.to_originir_official()`，或对裸文本调用 `uniqc.compile.convert_originir_ext_to_originir()`。普通线路（H/CNOT/RX/RY/RZ/CZ/MEASURE…）两种形式输出完全一致，旧代码不受影响。
> - 把 `Circuit` 对象直接传给 `submit_task(c, backend="originq:WK_C180", ...)`，uniqc 会自动做转换。

构建完成后，可用 `circuit_to_html()` 或 `schedule_circuit()` 可视化线路结构和时间线（见 [timeline-visualization.md](timeline-visualization.md)）。
