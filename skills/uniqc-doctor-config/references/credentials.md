# Credentials & tokens

uniqc reads tokens from `~/.uniqc/config.yaml` (or the
`UNIQC_PROFILE`-prefixed override). It does **not** auto-import
`ORIGINQ_API_KEY`, `QUARK_API_KEY`, `IBM_TOKEN`, `TIANYAN_LOGIN_KEY`,
or `LOGICALQUBIT_API_KEY` from the environment. Since 0.1.0 the file
carries a top-level `config_version` (auto-migrated on first load);
Quafu keys are gone with the platform.

## What goes in config.yaml

```yaml
config_version: 1

originq:
  token: <ORIGINQ_TOKEN>

quark:
  QUARK_API_KEY: <QUARK_API_KEY>         # NOT `token`
  # other quark.* fields as supplied by the platform

tianyan:
  login_key: <TIANYAN_LOGIN_KEY>

logicalqubit:
  api_key: <LOGICALQUBIT_API_KEY>
  # url: https://cloud.logicalqubit.com   # optional override

ibm:
  token: <IBM_TOKEN>
  proxy:
    https: http://127.0.0.1:7890         # optional
    http:  http://127.0.0.1:7890
  channel: ibm_quantum                   # or ibm_cloud, depending on account
  instance: ibm-q/open/main              # depends on entitlement
```

## Setting tokens via CLI

```bash
uniqc config set originq.token <T>
uniqc config set quark.QUARK_API_KEY <K>
uniqc config set tianyan.login_key <K>
uniqc config set logicalqubit.api_key <K>
uniqc config set ibm.token <T>
uniqc config set ibm.proxy.https http://127.0.0.1:7890
uniqc config validate
```

## Programmatic read

```python
from uniqc import config as cfg

print(cfg.get_active_profile())                          # 'default' or override
for plat in cfg.SUPPORTED_PLATFORMS:
    print(plat, cfg.has_platform_credentials(plat))

# Explicit getters (return dicts):
print(cfg.get_originq_config())
print(cfg.get_quark_config())
print(cfg.get_ibm_config())
```

## Doctor's "Config" section line by line

`uniqc doctor` reports for each platform:

- **Configured (token: abcdef****)** — ready. Will still ping
  connectivity in section 7.
- **Missing token** — run the corresponding `uniqc config set ...`.
- **Missing SDK** — install the matching extra (see `install.md`).
- **Auth failed** — token present but the platform rejected the ping.
  Re-issue the token.

## Profile switching

```bash
UNIQC_PROFILE=staging uniqc doctor
UNIQC_PROFILE=staging uniqc config set originq.token <T>
```

A profile is a sub-dict of `config.yaml` keyed by name; see
`uniqc config list-profiles`.

## Common mistakes

- **Quark vs other platforms** — Quark's token field is
  `quark.QUARK_API_KEY`, not `quark.token`. `uniqc config validate`
  will not surface a wrongly named field beyond a generic "missing
  token".
- **`token: "<TOKEN>"` literally written into the file** — copy/paste
  artefact; verify with `uniqc config get <platform>`.
- **`quafu.*` keys left in an old config** — harmless leftovers from
  pre-0.1.0; the platform (and its validation) is gone. Remove them or
  ignore.
- **IBM `instance:` mismatch** — the IBM Quantum platform tightened
  account scoping; if connectivity passes but submit fails with 401,
  the `ibm.instance` field is wrong.
