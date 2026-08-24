---
name: uniqc-doctor-config
description: "Use when the user is debugging the UnifiedQuantum environment, install, or configuration: run `uniqc doctor` (added in uniqc 0.0.13), interpret its multi-section report (env / core deps / optional dep groups / config tokens / task DB / backend cache / platform connectivity), triage `MissingDependencyError` / `ConfigValidationError` / `AuthenticationError` / `BackendNotFoundError`, fix proxy or token problems, refresh the local backend cache, and validate end-to-end before any cloud submit. Covers the `uniqc config validate` / `uniqc config list` / `uniqc config set` / `uniqc backend update` / `uniqc backend list` flow, the platform-extras layout (qiskit core, Quafu removed in 0.1.0, originq / quark / tianyan / logicalqubit extras), the config schema versioning, and `uniqc sync` credential sync (Infisical / confsync)."
---

# Uniqc Doctor & Config Skill

Use this skill **first** whenever the user reports "submit fails", "import
fails", "no backend found", "auth error", "removed-API error after the
0.1.0 upgrade", "wrong qiskit
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
   | originq | `pyqpanda3` | `pip install unified-quantum[originq]` (Py < 3.14) |
   | quark | `quarkstudio`, `quarkcircuit` | `pip install unified-quantum[quark]` (Py ≥ 3.12 only; back in `[all]` since v0.1.0) |
   | tianyan | `cqlib` | `pip install unified-quantum[tianyan]` |
   | logicalqubit | `lqcloud` | `pip install unified-quantum[logicalqubit]` |
   | qiskit (core) | `qiskit`, `qiskit_ibm_runtime` | core deps since 0.0.13 |
   | simulation | `qutip` | `pip install unified-quantum[simulation]` |
   | visualization | `matplotlib` | `pip install unified-quantum[visualization]` |
   | pytorch | `torch` | `pip install unified-quantum[pytorch]` |

   Quafu has no row: the platform was **removed in 0.1.0**. BAQIS ScQ
   chips are served by Quark (`[quark]` extra, `quark:<chip>` backends).

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
- Quafu is **removed as of 0.1.0** — module, `Platform.QUAFU`,
  `quafu.*` config keys, everything. Users on `quafu:ScQ-*` backends
  migrate to Quark: `pip install unified-quantum[quark]` and
  `quark:<chip>` backend ids.
- The config file now carries a top-level `config_version` (schema
  versioning added in 0.1.0): `load_config` auto-migrates older
  unversioned files and persists the result; a file written by a newer
  uniqc is rejected with an upgrade hint. Don't hand-delete the key.
- Credential sync (`uniqc sync`): `setup` / `status` / `push` / `pull`
  talk to an Infisical secrets project via the local `infisical` CLI;
  `upload` pushes the config to a self-hosted confsync server via the
  optional `confsync-client` package. Values are never echoed.
- Never log full tokens. Doctor masks them to the first 6 chars; do
  the same in your output.
- IBM proxies belong in `~/.uniqc/config.yaml`, not just env vars
  (uniqc only auto-reads `UNIQC_PROFILE` and `HTTP(S)_PROXY` — not
  `IBM_TOKEN` etc.).

## 0.1.0 removals (shipped in uniqc 0.1.0)

The deprecation cliff announced in 0.0.15 has been executed: every API
that emitted `DeprecationWarning` throughout `0.0.x` is **gone** in
0.1.0. The upstream migration guide lives at
`docs/source/7_releases/migration_0.1.0.md`. When a user upgrades from
0.0.x and hits one of these, map it directly:

