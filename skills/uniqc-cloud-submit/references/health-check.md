# Environment & API key health check

uniqc 0.0.13 introduces the `uniqc doctor` subcommand — a one-shot
environment diagnostic that bundles every check on this page. **Run it
first.** Then drop into `uniqc config validate` / `uniqc config list` /
`uniqc backend list` for the deeper details.

## Step 0 — `uniqc doctor` (uniqc ≥ 0.0.13)

```bash
uniqc doctor                 # full env + deps + config + DB + cache + connectivity
uniqc doctor --ai-hints      # plus next-step hints for AI agents
```

Sections it prints (each as a Rich table):

1. **Environment** — uniqc version, Python version, OS, `~/.uniqc/config.yaml` path.
2. **Core dependencies** — numpy / typer / rich / scipy / pyyaml.
3. **Optional dependency groups** — installed version per group:
   `originq` (pyqpanda3), `quark`
   (quarkstudio + quarkcircuit), `qiskit`
   (qiskit + qiskit_ibm_runtime), `simulation` (qutip),
   `visualization` (matplotlib), `pytorch` (torch).
4. **Config** — for each platform: token presence (masked, first 6 chars)
   + remediation command if missing.
5. **Task DB** — schema version + row count of `~/.uniqc/cache/tasks.sqlite`,
   migration warnings if any.
6. **Backend cache** — `~/.uniqc/backend/backends.json` presence + last update.
7. **Platform connectivity** — minimum-permission ping for every configured
   platform.

If the user reports "submit keeps failing" or "something looks wrong",
**do `uniqc doctor` first** and base the next step on its output.

## Step 1 — show the user the active config

```bash
uniqc config list                  # rich table of platforms + status
uniqc config validate              # exits non-zero if anything is wrong
uniqc config get originq           # prints the originq section
```

`uniqc config list` reports one of:

- `Configured` — token present, SDK importable.
- `Missing token` — `uniqc config set <platform>.token <VALUE>` (Quark uses
  `quark.QUARK_API_KEY` not `token`).
- `Missing SDK` — install the matching extra (see the table below).

## Step 2 — install the platform extra if needed (uniqc 0.0.13 layout)

| Platform | Install                                | Min Python | What it pulls            |
| -------- | -------------------------------------- | ---------- | ------------------------ |
| OriginQ  | `pip install unified-quantum[originq]` | 3.10 (< 3.14) | `pyqpanda3`           |
| Quark    | `pip install unified-quantum[quark]`   | **3.12**   | `quarkstudio` + `quarkcircuit` |
| IBM      | `pip install unified-quantum`          | 3.10       | qiskit / qiskit-aer / qiskit-ibm-runtime (now **core deps** in 0.0.13 — `[qiskit]` extra removed) |
| TianYan  | `pip install unified-quantum[tianyan]` | 3.10       | `cqlib`                  |
| LogicalQubit | `pip install unified-quantum[logicalqubit]` | 3.10  | `lqcloud`               |
| Chip-backed dummy (`dummy:originq:<chip>`, `dummy:quark:<chip>`) | `pip install unified-quantum` | 3.10 | qiskit transpiler (core dep) |

`unified-quantum[all]` is a convenience meta-extra; since 0.1.0 it
includes `[quark]` again (the extra only requires Python ≥ 3.12 and is
silently skipped on 3.10/3.11). Quafu was **removed entirely in 0.1.0** —
BAQIS ScQ chips are served by `quark:<chip>`.

> 💡 0.0.13 also enriches every `MissingDependencyError` with a doc link
> and the exact `pip install ...` line — when in doubt, follow the error
> message verbatim before hand-editing.

## Step 3 — set the missing token

```bash
uniqc config set originq.token   $ORIGINQ_TOKEN
uniqc config set quark.QUARK_API_KEY $QUARK_API_KEY    # different key!
uniqc config set ibm.token       $IBM_TOKEN
uniqc config set tianyan.login_key  $TIANYAN_LOGIN_KEY
uniqc config set logicalqubit.api_key $LOGICALQUBIT_API_KEY
```

Then re-run `uniqc config validate`.

> ⚠️ Do **not** rely on environment variables. uniqc itself only reads
> `UNIQC_PROFILE` and `HTTP(S)_PROXY`. It does not auto-import
> `ORIGINQ_API_KEY` / `QUARK_API_KEY` / `IBM_TOKEN` / `TIANYAN_LOGIN_KEY` /
> `LOGICALQUBIT_API_KEY`.

## Step 4 — refresh the backend cache

```bash
uniqc backend update --platform originq
uniqc backend update --platform ibm
uniqc backend list                 # combined view across all configured platforms
```

If `backend list` shows a backend with `status=available` for the platform you
care about, you are clear to dry-run and submit.

## Programmatic equivalent

```python
from uniqc import config as cfg

print(cfg.get_active_profile())
for plat in cfg.SUPPORTED_PLATFORMS:
    print(plat, "configured?", cfg.has_platform_credentials(plat))

# Inspect a single platform
print(cfg.get_originq_config())
```

## Common follow-up issues

- `qiskit_runtime_service` warns "Loading account with the given token. A
  saved account will not be used" — harmless, you are using the uniqc-managed
  token rather than a saved IBM account file.
- IBM behind a proxy:
  ```bash
  uniqc config set ibm.proxy.https http://127.0.0.1:7890
  uniqc config set ibm.proxy.http  http://127.0.0.1:7890
  ```
- After fixing config you usually need `uniqc backend update --platform <p>`
  again — `uniqc backend list` returns cached entries until you do.
