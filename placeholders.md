# Production Integration Placeholders

Replace the values below with your real production settings. Do **not** commit
actual credentials to source control.

## Environment Variables
```
export HMC_URL=https://hmc.example.com
export HMC_USERNAME=<your-username>
export HMC_PASSWORD=<your-password>
export HMC_VERIFY_SSL=true  # set to false only for testing
export HMC_CA_BUNDLE=/path/to/ca.pem  # optional
```

## YAML Configuration (`~/.hmc_orchestrator.yaml`)
```yaml
base_url: https://hmc.example.com
username: your-username
password: your-password
verify_ssl: true
# ca_bundle: /path/to/ca.pem
```

## Notes
- Rotate credentials regularly and store them in a secure secret manager.
- Limit filesystem permissions on the YAML file: `chmod 600`.
- Review network policies before disabling TLS verification.
