---
name: uniqc-doctor-config
description: "Use when the user is debugging the UnifiedQuantum environment, install, or configuration: run `uniqc doctor` (added in uniqc 0.0.13), interpret its 6-section report (env / core deps / optional dep groups / config tokens / task DB / backend cache / platform connectivity), triage `MissingDependencyError` / `ConfigValidationError` / `AuthenticationError` / `BackendNotFoundError`, fix proxy or token problems, refresh the local backend cache, and validate end-to-end before any cloud submit. Covers the `uniqc config validate` / `uniqc config list` / `uniqc config set` / `uniqc backend update` / `uniqc backend list` flow and the platform-extras layout (qiskit core, Quafu archived, originq / quark extras)."
---

# Uniqc Doctor & Config Skill

Use this skill **first** whenever the user reports "submit fails", "import
fails", "no backend found", "auth error", "Quafu warning", "wrong qiskit
version", or "don't know what's installed". `uniqc doctor` (uniqc ≥ 0.0.13)
is the canonical one-shot diagnostic. Everything below reads its output
and converts it into actionable next steps.

## The single command

```bash
uniqc doctor
uniqc doctor --ai-hints           # adds next-step hints suitable for AI agents
```

It prints six Rich tables in order:

1. **Environment** — uniqc version, Python (incl. implementation), OS,
   active config file path (`~/.uniqc/config.yaml` or
   `$UNIQC_PROFILE`-prefixed override).
2. **Core dependencies** — `numpy`, `typer`, `rich`, `scipy`, `pyyaml`
   plus their installed versions. Missing → reinstall uniqc.
3. **Optional dependency groups** — for each group reports installed
   version of every package:

   | Group | Packages | Install |
   | ----- | -------- | ------- |
   | originq | `pyqpanda3` | `pip install unified-quantum[originq]` (Py < 3.14 in v0.0.15) |
   | quafu (archived) | `pyquafu` | `pip install pyquafu` (numpy<2) |
   | quark | `quarkstudio`, `quarkcircuit` | `pip install unified-quantum[quark]` (Linux/macOS, Py 3.12–3.13; **no longer included in `[all]` as of v0.0.15**) |
   | qiskit (now core) | `qiskit`, `qiskit_ibm_runtime` | core deps in 0.0.13 |
   | simulation | `qutip` | `pip install unified-quantum[simulation]` |
   | visualization | `matplotlib` | `pip install unified-quantum[visualization]` |
   | pytorch | `torch` | `pip install unified-quantum[pytorch]` |

4. **Config** — for each platform: token presence (masked, first 6 chars
   shown) + remediation command if missing. Quark uses
   `quark.QUARK_API_KEY`, not `quark.token`.
5. **Task DB** — `~/.uniqc/cache/tasks.sqlite` schema version, row
   count, migration warnings (schema bumps from 2 → 5 happen on
   first use).
6. **Backend cache** — `~/.uniqc/backend/backends.json` size + last update;
   user virtual-machine YAML files live in `~/.uniqc/backend/virtual/`.
   timestamp.
7. **Platform connectivity** — minimum-permission ping for each
   configured platform.

## First decision

| Symptom from `uniqc doctor`                                  | Read first                                              |
| ------------------------------------------------------------ | ------------------------------------------------------- |
| Some optional group prints "not installed"                   | [references/install.md](references/install.md)          |
| Some platform prints "Missing token" / "Missing SDK"         | [references/credentials.md](references/credentials.md)  |
| Backend cache stale / empty / IBM cache won't refresh        | [references/backend-cache.md](references/backend-cache.md) |
| Connectivity check fails behind a proxy / firewall           | [references/proxy.md](references/proxy.md)              |
| `MissingDependencyError` / `BackendNotFoundError` at submit  | [references/error-mapping.md](references/error-mapping.md) |
| Task DB schema version unexpected / migration warnings       | [references/task-db.md](references/task-db.md)          |

## Practical defaults

- **Always lead with `uniqc doctor`** — the user's previous answer to
  any version-of-Python / package question is unreliable; doctor is the
  ground truth.
- After fixing a config problem, re-run `uniqc doctor` (or at minimum
  `uniqc config validate`) before assuming success.
- After installing a platform extra, you usually also need
  `uniqc backend update --platform <p>` (the cache is per-process and
  lazy).
- For a local custom backend, use the offline lifecycle `uniqc backend virtual
  init <name>`, edit `~/.uniqc/backend/virtual/<name>.yaml`, then
  `list`, `show`, and `validate` before
  `uniqc submit ... --backend dummy:virtual:<name>`. A virtual machine may
  model `noise.thermal_relaxation` only when `gate_times_ns` is present.
- For `MissingDependencyError`, **read the error message verbatim** —
  uniqc 0.0.13 enriched every public-facing error with a doc link and
  the exact `pip install ...` command. Do not guess; copy.
- Treat Quafu specially: it is **archived as of 0.0.13**. The `[quafu]`
  extra is **gone**. If a user genuinely needs it, install `pyquafu`
  directly and accept `numpy<2`. New code should target OriginQ /
  Quark / IBM.
- Never log full tokens. Doctor masks them to the first 6 chars; do
  the same in your output.
- IBM proxies belong in `~/.uniqc/config.yaml`, not just env vars
  (uniqc only auto-reads `UNIQC_PROFILE` and `HTTP(S)_PROXY` — not
  `IBM_TOKEN` etc.).

## 0.1.0 deprecation cliff (uniqc ≥ 0.0.15)