| Removed in 0.1.0                                              | Replacement                                                      |
| ------------------------------------------------------------- | ---------------------------------------------------------------- |
| `uniqc.simulator.get_backend()`                               | `uniqc.simulator.get_simulator()` / `create_simulator()` (same args; the top-level cloud factory `uniqc.get_backend()` is unaffected) |
| `IBMAdapter`                                                  | `QiskitAdapter` (same `proxy=` constructor; the `ibm_adapter` module itself stays) |
| entire Quafu platform (`quafu_adapter`, `Platform.QUAFU`, `quafu.*` config keys, `pyquafu` refs) | migrate to Quark: `[quark]` extra + `quark:<chip>` backends |
| in-place `*_circuit(circuit, ...)` forms of the 12 algorithm builders | fragment form `*_circuit(n_qubits, ...) -> Circuit` + `circuit.add_circuit(fragment)` |
| `grover_diffusion(..., ancilla=...)` kwarg (was a no-op)      | drop the kwarg                                                   |
| Task lookup by platform task id (implicit `uqt_*` resolution) | use the uniqc `uqt_*` id returned by `submit_task` / `submit_batch` |

On 0.0.x these all raised `DeprecationWarning` containing the literal
substring `"uniqc 0.1.0"` — grep old logs with
`grep -F "uniqc 0.1.0"` to find code that will now break. Also note the
C++ simulator kernel moved to the standalone `uniqc-cppsimulator` PyPI
package (import name `uniqc_cpp` unchanged), so `unified-quantum`
installs as a pure-Python wheel — no CMake/C++ toolchain needed.

## Cheat sheet — fix-with-one-command

```bash
# Health
uniqc doctor

# Configure tokens
uniqc config set originq.token <ORIGINQ_TOKEN>
uniqc config set quark.QUARK_API_KEY <QUARK_API_KEY>     # different field!
uniqc config set ibm.token <IBM_TOKEN>
uniqc config set tianyan.login_key <TIANYAN_LOGIN_KEY>
uniqc config set logicalqubit.api_key <LOGICALQUBIT_API_KEY>
uniqc config set ibm.proxy.https http://127.0.0.1:7890   # if needed
uniqc config set ibm.proxy.http  http://127.0.0.1:7890

# Reload + verify
uniqc config validate
uniqc config list

# Refresh backend cache
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
| `ModuleNotFoundError: quarkstudio` after `pip install unified-quantum[all]` (≤ v0.0.17) | Since v0.1.0 `[all]` includes `[quark]` again — upgrade, or `pip install unified-quantum[quark]` (Py ≥ 3.12). |
| `ConfigValidationError: Missing token`           | `uniqc config set <p>.token <K>` (Quark uses `QUARK_API_KEY`; TianYan uses `tianyan.login_key`; LogicalQubit uses `logicalqubit.api_key`). |
| `BackendNotFoundError: originq:WK_C180`          | `uniqc backend update --platform originq` then `uniqc backend list --platform originq`.            |
| `AuthenticationError`                            | Token typo / expired / wrong instance. Re-set, then `uniqc config validate` and `doctor`.          |
| `NetworkError` / IBM 401                         | Proxy missing — set `ibm.proxy.https/http` in config; re-run.                                       |
| `ModuleNotFoundError: uniqc.backend_adapter.task.adapters.quafu_adapter` | Quafu was removed in 0.1.0. Migrate to `quark:<chip>` (`pip install unified-quantum[quark]`). |
| Removed-API errors after upgrading to 0.1.0 | See the "0.1.0 removals" section above — `simulator.get_backend()` / `IBMAdapter` / Quafu / in-place algorithm builders / platform-id lookup are gone. |

## Names to remember

- CLI: `uniqc doctor`, `uniqc config validate`, `uniqc config list`,
  `uniqc config get <platform>`, `uniqc config set <key> <value>`,
  `uniqc backend update --platform <p>`, `uniqc backend list`,
  `uniqc sync setup / status / push / pull / upload`.
- Python: `uniqc.config.get_active_profile()`,
  `uniqc.config.SUPPORTED_PLATFORMS` (`originq` / `quark` / `ibm` /
  `tianyan` / `logicalqubit`),
  `uniqc.config.has_platform_credentials(<p>)`,
  `uniqc.config.get_originq_config()` / `get_ibm_config()` /
  `get_quark_config()` / `get_platform_config("tianyan")` /
  `get_platform_config("logicalqubit")`.
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
