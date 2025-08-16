# hmc-power-orchestrator

Command line tool for inspecting IBM Power Hardware Management Console (HMC)
objects and experimenting with autoscaling policies.  Current capabilities
include:

- list managed systems and logical partitions (LPARs)
- preview CPU/memory changes via policy *dry-run*
- validate autoscaling policy files

> **Note**: applying policy changes to the HMC is **not implemented** yet.  All
> actions are read‑only or dry‑run previews.

## Quickstart

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
cp .env.example .env  # edit with your credentials
hmc-orchestrator --help
```

Example `.env` values:

```bash
export HMC_HOST=hmc.example.com
export HMC_USER=myuser
# omit HMC_PASS to be prompted securely
```

Listing LPARs:

```bash
hmc-orchestrator list
```

Validating a policy:

```bash
hmc-orchestrator policy validate examples/sample-policy.yaml
```

Dry-run a policy:

```bash
hmc-orchestrator policy dry-run examples/sample-policy.yaml
```

## HMC prerequisites

- User with sufficient privileges to query systems and LPAR metrics
- Performance and Capacity Monitoring (PCM) must be enabled
- Tested against HMC API version 2.0 on firmware 950+

## Security

TLS certificate verification is enabled by default.  Disabling it via
`--no-verify` is strongly discouraged as it exposes credentials on the wire.

## Example policy file

See [examples/sample-policy.yaml](examples/sample-policy.yaml).  A dry run
produces output similar to:

```
Would resize LPAR1 -> cpu=4, mem=8192
Would resize LPAR2 -> cpu=2, mem=4096
```

## License

Apache-2.0
