# hmc-power-orchestrator

Production ready CLI to inspect and resize IBM Power HMC logical partitions.

Features include:

- resilient HTTP client with retries and correlation IDs
- policy planning and guarded apply (`--apply --confirm`)
- structured JSON logging and Prometheus metrics
- append only audit log

## Quickstart

```bash
pip install hmc-power-orchestrator
# or with pipx
pipx install hmc-power-orchestrator
```

Create `~/.hmc_orchestrator.yaml` with your credentials and then:

```bash
hmc-orchestrator inventory
hmc-orchestrator plan examples/example-policy.json
hmc-orchestrator apply examples/example-policy.json --apply --confirm
```

Each run uses a unique run id (override with `--run-id`). Previews and apply
artifacts are written under `--output` (default `./run`).

## Configuration

Environment variables or `~/.hmc_orchestrator.yaml` are supported:

```yaml
host: hmc.example.com
username: myuser
password: secret
```

## Policy Schema

Policies are versioned. Example v1 policy:

```json
{
  "policy_version": 1,
  "targets": [
    {"lpar": "L1", "cpu": 2, "mem": 2048}
  ]
}
```

Generate the JSON schema via:

```bash
python -c "import json, hmc_power_orchestrator.policy as p; print(p.Policy().to_json_schema())"
```

## Safety Rails

`apply` requires both `--apply` and `--confirm`. Without `--apply` a dry run is
performed. Outputs are logged in structured JSON and optional audit log via
`--audit-log file`.

## License

Apache-2.0
