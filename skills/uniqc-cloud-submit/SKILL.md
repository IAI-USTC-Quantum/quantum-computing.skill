---
name: uniqc-cloud-submit
description: "Use when the user wants an end-to-end cloud / real-hardware submission with UnifiedQuantum (uniqc ≥ 0.0.13): run `uniqc doctor` for environment health, validate API keys, ask for / load a quantum-program file (.originir / .qasm / .py) or pass any AnyQuantumCircuit input, dry-run, `submit_task` (single `--backend <provider>:<chip>` flag — `--platform` removed in 0.0.13), query status with `query_task` / `poll_result`, fetch with `wait_for_result` / `get_result`. Also covers writing a circuit in Python and persisting it as a quantum-program file. Applies to OriginQ / Quark / IBM and chip-backed dummy backends; Quafu is deprecated."
---

# Uniqc Cloud Submission Skill

This skill is the **operational** counterpart to `uniqc-basic-usage`. Use it when
the user wants to actually push a circuit to a backend (real hardware, cloud
simulator, or chip-backed dummy) and then track the task to results.

The end-to-end shape is always the same:

1. **Health-check** the environment (`uniqc doctor`; deeper config-only:
   `uniqc config validate` / `uniqc config list`).
2. **Pick or build** a quantum-program file — `.originir`, `.qasm`,
   or a Python script that constructs a `Circuit` and writes one of the above.
   `submit_task` accepts the unified `AnyQuantumCircuit` input
   (Circuit / OriginIR str / QASM2 str / qiskit `QuantumCircuit` / pyqpanda3
   circuit) — pre-saving to a file is optional but helpful for `uniqc submit`.
3. **Dry-run** the submission to catch backend / IR / topology errors locally.
4. **Submit** via `uniqc submit ... --backend <provider>:<chip>` (CLI;
   single `--backend` flag — `--platform` is **gone** as of uniqc 0.0.13)
   or `submit_task` / `submit_batch` (Python; `backend=` requires the
   full `provider:chip` string — bare `"originq"` / `"ibm"` raises).
   Always returns a uniqc-managed task id `uqt_<32-hex>` (uniqc ≥ 0.0.12).
5. **Query** with `uniqc task show <uid>` / `query_task(uid)` /
   `poll_result(uid)` (non-blocking single-shot status check).
6. **Wait & fetch** with `uniqc result <uid> --wait` /
   `wait_for_result(uid, timeout=...)` / `get_result(uid, timeout=...)`
   ("I want the answer" alias for `wait_for_result`).

> ✅ As of uniqc 0.0.13, **`uniqc doctor` exists** and is the canonical
> first-line health-check (environment + dependency groups + tokens +
> task DB + backend cache + connectivity in one command). Run it before
> anything else. `uniqc config validate` / `uniqc config list` remain
> useful for the deeper config-only details.

## First decision — branch by user intent

| User goal                                              | Read first                                              |
| ------------------------------------------------------ | -------------------------------------------------------- |
| "Check my keys / why is my submit failing on auth?"   | [references/health-check.md](references/health-check.md) |
| "I have a circuit in Python — how do I save it?"      | [references/authoring-program-files.md](references/authoring-program-files.md) |
| "I have an `.originir` / `.qasm` file — submit it."   | [references/submit-and-poll.md](references/submit-and-poll.md) |
| "How do I batch many circuits in one task id?"        | [references/submit-and-poll.md](references/submit-and-poll.md) (`submit_batch` section) |
| "What does the resulting `uqt_*` id map to?"          | [references/task-ids-and-shards.md](references/task-ids-and-shards.md) |

For result inspection / plotting after `wait_for_result`, hand off to
the **`uniqc-result-analysis`** skill.

## Recommended interactive flow when the user has not given a circuit

If the user asks "submit a circuit for me" without a concrete file, **do not
guess**. Ask once:

> Which circuit do you want to submit? You can give me one of:
>
> 1. A path to an `.originir` / `.qasm` file, or
> 2. A path to a `.py` script that builds and prints a `Circuit`, or
> 3. A short description ("Bell state, 2 qubits") — I'll generate the file.
>
> Also which backend? (e.g. `dummy`, `originq:WK_C180`, `quark:Baihua`, `ibm:ibm_fez`)

Then:
1. If option 3, write the circuit to `circuit.py` + dump
   `circuit.originir` to `circuit.originir` (and `circuit.qasm` to
   `circuit.qasm` for IBM/Quafu).
2. Run `uniqc config validate` and `uniqc config list` — make sure the chosen
   platform shows `Configured`.
3. Always **dry-run before real submit**.
4. Show the user the `uqt_*` id and explain how to re-attach later.

## Practical defaults

