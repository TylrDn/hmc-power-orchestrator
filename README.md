# hmc-power-orchestrator

Secure, scriptable CLI for dynamically managing CPU and memory of IBM Power
LPARs via the Hardware Management Console (HMC) REST API.

## Features
- Discover systems and LPARs
- Resize CPU and memory allocations
- Dry-run simulation mode
- Secure credential handling (env or `~/.hmc_orchestrator.yaml`)
- Rich output and logging

## Installation
```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
# or: pip install .
```

## Usage
```bash
hmc-power list
hmc-power resize LPAR1 --cpu 4 --mem 8192 --dry-run
```

### Authentication
- Environment variables: `HMC_URL`, `HMC_USERNAME`, `HMC_PASSWORD`
- Optional YAML config: `~/.hmc_orchestrator.yaml`
- Custom CA bundle via `HMC_CA_BUNDLE`

## Example Workflow
1. View current LPAR inventory  
   `hmc-power list`
2. Resize an LPAR with confirmation  
   `hmc-power resize LPAR1 --cpu 8 --mem 16384`
3. Perform dry-run before applying  
   `hmc-power resize LPAR1 --cpu 8 --mem 16384 --dry-run`

## License
Apache-2.0
