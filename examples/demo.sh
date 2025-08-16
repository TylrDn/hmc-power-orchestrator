#!/usr/bin/env bash
# Simple demo script

python -m hmc_orchestrator.cli list-systems
python -m hmc_orchestrator.cli list-lpars --ms "$HMC_MANAGED_SYSTEM"