uniqc 0.0.15 formalised a **0.0.x → 0.1.0 compatibility cliff**: every
API currently emitting `DeprecationWarning` will be removed (or stop
being maintained) at uniqc 0.1.0. The upstream policy lives at
`docs/source/7_releases/deprecation_policy.md`. Notable items to flag
when you see them in `uniqc doctor` or user logs:

| Deprecated (now)                                              | Replacement                                                      |
| ------------------------------------------------------------- | ---------------------------------------------------------------- |
| `uniqc.simulator.get_backend()`                               | `get_simulator()` / `create_simulator()`                         |
| `IBMAdapter`                                                  | `QiskitAdapter`                                                  |
| entire `uniqc.backend_adapter.task.adapters.quafu_adapter` module | (no replacement) install `pyquafu` directly with `numpy<2` if essential |
| in-place `*_circuit(circuit, ...)` forms of every algorithm builder | fragment form `*_circuit(n_qubits, ...) -> Circuit` + `circuit.add_circuit(fragment)` |
| `grover_diffusion(..., ancilla=...)` kwarg (unused)           | drop the kwarg                                                   |
| Task lookup by platform task id                               | use the uniqc `uqt_*` id returned by `submit_task` / `submit_batch` |

Every deprecation message routes through
`uniqc._deprecation.warn_removed_in_0_1_0` and contains the literal
substring `"uniqc 0.1.0"`. To find every deprecated API exercised in a
log:

```bash
python my_script.py 2>&1 | grep -F "uniqc 0.1.0"
```

If a user is targeting long-lived production code, treat any of the
above as a blocking finding even though it currently still works.

## Cheat sheet — fix-with-one-command

```bash
# Health
uniqc doctor

# Configure tokens
uniqc config set originq.token <ORIGINQ_TOKEN>
uniqc config set quark.QUARK_API_KEY <QUARK_API_KEY>     # different field!
uniqc config set ibm.token <IBM_TOKEN>
uniqc config set ibm.proxy.https http://127.0.0.1:7890   # if needed
uniqc config set ibm.proxy.http  http://127.0.0.1:7890

# Reload + verify
uniqc config validate
uniqc config list

# Refresh backend cache (works for ibm/quafu/quark in 0.0.13)
uniqc backend update --platform originq
uniqc backend update --platform ibm
uniqc backend update --platform quark
uniqc backend list

# Smoke test against the local dummy
uniqc submit /dev/stdin <<<'QINIT 2
H q[0]
CNOT q[0],q[1]
MEASURE q[0],c[0]
MEASURE q[1],c[1]' --backend dummy:local:simulator --shots 100 --wait
```

## Key error → action mapping

| Error                                            | First action                                                                                       |
| ------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| `MissingDependencyError(extra='originq')`        | `pip install unified-quantum[originq]` (Py < 3.14 in v0.0.15); re-run `uniqc doctor`.              |
| `MissingDependencyError(extra='qiskit')` (rare) | qiskit is core in 0.0.13 — `pip install --upgrade unified-quantum`.                                |
| `MissingDependencyError(extra='quafu')`          | Quafu archived; `pip install pyquafu` directly. Hint at deprecation.                               |
| `ModuleNotFoundError: quarkstudio` after `pip install unified-quantum[all]` (v0.0.15) | `[all]` no longer pulls `[quark]`. Install with `pip install unified-quantum[quark]` (Linux/macOS, Py 3.12–3.13). |
| `ConfigValidationError: Missing token`           | `uniqc config set <p>.token <K>` (Quark uses `QUARK_API_KEY`).                                     |
| `BackendNotFoundError: originq:WK_C180`          | `uniqc backend update --platform originq` then `uniqc backend list --platform originq`.            |
| `AuthenticationError`                            | Token typo / expired / wrong instance. Re-set, then `uniqc config validate` and `doctor`.          |
| `NetworkError` / IBM 401                         | Proxy missing — set `ibm.proxy.https/http` in config; re-run.                                       |
| `DeprecationWarning at uniqc.backend_adapter.task.adapters.quafu_adapter` | Quafu archived; migrate or accept the warning. **Will be removed at uniqc 0.1.0** (v0.0.15 cliff). |
| Any `DeprecationWarning` containing `"uniqc 0.1.0"` | Code path will be removed at 0.1.0 (v0.0.15 deprecation cliff); see the "0.1.0 deprecation cliff" section above for the replacement table. |

## Names to remember

- CLI: `uniqc doctor`, `uniqc config validate`, `uniqc config list`,
  `uniqc config get <platform>`, `uniqc config set <key> <value>`,
  `uniqc backend update --platform <p>`, `uniqc backend list`.
- Python: `uniqc.config.get_active_profile()`,
  `uniqc.config.SUPPORTED_PLATFORMS`,
  `uniqc.config.has_platform_credentials(<p>)`,
  `uniqc.config.get_originq_config()` / `get_ibm_config()` /
  `get_quark_config()` / `get_quafu_config()`.
- File locations: `~/.uniqc/config.yaml`,
  `~/.uniqc/cache/tasks.sqlite`,
  `~/.uniqc/backend/backends.json`,
  `~/.uniqc/backend/chips/`,
  `~/.uniqc/calibration_cache/`.

## Response style

- Lead with the **`uniqc doctor` output line** that explains the
  failure, then the one-line fix. Do not prescribe a fix without
  pointing at the doctor section that motivates it.
- For multi-step fixes (install + config + cache refresh), present
  them as a numbered list of single shell commands.
- After any fix, always tell the user to re-run `uniqc doctor` to
  confirm — do not declare victory based on partial output.
