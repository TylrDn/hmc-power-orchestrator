# HMC Power Orchestrator

[![DeepSource](https://app.deepsource.com/gh/TylrDn/hmc-power-orchestrator.svg/?label=code+coverage&show_trend=true&token=mkkonFVMzeR2W82xag2rBFCf)](https://app.deepsource.com/gh/TylrDn/hmc-power-orchestrator/)

CLI tool to inventory IBM Power systems and evaluate autoscaling policies for
Logical Partitions (LPARs). This repository provides a safe dry‑run engine with
structured logging and strict schema validation.

## Quickstart

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e .[dev]
```

Create a configuration file or environment variables. Credentials can also be
loaded from a `.env` file.

```yaml
# ~/.hmc_orchestrator.yaml
host: hmc.example.com
username: svc_hmc
password: ${HMC_PASS}
```

Run the CLI:

```bash
hmc-orchestrator list --json
hmc-orchestrator policy validate examples/example-policy.yaml
hmc-orchestrator policy dry-run examples/example-policy.yaml --report report.json
```

## Configuration precedence

1. CLI flags
2. Environment variables / `.env`
3. YAML file (`~/.hmc_orchestrator.yaml`)

Supported environment variables mirror the YAML keys, e.g. `HMC_HOST`,
`HMC_USERNAME`, `HMC_PASSWORD`, `HMC_VERIFY`.

## Testing

```bash
pytest -q
```

## Code quality

DeepSource currently reports around **27%** code coverage, indicating a low level
of confidence in the test suite. See the
[DeepSource dashboard](https://app.deepsource.com/gh/TylrDn/hmc-power-orchestrator/)
for more details and coverage trends.

## Operator runbook

1. Ensure PCM/LTM is enabled on all frames hosting IBM i LPARs.
2. Run `hmc-orchestrator list --json` regularly and archive the output.
3. Validate and dry-run policies. Review the dry-run report before any manual
   resize.
4. Never disable TLS verification in production; provide a CA bundle if needed.

## License

Apache-2.0