- **Always** pass `backend=` as a single `"<provider>:<chip>"` string
  to `submit_task` — uniqc 0.0.13 enforces `provider:chip-name` format and
  raises on bare `"originq"` / `"ibm"`. Use `"originq:WK_C180"`,
  `"ibm:ibm_fez"`, `"quark:Baihua"`, or a `"dummy:..."` rule string.
  The legacy two-arg form (`backend="originq", backend_name="WK_C180"`)
  still works but is no longer the recommended pattern.
- **OriginIR-ext default emission (uniqc ≥ 0.0.15)** — `Circuit.originir`
  now returns **OriginIR-ext** (strict superset of official OriginIR with
  `ECR`/`ISWAP`/`XX`/`YY`/`ZZ`/`XY`/`PHASE2Q`/`UU15`/`RPhi*`, `QRAM`,
  `DEF`/`ENDDEF`, inline `dagger`/`controlled_by(...)`, error channels).
  - Local `Simulator` / `NoisySimulator` and `dummy:*` backends accept
    both languages natively — nothing to change.
  - **OriginQ cloud** only accepts official OriginIR. If your circuit
    uses any ext-only construct, persist with `c.to_originir_official()`
    (Python) or feed raw ext text through
    `uniqc.compile.convert_originir_ext_to_originir()`. Plain circuits
    (H/CNOT/RX/RY/RZ/CZ/MEASURE …) round-trip unchanged, so existing
    Bell-pair snippets keep working — the conversion call is the
    safe-by-default pattern. Passing the `Circuit` object directly to
    `submit_task(c, backend="originq:WK_C180", ...)` lets uniqc do the
    conversion for you.
- For OriginQ real hardware, **compile first** and pass the compiled
  `Circuit`:
  ```python
  from uniqc import compile, find_backend, submit_task
  bi = find_backend("originq:WK_C180")
  c_native = compile(my_circuit, bi, level=2)
  uid = submit_task(c_native, backend="originq:WK_C180", shots=200)
  ```
  If you skip the compile, `local_compile=1` (default) does it for you via
  qiskit, which is now a **core dependency** in uniqc 0.0.13 (no extra
  install required); set `local_compile=0` to skip. `auto_compile` is also
  fixed in 0.0.13 to actually run when no `compile_options` are provided.
- **Packaging extras (uniqc ≥ 0.0.15)** — `[all]` is the broadly-installable
  superset but **no longer pulls in `[quark]`** (quarkstudio has no
  cp314/win32 wheels). Install Quark explicitly with `[quark]` on
  Linux/macOS Python 3.12–3.13. The `[originq]` extra is gated to
  `python_version < '3.14'` until pyqpanda3 publishes a cp314 wheel. The
  core package (and `[simulation]` / `[visualization]` / `[pytorch]`)
  supports cp310–cp314.
- For Quark / IBM: same single-string `backend="<provider>:<chip>"` works,
  shots small (≤ 200) for the first real attempt. Quafu is **deprecated and
  archived** in 0.0.13 — `[quafu]` extra removed; users that still need
  Quafu install `pyquafu` directly with `pip install pyquafu` and accept
  `numpy<2`. New code should target OriginQ / Quark / IBM.
- Never log full tokens. Read them from `~/.uniqc/config.yaml` via
  `uniqc.config.get_*_config(...)`, not from the user prompt.
- All submits return a single string id of the form `uqt_<32-hex>` (36 chars).
  Treat platform-native ids (OriginQ MD5, IBM `cp...`, Quafu UUID) as
  legacy — they still resolve in `query_task` but emit `DeprecationWarning`
  that mentions the **0.1.0 deprecation cliff** (every currently-deprecated
  API is removed at uniqc 0.1.0).
- `wait_for_result(uid)` (and its `get_result(uid)` alias) returns one
  `UnifiedResult` for single-circuit tasks and `list[UnifiedResult]` for
  batches — branch on `isinstance(_, list)`. `poll_result(uid)` returns
  `TaskInfo` immediately for non-blocking status checks.
- Bitstring convention is now `c[0]=LSB` end-to-end across OriginQ / dummy /
  simulator **and** Quafu / IBM (0.0.13 fix). If you previously hand-reversed
  Quafu/IBM bitstrings to align with OriginQ, drop the reversal.

## CLI cheat sheet

```bash
# 0. health (uniqc ≥ 0.0.13)
uniqc doctor                       # full env + deps + tokens + cache + connectivity
uniqc config validate              # deeper config-only check
uniqc config list

# 1. authoring (Python -> file)
python build_circuit.py            # writes circuit.originir / circuit.qasm

# 2. dry-run (no quota spent) — single --backend flag, --platform is gone in 0.0.13
uniqc submit circuit.originir --backend dummy:local:simulator --shots 1000 --dry-run
uniqc submit circuit.originir --backend originq:WK_C180 --shots 200 --dry-run

# 3. real submit
uid=$(uniqc submit circuit.originir --backend originq:WK_C180 --shots 200)
echo "$uid"                        # uqt_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 4. inspect status / shards
uniqc task show "$uid"
uniqc task shards "$uid"           # platform task id mapping

# 5. wait & fetch
uniqc result "$uid" --wait
```

