# hmc-power-orchestrator

`hmc-power-orchestrator` is a small Python CLI for discovering IBM Power
managed systems and LPARs, fetching basic performance metrics and performing
simple dynamic LPAR (DLPAR) changes.  It talks directly to the HMC REST APIs
using `requests` and is intended for demos and automation scripts.

## Prerequisites

* Python 3.10+
* Network access to an IBM Hardware Management Console (HMC)
* An HMC user with sufficient privileges to view systems and perform DLPAR
  operations
* Optional: firewall rules or proxies allowing HTTPS access

## Quickstart

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # edit with your HMC credentials

# List systems and LPARs
python -m hmc_orchestrator.cli list-systems
python -m hmc_orchestrator.cli list-lpars --ms "$HMC_MANAGED_SYSTEM"
```

## Example Policy

A sample autoscaling policy is provided in `examples/policy.yaml`:

```yaml
min_vcpu: 1
max_vcpu: 32
scale_up_cpu_ready_pct: 20
scale_down_cpu_idle_pct: 70
min_mem_mb: 4096
max_mem_mb: 262144
scale_up_mem_free_mb: 1024
scale_down_mem_free_mb: 8192
step_mem_mb: 1024
exclude_lpars: ["VIOS1", "VIOS2"]
```

Run a dry‑run autoscale with:

```bash
python -m hmc_orchestrator.cli auto-adjust --policy examples/policy.yaml --dry-run -v
```

## Safety Notes

* TLS certificate verification is **enabled** by default. Use `--no-verify`
  with caution.
* The CLI is safe-by-default: destructive actions require explicit flags such
  as `--yes` (not implemented in this minimal example).
* Credentials are loaded from `.env`; avoid committing real secrets.

## Troubleshooting

* `AuthError`: verify your HMC user and password and that the account has the
  correct roles.
* `PCM metrics not available`: the target LPAR or HMC may not have Performance
  and Capacity Monitoring enabled.

## License

This project is licensed under the Apache 2.0 license.  See `LICENSE` for
details.  This software is provided as-is without warranty.