## Python cheat sheet

```python
from uniqc import (
    Circuit, compile, find_backend,
    dry_run_task, submit_task, submit_batch,
    query_task, wait_for_result, get_result, poll_result,
    get_platform_task_ids,
)

# 1. authoring (any AnyQuantumCircuit input is accepted by submit_task)
c = Circuit(2); c.h(0); c.cnot(0, 1); c.measure(0); c.measure(1)
open("circuit.originir", "w").write(c.originir)
open("circuit.qasm", "w").write(c.qasm)

# 2. dry-run
check = dry_run_task(c, backend="originq:WK_C180", shots=100)
if not check.success:
    raise RuntimeError(check.error or check.details)

# 3. submit (compile first for chip-backed backends)
bi = find_backend("originq:WK_C180")
c_native = compile(c, bi, level=2)
uid = submit_task(c_native, backend="originq:WK_C180", shots=200)
print(uid)                              # uqt_xxxx...

# 4. inspect
info = query_task(uid)                  # cached snapshot
info_now = poll_result(uid)             # non-blocking single-shot status
shards = get_platform_task_ids(uid)     # list[TaskShard]

# 5. wait & fetch
result = wait_for_result(uid, timeout=300)   # -> UnifiedResult (or list for batch)
# alternative (same behavior, alternative name): get_result(uid, timeout=300)
print(result.counts, result.shots, result.platform)
```

## Failure-mode quick reference

| Symptom                                                         | Likely cause / fix                                                                                                  |
| --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `ConfigValidationError: Missing token`                          | `uniqc config set <platform>.token <KEY>` (Quark uses `quark.QUARK_API_KEY`, not `token`).                          |
| `ValueError: backend must be 'provider:chip-name', got 'originq'` | uniqc 0.0.13 enforces full chip ids — use `originq:WK_C180`, `ibm:ibm_fez`, `quark:Baihua`, or `dummy:...`.       |
| `Package 'pyqpanda3' is required for this feature`              | `pip install unified-quantum[originq]`. For Quark: `[quark]` (Py ≥ 3.12). **IBM & chip-backed dummy no longer need an extra in 0.0.13** — qiskit ships in core. |
| `MissingDependencyError`                                        | 0.0.13 wraps every dep error with a doc link + exact `pip install …` line; follow that hint first.                 |
| `CompilationFailedError` on `dummy:originq:<chip>` / IBM        | Likely a topology / basis-gate issue, not a missing extra (qiskit is core in 0.0.13). Check `find_backend(...)` reports the chip & the gate set is supported. |
| `ValueError: Backend 'originq:wk_c180' not found`               | OriginQ chip names are case-sensitive on real submit; use `WK_C180`. Lowercase only works on the `dummy:originq:…` path. |
| `UnsupportedGateError`                                          | Wrong IR for that platform (OriginQ wants OriginIR; Quafu/IBM want OpenQASM 2.0). uniqc auto-converts at submit; check that your file actually parses. |
| `DeprecationWarning` from `query_task` with platform id         | You passed the legacy platform id; use the `uqt_*` returned by `submit_task`/`submit_batch` going forward.          |
| `DeprecationWarning` at Quafu adapter import                    | Quafu archived in 0.0.13. Migrate to OriginQ / Quark / IBM, or `pip install pyquafu` directly and accept `numpy<2`. |
| `wait_for_result` returns `None`                                | Job failed on the platform side — inspect `query_task(uid).status` and `query_task(uid).error`. For batches the failed shard is reported per-element. |
| Empty table from `uniqc submit ... --wait`                      | Pre-0.0.13 the helper only handled raw dict / list; 0.0.13 unwraps `UnifiedResult` and `list[UnifiedResult]`. Upgrade. |

## Names to remember

- CLI: `uniqc config validate`, `uniqc submit`, `uniqc task show / shards`,
  `uniqc result <uid> --wait`, `uniqc backend list / show / chip-display`.
- Python: `dry_run_task`, `submit_task`, `submit_batch`, `query_task`,
  `wait_for_result`, `get_platform_task_ids` (all top-level `uniqc.*`).
- Config helpers: `uniqc.config.get_originq_config()`,
  `get_quafu_config()`, `get_quark_config()`, `get_ibm_config()`,
  `has_platform_credentials("originq")`.
- Caches: `~/.uniqc/config.yaml`, `~/.uniqc/cache/tasks.sqlite`,
  `~/.uniqc/backend/backends.json`, `~/.uniqc/backend/chips/`.

## Response style

- Lead with the runnable command/script that gets the user from
  "I have a circuit" to "I have a `uqt_*`" in three steps.
- Always show the dry-run before the real submit.
- After `wait_for_result`, hand off to the result-analysis skill rather
  than re-explaining `UnifiedResult`.
